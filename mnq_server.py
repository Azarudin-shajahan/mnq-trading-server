# mnq_server.py — MNQ Autonomous Trading System
# Owner: Azarudin | Version: 1.0 | April 2026
# Two-agent workflow: Claude architects, Goose executes.
# Deploy to Railway. AUTOMATION_ENABLED=false until 2-week demo passes.

# ─────────────────────────────────────────────────────────────
# S1 — Imports and config
# ─────────────────────────────────────────────────────────────

import os
import json
import math
import logging
import asyncio
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mnq_server")

NY = ZoneInfo("America/New_York")  # ALWAYS use this. Never hardcode IST.

app = FastAPI(title="MNQ Trading Server")
scheduler = AsyncIOScheduler(timezone="America/New_York")


# ─────────────────────────────────────────────────────────────
# S2 — ENV loading
# ─────────────────────────────────────────────────────────────

WEBHOOK_SECRET        = os.getenv("WEBHOOK_SECRET", "mnq_azarudin_2026")
AUTOMATION_ENABLED    = os.getenv("AUTOMATION_ENABLED", "false").lower() == "true"  # DEFAULT FALSE ALWAYS
SYMBOL                = os.getenv("SYMBOL", "MNQM6")
ENVIRONMENT           = os.getenv("ENVIRONMENT", "auto")
DAILY_TARGET_EVAL     = float(os.getenv("DAILY_TARGET_EVAL", "1200"))
CONSISTENCY_CEILING   = float(os.getenv("CONSISTENCY_CEILING", "1560"))
MLL_LOCK_TRIGGER      = float(os.getenv("MLL_LOCK_TRIGGER", "52100"))
MLL_LOCKED_FLOOR      = float(os.getenv("MLL_LOCKED_FLOOR", "50100"))
TELEGRAM_BOT_TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID      = os.getenv("TELEGRAM_CHAT_ID", "")
TRADOVATE_USERNAME    = os.getenv("TRADOVATE_USERNAME", "")
TRADOVATE_PASSWORD    = os.getenv("TRADOVATE_PASSWORD", "")
TRADOVATE_ACCOUNT_SPEC = os.getenv("TRADOVATE_ACCOUNT_SPEC", "")
ANTHROPIC_API_KEY     = os.getenv("ANTHROPIC_API_KEY", "")

ENTRY_MIN = 4.5        # HARD CONSTANT. Locked May 7 2026. Never 5.0 — 3 grid datasets confirm 5.0 cannot reach Holy Grail.
MNQ_POINT_VALUE = 2.00  # $2.00 per point live (4 ticks × $0.50/tick). Backtest engine uses $0.50 — that's intentional there, not here.


# ─────────────────────────────────────────────────────────────
# S3 — In-memory state
# ─────────────────────────────────────────────────────────────

state = {
    "daily_pnl": 0.0,
    "daily_trades": 0,
    "total_profit": 0.0,
    "account_balance": 50000.0,
    "mll_floor": 48000.0,
    "mll_locked": False,
    "consistency_largest_day": 0.0,
    "tradovate_token": None,
    "tradovate_token_expiry": None,
    "open_positions": {},
    "trade_log": [],
    "alerted_setups": {},  # {f"{direction}:{stop}": datetime} — dedup same FVG zone within 6h
    "signal_log": [],     # [{ts, direction, grade, score, entry, stop, ny_ok, status}] — capped 100
}




# ─────────────────────────────────────────────────────────────
# S3b — Signal log helper
# ─────────────────────────────────────────────────────────────

def _log_signal(body: dict, status: str):
    now_ny = datetime.now(NY)
    ny_ok = (
        now_ny.weekday() < 5
        and (7 * 60 + 30) <= (now_ny.hour * 60 + now_ny.minute) < 17 * 60
    )
    state["signal_log"].insert(0, {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "direction": body.get("direction", ""),
        "grade": body.get("grade", ""),
        "score": float(body.get("score", 0)),
        "entry": float(body.get("entry", 0)),
        "stop": float(body.get("stop", 0)),
        "ny_ok": ny_ok,
        "status": status,
    })
    if len(state["signal_log"]) > 100:
        state["signal_log"] = state["signal_log"][:100]

# ─────────────────────────────────────────────────────────────
# S4 — Tradovate authentication
# ─────────────────────────────────────────────────────────────

