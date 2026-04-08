import os, json, math, logging, asyncio
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mnq_server")

NY = ZoneInfo("America/New_York")
app = FastAPI(title="MNQ Trading Server")
scheduler = AsyncIOScheduler(timezone="America/New_York")

WEBHOOK_SECRET       = os.getenv("WEBHOOK_SECRET", "mnq_azarudin_2026")
AUTOMATION_ENABLED   = os.getenv("AUTOMATION_ENABLED", "false").lower() == "true"
SYMBOL               = os.getenv("SYMBOL", "MNQM6")
ENVIRONMENT          = os.getenv("ENVIRONMENT", "auto")
DAILY_TARGET_EVAL    = float(os.getenv("DAILY_TARGET_EVAL", "1200"))
CONSISTENCY_CEILING  = float(os.getenv("CONSISTENCY_CEILING", "1560"))
MLL_LOCK_TRIGGER     = float(os.getenv("MLL_LOCK_TRIGGER", "52100"))
MLL_LOCKED_FLOOR     = float(os.getenv("MLL_LOCKED_FLOOR", "50100"))
TELEGRAM_BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID", "")
TRADOVATE_USERNAME   = os.getenv("TRADOVATE_USERNAME", "")
TRADOVATE_PASSWORD   = os.getenv("TRADOVATE_PASSWORD", "")
TRADOVATE_ACCOUNT_SPEC = os.getenv("TRADOVATE_ACCOUNT_SPEC", "")
ANTHROPIC_API_KEY    = os.getenv("ANTHROPIC_API_KEY", "")

ENTRY_MIN = 5.0
MNQ_POINT_VALUE = 0.50

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
}

TRADOVATE_BASE = "https://demo.tradovateapi.com/v1"

async def get_tradovate_token() -> str:
    now = datetime.now(timezone.utc)
    if state["tradovate_token"] and state["tradovate_token_expiry"] > now:
        return state["tradovate_token"]
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{TRADOVATE_BASE}/auth/accesstokenrequest", json={
            "name": TRADOVATE_USERNAME, "password": TRADOVATE_PASSWORD,
            "appId": "MNQServer", "appVersion": "1.0", "cid": 0, "sec": ""
        })
        data = resp.json()
        state["tradovate_token"] = data["accessToken"]
        state["tradovate_token_expiry"] = datetime.fromisoformat(data["expirationTime"]).replace(tzinfo=timezone.utc)
        logger.info("Tradovate token refreshed")
        return state["tradovate_token"]

def calculate_contracts(accumulation_pts: float, grade: str) -> int:
    if accumulation_pts <= 0:
        return 1
    t2_per_contract = accumulation_pts * 2.5 * MNQ_POINT_VALUE
    if t2_per_contract <= 0:
        return 1
    raw = math.floor(DAILY_TARGET_EVAL / t2_per_contract)
    cap = 40
    contracts = max(1, min(raw, cap))
    logger.info(f"Sizing: {accumulation_pts}pt → T2/contract=${t2_per_contract:.2f} → raw={raw} → capped={contracts}")
    return contracts

def consistency_ok(proposed_pnl: float) -> bool:
    projected = state["daily_pnl"] + proposed_pnl
    if projected > CONSISTENCY_CEILING:
        logger.warning(f"Consistency ceiling: projected {projected:.2f} > {CONSISTENCY_CEILING}")
        return False
    return True

def drawdown_ok() -> tuple[bool, str]:
    if state["mll_locked"]:
        if state["account_balance"] <= MLL_LOCKED_FLOOR:
            return False, f"MLL locked floor breached: {state['account_balance']:.2f} <= {MLL_LOCKED_FLOOR}"
        return True, "ok"
    else:
        if state["account_balance"] <= state["mll_floor"]:
            return False, f"MLL floor breached: {state['account_balance']:.2f} <= {state['mll_floor']:.2f}"
        return True, "ok"

def check_mll_lock():
    if not state["mll_locked"] and state["account_balance"] > MLL_LOCK_TRIGGER:
        state["mll_locked"] = True
        state["mll_floor"] = MLL_LOCKED_FLOOR
        logger.info(f"MLL LOCKED at {MLL_LOCKED_FLOOR}")
        asyncio.create_task(send_telegram(
            f"🔒 MLL LOCKED\nFloor: ${MLL_LOCKED_FLOOR:,.0f} permanent"
        ))

async def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message,
                                         "parse_mode": "HTML"}, timeout=10)
        except Exception as e:
            logger.error(f"Telegram failed: {e}")

