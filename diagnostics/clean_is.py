import sys; sys.path.insert(0,"/Users/azarudin/mnq_trading/diagnostics"); sys.path.insert(0,"/Users/azarudin/mnq_trading/backtest")
import pandas as pd, warnings; warnings.filterwarnings("ignore")
import model9_oneshot_engine as M9, model5_intraday_engine as M5
import model5_ym_halfbudget_portfolio as P
from pathlib import Path
DATA=Path.home()/"mnq_trading/data"
# REPOINT engines to clean 2020-2024 files (physically end 2024-12-31)
M9.M5   = DATA/"MULTI_5min_IST_2020_2024.csv"
M9.H4   = DATA/"MULTI_4h_IST_2020_2024.csv"
M9.DAILY= DATA/"MULTI_1d_IST_2020_2024.csv"
print("engine 5m ->", M9.M5.name, "| 4h ->", M9.H4.name)

df5m,fvgs,news=M9.load_all()
print("CLEAN data max date:", pd.to_datetime(df5m['timestamp']).max())
data=M9.make_data("off",df5m,fvgs,news)
o=M9.backtest(dict(M9.DEFAULTS,entry="ote",tp="r2",maxrisk=30),data)
t=M9.backtest(dict(M9.DEFAULTS,entry="turtle",tp="r3",maxrisk=30),data)
m9=P.eq(pd.concat([o,t]).reset_index(drop=True))
sc=dict(M5.DEFAULTS,entry="ote",tp="r1",exit="kz",session="ny")
m5nq=P.eq(M5.backtest(dict(sc),"nq")); m5ym=P.eq(M5.backtest(dict(sc),"ym"))

w9=P.weekly(m9,False); wnq=P.weekly(m5nq,True); wym=P.weekly(m5ym,True)
idx=w9.index.union(wnq.index).union(wym.index)
a9=w9.reindex(idx,fill_value=0.0); anq=wnq.reindex(idx,fill_value=0.0); aym=wym.reindex(idx,fill_value=0.0)
A=a9+anq; C=a9+0.5*anq+0.5*aym
def m(x,nm):
    pf,dd=P.pf_dd(x); yrs=max(0.1,(idx.max()-idx.min()).days/365.25)
    print(f"  {nm}: total ${x.sum():>7,.0f} ann ${x.sum()/yrs:>6,.0f} PF {pf} maxDD ${dd:>6,.0f} return/DD {x.sum()/abs(dd):.1f} annRet/DD {(x.sum()/yrs)/abs(dd):.2f}")
print(f"\n=== CLEAN IN-SAMPLE 2020-2024 ONLY (M9 {len(m9)} / M5nq {len(m5nq)} / M5ym {len(m5ym)}) ===")
m(A,"Book A"); m(C,"Book C")
print("\nCompare to: full-file IS slice was A PF2.59/annRetDD~4.5, C PF2.83/annRetDD~5.4")
print("           2025-26 holdout was   A PF2.23/annRetDD~4.3, C PF2.47/annRetDD~5.2")