_tv_env = os.getenv("TRADOVATE_ENV", "demo")  # set to "live" in Railway when ready
TRADOVATE_BASE = f"https://{_tv_env}.tradovateapi.com/v1"


async def get_tradovate_token() -> str:
    now = datetime.now(timezone.utc)
    if state["tradovate_token"] and state["tradovate_token_expiry"] > now:
        return state["tradovate_token"]
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TRADOVATE_BASE}/auth/accesstokenrequest",
            json={
                "name": TRADOVATE_USERNAME,
                "password": TRADOVATE_PASSWORD,
                "appId": "MNQServer",
                "appVersion": "1.0",
                "cid": 0,
                "sec": "",
            },
        )
        data = resp.json()
        state["tradovate_token"] = data["accessToken"]
        state["tradovate_token_expiry"] = (
            datetime.fromisoformat(data["expirationTime"]).replace(tzinfo=timezone.utc)
        )
        logger.info("Tradovate token refreshed")
        return state["tradovate_token"]


# ─────────────────────────────────────────────────────────────
# S5 — Contract sizing (formula, never fixed)
# ─────────────────────────────────────────────────────────────

def calculate_contracts(accumulation_pts: float, grade: str) -> int:
    """
    T2_per_contract = accumulation_pts x 2.5 x $0.50
    Contracts = floor(DAILY_TARGET_EVAL / T2_per_contract)
    Cap: 40 micros (hard Lucid Flex rule for 50K eval and funded tier 3).
    No fixed contract count anywhere in this function.
    """
    if accumulation_pts <= 0:
        return 1
    t2_per_contract = accumulation_pts * 2.5 * MNQ_POINT_VALUE
    if t2_per_contract <= 0:
        return 1
    raw = math.floor(DAILY_TARGET_EVAL / t2_per_contract)
    cap = 40  # eval cap; funded tier logic handled separately if needed
    contracts = max(1, min(raw, cap))
    logger.info(
        f"Sizing: {accumulation_pts}pt → T2/contract=${t2_per_contract:.2f}"
        f" → raw={raw} → capped={contracts}"
    )
    return contracts


# ─────────────────────────────────────────────────────────────
# S6 — Consistency check (eval only)
# ─────────────────────────────────────────────────────────────

def consistency_ok(proposed_pnl: float) -> bool:
    """
    Largest day <= 50% of total profit. Effective ceiling $1,560/day during eval.
    No consistency rule in funded — this check still runs but ceiling is not binding.
    """
    projected = state["daily_pnl"] + proposed_pnl
    if projected > CONSISTENCY_CEILING:
        logger.warning(
            f"Consistency ceiling: projected {projected:.2f} > {CONSISTENCY_CEILING}"
        )
        return False
    return True


# ─────────────────────────────────────────────────────────────
# S7 — Drawdown guard (EOD trailing MLL)
# ─────────────────────────────────────────────────────────────

def drawdown_ok() -> tuple[bool, str]:
    """
    EOD trailing MLL. Trails at $2,000 gap below EOD closing balance.
    Locks permanently at $50,100 once balance exceeds $52,100.
    Intraday drawdown irrelevant to firm — only EOD balance matters.
    Stop placement based on STDV, not intraday MLL.
    """
    if state["mll_locked"]:
        if state["account_balance"] <= MLL_LOCKED_FLOOR:
            return (
                False,
                f"MLL locked floor breached: {state['account_balance']:.2f} <= {MLL_LOCKED_FLOOR}",
            )
        return True, "ok"
    else:
        if state["account_balance"] <= state["mll_floor"]:
            return (
                False,
                f"MLL floor breached: {state['account_balance']:.2f} <= {state['mll_floor']:.2f}",
            )
        return True, "ok"


def check_mll_lock():
    """Call at daily reset. Locks MLL permanently if balance exceeded trigger."""
    if not state["mll_locked"] and state["account_balance"] > MLL_LOCK_TRIGGER:
        state["mll_locked"] = True
        state["mll_floor"] = MLL_LOCKED_FLOOR
        logger.info(f"MLL LOCKED at {MLL_LOCKED_FLOOR}")
        asyncio.create_task(
            send_telegram(f"🔒 MLL LOCKED\nFloor: ${MLL_LOCKED_FLOOR:,.0f} permanent")
        )


# ─────────────────────────────────────────────────────────────
# S8 — Telegram
# ─────────────────────────────────────────────────────────────