async def place_order(direction: str, contracts: int, entry: float,
                      stop: float, t1: float, t2: float) -> dict:
    token = await get_tradovate_token()
    action = "Buy" if direction == "long" else "Sell"
    stop_action = "Sell" if direction == "long" else "Buy"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{TRADOVATE_BASE}/order/placeorder", headers=headers, json={
            "accountSpec": TRADOVATE_ACCOUNT_SPEC, "symbol": SYMBOL,
            "orderQty": contracts, "orderType": "Limit",
            "price": entry, "action": action, "timeInForce": "Day"
        }, timeout=15)
        order = resp.json()
        order_id = order.get("orderId") or order.get("id")
        await client.post(f"{TRADOVATE_BASE}/order/placeorder", headers=headers, json={
            "accountSpec": TRADOVATE_ACCOUNT_SPEC, "symbol": SYMBOL,
            "orderQty": contracts, "orderType": "Stop",
            "stopPrice": stop, "action": stop_action,
            "timeInForce": "GTC", "isAutomated": True
        }, timeout=15)
    logger.info(f"Order placed: {action} {contracts}x {SYMBOL} @ {entry}")
    return {"order_id": order_id, "entry": entry, "stop": stop, "t1": t1, "t2": t2, "contracts": contracts}

@app.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.json()

    if body.get("secret") != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    if not body.get("ssmt_confirmed", False):
        logger.warning("SSMT not confirmed — rejecting")
        await send_telegram("⚠️ Webhook received but SSMT not confirmed — rejected")
        return JSONResponse({"status": "gate_failed", "reason": "ssmt_not_confirmed"})

    score = float(body.get("score", 0))
    grade = body.get("grade", "C")
    direction = body.get("direction", "")
    entry = float(body.get("entry", 0))
    stop = float(body.get("stop", 0))
    t1 = float(body.get("t1", 0))
    t2 = float(body.get("t2", 0))
    accumulation_pts = float(body.get("accumulation_pts", 0))
    conditions = body.get("conditions", [])

    if score < ENTRY_MIN:
        await send_telegram(
            f"📊 <b>JUDGE SIGNAL — BELOW THRESHOLD</b>\n"
            f"Grade: {grade} | Score: {score:.1f} | Min: {ENTRY_MIN}\n"
            f"Direction: {direction.upper()} | Logged only."
        )
        return JSONResponse({"status": "below_threshold", "score": score})

    if grade not in ("A+", "A"):
        await send_telegram(
            f"📊 <b>JUDGE SIGNAL — {grade}</b>\n"
            f"Score: {score:.1f} | Direction: {direction.upper()}\n"
            f"Entry: {entry} | Stop: {stop} | T2: {t2}\n"
            f"Conditions: {', '.join(conditions)}\n→ Alert only. Manual confirm."
        )
        return JSONResponse({"status": "alert_only", "grade": grade})

    if not AUTOMATION_ENABLED:
        await send_telegram(
            f"🟡 <b>A/A+ SIGNAL — AUTOMATION OFF</b>\n"
            f"Grade: {grade} | Score: {score:.1f}\n"
            f"Direction: {direction.upper()}\n"
            f"Entry: {entry} | Stop: {stop} | T1: {t1} | T2: {t2}\n"
            f"Accum: {accumulation_pts}pt\nConditions: {', '.join(conditions)}\n"
            f"→ Set AUTOMATION_ENABLED=true to execute."
        )
        return JSONResponse({"status": "automation_disabled", "grade": grade, "score": score})

    dd_ok, dd_reason = drawdown_ok()
    if not dd_ok:
        await send_telegram(f"🚨 DRAWDOWN GUARD — No order\n{dd_reason}")
        return JSONResponse({"status": "drawdown_block", "reason": dd_reason})

    contracts = calculate_contracts(accumulation_pts, grade)

    estimated_profit = contracts * abs(t2 - entry) * MNQ_POINT_VALUE
    if not consistency_ok(estimated_profit):
        await send_telegram(
            f"⚠️ CONSISTENCY CEILING — No order\n"
            f"Daily P&L: ${state['daily_pnl']:.2f} | Ceiling: ${CONSISTENCY_CEILING}"
        )
        return JSONResponse({"status": "consistency_block"})

    try:
        order = await place_order(direction, contracts, entry, stop, t1, t2)
        state["open_positions"][str(order["order_id"])] = {
            **order, "grade": grade, "score": score, "direction": direction
        }
        state["daily_trades"] += 1
        await send_telegram(
            f"✅ <b>ORDER PLACED — Grade {grade}</b>\n"
            f"Score: {score:.1f} | Direction: {direction.upper()}\n"
            f"Symbol: {SYMBOL} | Contracts: {contracts}\n"
            f"Entry: {entry} | Stop: {stop}\nT1: {t1} | T2: {t2}\n"
            f"Accum leg: {accumulation_pts}pt\nConditions: {', '.join(conditions)}\n"
            f"Daily trades: {state['daily_trades']} | Daily P&L: ${state['daily_pnl']:.2f}"
        )
        return JSONResponse({"status": "order_placed", "contracts": contracts, "order_id": order["order_id"]})
    except Exception as e:
        logger.error(f"Order failed: {e}")
        await send_telegram(f"🚨 ORDER FAILED\n{str(e)}")
        return JSONResponse({"status": "order_failed", "error": str(e)}, status_code=500)

