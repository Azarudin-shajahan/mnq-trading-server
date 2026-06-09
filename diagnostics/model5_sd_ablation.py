#!/usr/bin/env python3
"""
Model 5 SD-confluence ("the Grail") ablation - clears the YM cross-index BLOCKER 3
(SD-confluence named in the spec but never built/ablated, parallel to Model 9 COT).

ICT's standard-deviation confluence projects an overnight dealing range (CBDR / Asian /
flout) in 1-3 SD (range multiples) and claims entries/targets confluent with an SD line
are higher-probability. It is emphatically DISCRETIONARY -> the exact fingerprint that
did NOT mechanize for Model 9 COT / GxT drivers. This runs the EXACT M5 production scalp
(--entry ote --tp r1 --exit kz --session ny) on NQ three ways:
  off     = no SD filter (current production)
  confirm = take ONLY entries whose entry OR target confluences with an SD line
  veto    = take ONLY entries that do NOT confluence (the inverse - separation test)

Decision: SD-confluence adds edge ONLY if confirm pf > off pf AND it separates
(confirm > off > veto). If confirm ~ off ~ veto -> non-additive/anti-predictive -> stays
OFF; blocker cleared by "built + ablated, off in production (no edge)".

Imports the engine; touches NO production default (sd defaults off). Prints n/wr/pf/pnl/
maxDD/every-year + per-year per mode + a band-robustness check.
"""
import sys
sys.path.insert(0, "/Users/azarudin/mnq_trading/backtest")
import pandas as pd
import model5_intraday_engine as M5
import model9_oneshot_engine as M9

BASE = dict(M5.DEFAULTS, entry="ote", session="ny", tp="r1", exit="kz",
            half_filter=True, maxrisk=0, min_imp=20.0)


def report(mode, tr):
    s = M9.stats(tr)
    eq = tr.pnl.cumsum() if len(tr) else pd.Series([0.0])
    dd = (eq - eq.cummax()).min()
    py = M9.peryear(tr)
    every = all((v[3] == "inf" or float(v[3]) >= 1.0) for v in py.values()) if py else False
    print("sd=%-8s | n=%4d wr=%4.1f pf=%5s pnl=%7.0fpt maxDD=%6.0fpt every-yr+=%s"
          % (mode, s["n"], s["wr"], s["pf"], s["pnl"], dd, every))
    print("   yr pf: " + " ".join("%s:%s" % (y, v[3]) for y, v in py.items()))
    return dict(mode=mode, n=s["n"], pf=s["pf"], pnl=s["pnl"], dd=round(float(dd), 1))


def main():
    inst = "nq"
    print("=== MODEL 5 OTE-scalp - SD-CONFLUENCE ('Grail') ABLATION on NQ ===")
    print("config: --entry ote --tp r1 --exit kz --session ny (sd OFF in production)\n")
    out = []
    for mode in ["off", "confirm", "veto"]:
        out.append(report(mode, M5.backtest(dict(BASE, sd=mode), inst)))
    base = next(r for r in out if r["mode"] == "off")
    conf = next(r for r in out if r["mode"] == "confirm")
    print("\n=== DELTA vs off (production default) ===")
    for r in out:
        if r["mode"] == "off":
            continue
        print("  %-7s: dPnL %+.0fpt  dN %+d  pf %s->%s  dDD %+.0fpt"
              % (r["mode"], r["pnl"] - base["pnl"], r["n"] - base["n"], base["pf"], r["pf"],
                 r["dd"] - base["dd"]))
    if base["n"]:
        print("  confluence rate (confirm_n / off_n) = %.0f%%" % (100 * conf["n"] / base["n"]))
    print("\n=== confirm-mode band robustness (does the verdict depend on the error band?) ===")
    for bf in [0.10, 0.15, 0.25]:
        s = M9.stats(M5.backtest(dict(BASE, sd="confirm", sd_band_frac=bf), inst))
        print("  band=%2.0f%% of SD-range: n=%4d pf=%5s pnl=%7.0fpt" % (bf * 100, s["n"], s["pf"], s["pnl"]))
    print("\nVERDICT INPUT: SD-confluence helps ONLY if confirm pf > off pf AND it separates "
          "(confirm > off > veto).")
    print("If confirm ~ off ~ veto -> 'the Grail' is non-additive/anti-predictive (like COT) "
          "-> stays OFF; YM blocker 3 cleared.")


if __name__ == "__main__":
    main()