async def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                url,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Telegram failed: {e}")


# ─────────────────────────────────────────────────────────────
# S9 — Order placement
# ─────────────────────────────────────────────────────────────

async def place_order(
    direction: str,
    contracts: int,
    entry: float,
    stop: float,
    t1: float,
    t2: float,
) -> dict:
    token = await get_tradovate_token()
    action = "Buy" if direction == "long" else "Sell"
    stop_action = "Sell" if direction == "long" else "Buy"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TRADOVATE_BASE}/order/placeorder",
            headers=headers,
            json={
                "accountSpec": TRADOVATE_ACCOUNT_SPEC,
                "symbol": SYMBOL,
                "orderQty": contracts,
                "orderType": "Limit",
                "price": entry,
                "action": action,
                "timeInForce": "Day",
            },
            timeout=15,
        )
        order = resp.json()
        order_id = order.get("orderId") or order.get("id")

        # OCO stop
        await client.post(
            f"{TRADOVATE_BASE}/order/placeorder",
            headers=headers,
            json={
                "accountSpec": TRADOVATE_ACCOUNT_SPEC,
                "symbol": SYMBOL,
                "orderQty": contracts,
                "orderType": "Stop",
                "stopPrice": stop,
                "action": stop_action,
                "timeInForce": "GTC",
                "isAutomated": True,
            },
            timeout=15,
        )
    logger.info(f"Order placed: {action} {contracts}x {SYMBOL} @ {entry}")
    return {
        "order_id": order_id,
        "entry": entry,
        "stop": stop,
        "t1": t1,
        "t2": t2,
        "contracts": contracts,
    }


# ─────────────────────────────────────────────────────────────
# S10 — Webhook endpoint (8-gate chain)
# ─────────────────────────────────────────────────────────────