async def poll_positions():
    if not state["open_positions"] or not AUTOMATION_ENABLED:
        return
    try:
        token = await get_tradovate_token()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{TRADOVATE_BASE}/order/list", headers=headers, timeout=10)
            orders = resp.json()
    except Exception as e:
        logger.error(f"Position poll failed: {e}")
        return
    for order_id, pos in list(state["open_positions"].items()):
        matching = [o for o in orders if str(o.get("id")) == order_id]
        if not matching:
            continue
        order = matching[0]
        if order.get("filledQty", 0) > 0 and not pos.get("t1_filled"):
            pos["t1_filled"] = True
            await send_telegram(f"📈 T1 FILLED — Stop → Breakeven\nOrder: {order_id} | Entry: {pos['entry']}")
            try:
                token = await get_tradovate_token()
                stop_action = "Sell" if pos["direction"] == "long" else "Buy"
                async with httpx.AsyncClient() as client:
                    await client.post(f"{TRADOVATE_BASE}/order/placeorder",
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                        json={"accountSpec": TRADOVATE_ACCOUNT_SPEC, "symbol": SYMBOL,
                              "orderQty": pos["contracts"], "orderType": "Stop",
                              "stopPrice": pos["entry"], "action": stop_action,
                              "timeInForce": "GTC", "isAutomated": True}, timeout=15)
            except Exception as e:
                logger.error(f"BE stop failed: {e}")

async def daily_reset():
    check_mll_lock()
    prev_pnl = state["daily_pnl"]
    if prev_pnl > state["consistency_largest_day"]:
        state["consistency_largest_day"] = prev_pnl
    state["daily_pnl"] = 0.0
    state["daily_trades"] = 0
    await send_telegram(
        f"📅 <b>DAILY RESET</b>\nYesterday P&L: ${prev_pnl:.2f}\n"
        f"Balance: ${state['account_balance']:,.2f}\n"
        f"MLL Floor: ${state['mll_floor']:,.2f} ({'LOCKED' if state['mll_locked'] else 'trailing'})"
    )

async def weekly_journal():
    if not ANTHROPIC_API_KEY or not state["trade_log"]:
        return
    trade_summary = json.dumps(state["trade_log"][-50:], indent=2)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01",
                         "Content-Type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 1000,
                      "messages": [{"role": "user", "content":
                          f"Trading performance analyst. Analyse these MNQ trades: patterns in wins/losses, grade distribution, timing, one improvement suggestion. Trades: {trade_summary}"}]},
                timeout=60)
        journal = resp.json()["content"][0]["text"]
        await send_telegram(f"📓 <b>WEEKLY JOURNAL</b>\n\n{journal[:3000]}")
    except Exception as e:
        logger.error(f"Weekly journal failed: {e}")

@app.on_event("startup")
async def startup():
    logger.info(f"MNQ Server starting. AUTOMATION_ENABLED={AUTOMATION_ENABLED} ENTRY_MIN={ENTRY_MIN}")
    scheduler.add_job(poll_positions, "interval", seconds=60)
    scheduler.add_job(daily_reset, "cron", hour=16, minute=30, timezone="America/New_York")
    scheduler.add_job(weekly_journal, "cron", day_of_week="sun", hour=19, minute=0, timezone="America/New_York")
    scheduler.start()
    await send_telegram(
        f"🟢 <b>MNQ SERVER ONLINE</b>\nSymbol: {SYMBOL}\n"
        f"Automation: {'ENABLED' if AUTOMATION_ENABLED else 'DISABLED'}\n"
        f"Entry min: {ENTRY_MIN} | Environment: {ENVIRONMENT}"
    )

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
    await send_telegram("🔴 MNQ Server shutting down")

@app.get("/health")
async def health():
    return {"status": "ok", "symbol": SYMBOL, "automation": AUTOMATION_ENABLED,
            "entry_min": ENTRY_MIN, "daily_pnl": state["daily_pnl"],
            "daily_trades": state["daily_trades"], "mll_locked": state["mll_locked"]}

@app.get("/status")
async def status():
    return {"state": state, "automation_enabled": AUTOMATION_ENABLED,
            "entry_min": ENTRY_MIN, "consistency_ceiling": CONSISTENCY_CEILING,
            "mll_floor": state["mll_floor"]}

@app.post("/test_telegram")
async def test_telegram():
    await send_telegram("✅ MNQ Server Telegram test — connected")
    return {"status": "sent"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("mnq_server:app", host="0.0.0.0", port=port, reload=False)