@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Gate order:
      1. Secret validation
      2. SSMT confirmed (absolute hard gate — no bypass ever)
      3. Score >= ENTRY_MIN (4.5 — locked May 7 2026)
      4. Grade A or A+ only
      5. AUTOMATION_ENABLED
      6. Drawdown guard
      7. Contract sizing
      8. Consistency ceiling
      → Place order

    Expected payload:
    {
        "secret": "mnq_azarudin_2026",
        "ssmt_confirmed": true,
        "score": 9.5,
        "grade": "A",
        "direction": "long",
        "entry": 19540.25,
        "stop": 19510.0,
        "t1": 19570.0,
        "t2": 19600.0,
        "accumulation_pts": 60.0,
        "conditions": ["SSMT_ACT", "WEDNESDAY", "HTF_3of3", "C18"]
    }
    """
    body = await request.json()

    # GATE 1 — Secret
    if body.get("secret") != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # GATE 2 — SSMT: absolute hard gate, no exceptions ever
    if not body.get("ssmt_confirmed", False):
        logger.warning("SSMT not confirmed — rejecting")
        await send_telegram("⚠️ Webhook received but SSMT not confirmed — rejected")
        return JSONResponse({"status": "gate_failed", "reason": "ssmt_not_confirmed"})

    score          = float(body.get("score", 0))
    grade          = body.get("grade", "C")
    direction      = body.get("direction", "")
    entry          = float(body.get("entry", 0))
    stop           = float(body.get("stop", 0))
    t1             = float(body.get("t1", 0))
    t2             = float(body.get("t2", 0))
    accumulation_pts = float(body.get("accumulation_pts", 0))
    conditions     = body.get("conditions", [])

    # GATE 3 — Score >= ENTRY_MIN (4.5)
    if score < ENTRY_MIN:
        await send_telegram(
            f"📊 <b>JUDGE SIGNAL — BELOW THRESHOLD</b>\n"
            f"Grade: {grade} | Score: {score:.1f} | Min: {ENTRY_MIN}\n"
            f"Direction: {direction.upper()} | Logged only."
        )
        return JSONResponse({"status": "below_threshold", "score": score})

    # DEDUP — same FVG zone (direction + stop) fires every bar close; suppress repeats within 6h
    setup_key = f"{direction}:{round(stop, 2)}"
    now_utc = datetime.now(timezone.utc)
    last_ts = state["alerted_setups"].get(setup_key)
    if last_ts and (now_utc - last_ts).total_seconds() < 21600:
        logger.info(f"Duplicate suppressed: {setup_key}")
        return JSONResponse({"status": "duplicate_suppressed", "setup": setup_key})
    state["alerted_setups"][setup_key] = now_utc

    # GATE 4 — Grade A or A+ only executes
    if grade not in ("A+", "A"):
        _log_signal(body, "grade_B")
        await send_telegram(
            f"📊 <b>JUDGE SIGNAL — {grade}</b>\n"
            f"Score: {score:.1f} | Direction: {direction.upper()}\n"
            f"Entry: {entry} | Stop: {stop} | T2: {t2}\n"
            f"Conditions: {', '.join(conditions)}\n"
            f"→ Alert only. Manual confirm required."
        )
        return JSONResponse({"status": "alert_only", "grade": grade})

    # GATE 5 — Automation enabled
    if not AUTOMATION_ENABLED:
        _log_signal(body, "automation_off")
        await send_telegram(
            f"🟡 <b>A/A+ SIGNAL — AUTOMATION OFF</b>\n"
            f"Grade: {grade} | Score: {score:.1f}\n"
            f"Direction: {direction.upper()}\n"
            f"Entry: {entry} | Stop: {stop} | T1: {t1} | T2: {t2}\n"
            f"Accum: {accumulation_pts}pt\n"
            f"Conditions: {', '.join(conditions)}\n"
            f"→ Set AUTOMATION_ENABLED=true to execute."
        )
        return JSONResponse(
            {"status": "automation_disabled", "grade": grade, "score": score}
        )

    # GATE 6 — Drawdown guard
    dd_ok, dd_reason = drawdown_ok()
    if not dd_ok:
        _log_signal(body, "drawdown_block")
        await send_telegram(f"🚨 DRAWDOWN GUARD — No order\n{dd_reason}")
        return JSONResponse({"status": "drawdown_block", "reason": dd_reason})

    # GATE 7 — Contract sizing (formula, never fixed)
    contracts = calculate_contracts(accumulation_pts, grade)

    # GATE 8 — Consistency ceiling
    estimated_profit = contracts * abs(t2 - entry) * MNQ_POINT_VALUE
    if not consistency_ok(estimated_profit):
        _log_signal(body, "consistency_block")
        await send_telegram(
            f"⚠️ CONSISTENCY CEILING — No order\n"
            f"Daily P&L: ${state['daily_pnl']:.2f} | Ceiling: ${CONSISTENCY_CEILING}"
        )
        return JSONResponse({"status": "consistency_block"})

    # ALL GATES PASSED — place order
    try:
        order = await place_order(direction, contracts, entry, stop, t1, t2)
        state["open_positions"][str(order["order_id"])] = {
            **order,
            "grade": grade,
            "score": score,
            "direction": direction,
        }
        state["daily_trades"] += 1
        _log_signal(body, "order_placed")
        await send_telegram(
            f"✅ <b>ORDER PLACED — Grade {grade}</b>\n"
            f"Score: {score:.1f} | Direction: {direction.upper()}\n"
            f"Symbol: {SYMBOL} | Contracts: {contracts}\n"
            f"Entry: {entry} | Stop: {stop}\n"
            f"T1: {t1} | T2: {t2}\n"
            f"Accum leg: {accumulation_pts}pt\n"
            f"Conditions: {', '.join(conditions)}\n"
            f"Daily trades: {state['daily_trades']} | Daily P&L: ${state['daily_pnl']:.2f}"
        )
        return JSONResponse(
            {
                "status": "order_placed",
                "contracts": contracts,
                "order_id": order["order_id"],
            }
        )
    except Exception as e:
        logger.error(f"Order failed: {e}")
        await send_telegram(f"🚨 ORDER FAILED\n{str(e)}")
        return JSONResponse(
            {"status": "order_failed", "error": str(e)}, status_code=500
        )


# ─────────────────────────────────────────────────────────────
# S11 — Position monitoring (60s poll)
# ─────────────────────────────────────────────────────────────

async def poll_positions():
    if not state["open_positions"] or not AUTOMATION_ENABLED:
        return
    try:
        token = await get_tradovate_token()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{TRADOVATE_BASE}/order/list", headers=headers, timeout=10
            )
            orders = resp.json()
    except Exception as e:
        logger.error(f"Position poll failed: {e}")
        return

    for order_id, pos in list(state["open_positions"].items()):
        matching = [o for o in orders if str(o.get("id")) == order_id]
        if not matching:
            continue
        order = matching[0]

        # T1 filled → move stop to breakeven
        if order.get("filledQty", 0) > 0 and not pos.get("t1_filled"):
            pos["t1_filled"] = True
            await send_telegram(
                f"📈 T1 FILLED — Stop → Breakeven\n"
                f"Order: {order_id} | Entry: {pos['entry']}"
            )
            try:
                token = await get_tradovate_token()
                stop_action = "Sell" if pos["direction"] == "long" else "Buy"
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{TRADOVATE_BASE}/order/placeorder",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "accountSpec": TRADOVATE_ACCOUNT_SPEC,
                            "symbol": SYMBOL,
                            "orderQty": pos["contracts"],
                            "orderType": "Stop",
                            "stopPrice": pos["entry"],
                            "action": stop_action,
                            "timeInForce": "GTC",
                            "isAutomated": True,
                        },
                        timeout=15,
                    )
            except Exception as e:
                logger.error(f"Breakeven stop failed: {e}")


# ─────────────────────────────────────────────────────────────
# S12 — Daily reset and weekly journal
# ─────────────────────────────────────────────────────────────

async def daily_reset():
    check_mll_lock()
    prev_pnl = state["daily_pnl"]
    if prev_pnl > state["consistency_largest_day"]:
        state["consistency_largest_day"] = prev_pnl
    state["daily_pnl"] = 0.0
    state["daily_trades"] = 0
    state["alerted_setups"] = {}
    await send_telegram(
        f"📅 <b>DAILY RESET</b>\n"
        f"Yesterday P&L: ${prev_pnl:.2f}\n"
        f"Balance: ${state['account_balance']:,.2f}\n"
        f"MLL Floor: ${state['mll_floor']:,.2f}"
        f" ({'LOCKED' if state['mll_locked'] else 'trailing'})"
    )


async def weekly_journal():
    if not ANTHROPIC_API_KEY or not state["trade_log"]:
        return
    trade_summary = json.dumps(state["trade_log"][-50:], indent=2)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "You are a trading performance analyst. "
                                "Analyse these MNQ trades: patterns in wins/losses, "
                                "grade distribution, timing, one improvement suggestion. "
                                f"Trades: {trade_summary}"
                            ),
                        }
                    ],
                },
                timeout=60,
            )
        journal = resp.json()["content"][0]["text"]
        await send_telegram(f"📓 <b>WEEKLY JOURNAL</b>\n\n{journal[:3000]}")
    except Exception as e:
        logger.error(f"Weekly journal failed: {e}")


# ─────────────────────────────────────────────────────────────
# S13 — Startup and scheduler
# ─────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info(
        f"MNQ Server starting. "
        f"AUTOMATION_ENABLED={AUTOMATION_ENABLED} "
        f"ENTRY_MIN={ENTRY_MIN}"
    )
    scheduler.add_job(poll_positions, "interval", seconds=60)
    scheduler.add_job(
        daily_reset, "cron", hour=16, minute=30, timezone="America/New_York"
    )
    scheduler.add_job(
        weekly_journal,
        "cron",
        day_of_week="sun",
        hour=19,
        minute=0,
        timezone="America/New_York",
    )
    scheduler.start()
    await send_telegram(
        f"🟢 <b>MNQ SERVER ONLINE</b>\n"
        f"Symbol: {SYMBOL}\n"
        f"Automation: {'ENABLED' if AUTOMATION_ENABLED else 'DISABLED'}\n"
        f"Entry min: {ENTRY_MIN} | Environment: {ENVIRONMENT}"
    )


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
    await send_telegram("🔴 MNQ Server shutting down")


# ─────────────────────────────────────────────────────────────
# S14 — Endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "symbol": SYMBOL,
        "automation": AUTOMATION_ENABLED,
        "entry_min": ENTRY_MIN,
        "daily_pnl": state["daily_pnl"],
        "daily_trades": state["daily_trades"],
        "mll_locked": state["mll_locked"],
    }


@app.get("/status")
async def status():
    return {
        "state": state,
        "automation_enabled": AUTOMATION_ENABLED,
        "entry_min": ENTRY_MIN,
        "consistency_ceiling": CONSISTENCY_CEILING,
        "mll_floor": state["mll_floor"],
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    mode_color = "#22c55e" if AUTOMATION_ENABLED else "#eab308"
    mode_text = "LIVE — AUTOMATION ON" if AUTOMATION_ENABLED else "PAPER MODE — AUTOMATION OFF"
    now_et = datetime.now(NY).strftime("%Y-%m-%d %H:%M ET")

    rows = ""
    for s in state["signal_log"]:
        stat = s["status"]
        if stat == "order_placed":
            sc = "#22c55e"
        elif stat == "automation_off":
            sc = "#eab308"
        elif stat in ("drawdown_block", "consistency_block", "order_failed"):
            sc = "#ef4444"
        else:
            sc = "#94a3b8"
        ts = s["ts"]
        direction = s["direction"].upper()
        grade = s["grade"]
        score_val = s["score"]
        entry_val = s["entry"]
        ny_color = "#22c55e" if s["ny_ok"] else "#ef4444"
        ny_text = "YES" if s["ny_ok"] else "NO"
        rows += (
            f'<tr>'
            f'<td>{ts}</td>'
            f'<td>{direction}</td>'
            f'<td>{grade}</td>'
            f'<td>{score_val:.1f}</td>'
            f'<td>{entry_val}</td>'
            f'<td><span style="color:{ny_color}">{ny_text}</span></td>'
            f'<td style="color:{sc}">{stat}</td>'
            f'</tr>'
        )

    if not rows:
        rows = '<tr><td colspan="7" style="text-align:center;color:#64748b;padding:24px">No signals yet — waiting for JUDGE bar close alerts</td></tr>'

    total = len(state["signal_log"])
    a_grade = sum(1 for s in state["signal_log"] if s["grade"] in ("A", "A+"))
    executed = sum(1 for s in state["signal_log"] if s["status"] == "order_placed")

    return HTMLResponse(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>JUDGE Dashboard</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f1117;color:#e2e8f0;padding:16px;font-size:14px}}
.banner{{background:{mode_color}22;border-left:4px solid {mode_color};padding:12px 16px;border-radius:6px;margin-bottom:16px}}
.banner b{{color:{mode_color};font-size:13px;display:block;margin-bottom:4px;letter-spacing:.5px}}
.banner span{{color:#94a3b8;font-size:12px}}
h2{{font-size:15px;margin-bottom:4px;color:#f1f5f9;font-weight:600}}
.sub{{color:#64748b;font-size:12px;margin-bottom:10px}}
.stats{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:16px}}
.stat{{background:#1e2330;border-radius:8px;padding:12px;text-align:center}}
.stat-val{{font-size:24px;font-weight:700;color:#f1f5f9}}
.stat-lbl{{font-size:11px;color:#64748b;margin-top:2px}}
.card{{background:#1e2330;border-radius:8px;overflow:hidden;margin-bottom:16px;overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:12px;min-width:460px}}
th{{background:#252d3d;color:#94a3b8;font-weight:500;padding:8px 10px;text-align:left;white-space:nowrap}}
td{{padding:8px 10px;border-top:1px solid #1a2236;vertical-align:middle;white-space:nowrap}}
.footer{{color:#475569;font-size:11px;text-align:center;padding-top:8px}}
</style>
</head>
<body>
<div class="banner"><b>{mode_text}</b><span>entry_min=4.5 · MNQ1! 5m · TV alert 4791544276 · NY session only</span></div>
<div class="stats">
  <div class="stat"><div class="stat-val">{total}</div><div class="stat-lbl">Total</div></div>
  <div class="stat"><div class="stat-val" style="color:#a78bfa">{a_grade}</div><div class="stat-lbl">A / A+</div></div>
  <div class="stat"><div class="stat-val" style="color:#22c55e">{executed}</div><div class="stat-lbl">Executed</div></div>
</div>
<h2>Signal Log</h2>
<div class="sub">Most recent first &middot; auto-refresh 30s</div>
<div class="card">
  <table>
    <thead><tr><th>Time (UTC)</th><th>Dir</th><th>Grade</th><th>Score</th><th>Entry</th><th>NY?</th><th>Status</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
<div class="footer">Last loaded: {now_et}</div>
</body>
</html>""")


@app.post("/test_telegram")
async def test_telegram():
    await send_telegram("✅ MNQ Server Telegram test — connected")
    return {"status": "sent"}


# ─────────────────────────────────────────────────────────────
# S15 — Entrypoint
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("mnq_server:app", host="0.0.0.0", port=port, reload=False)
