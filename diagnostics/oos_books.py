import sys
sys.path.insert(0,"/Users/azarudin/mnq_trading/diagnostics")
sys.path.insert(0,"/Users/azarudin/mnq_trading/backtest")
import pandas as pd, warnings; warnings.filterwarnings("ignore")
import model5_ym_halfbudget_portfolio as P
import model9_oneshot_engine as M9
import model5_intraday_engine as M5

df5m,fvgs,news=M9.load_all()
data=M9.make_data("off",df5m,fvgs,news)
o=M9.backtest(dict(M9.DEFAULTS,entry="ote",tp="r2",maxrisk=30),data)
t=M9.backtest(dict(M9.DEFAULTS,entry="turtle",tp="r3",maxrisk=30),data)
m9=P.eq(pd.concat([o,t]).reset_index(drop=True))
sc=dict(M5.DEFAULTS,entry="ote",tp="r1",exit="kz",session="ny")
m5nq=P.eq(M5.backtest(dict(sc),"nq"))
m5ym=P.eq(M5.backtest(dict(sc),"ym"))
for s in (m9,m5nq,m5ym): s["date"]=pd.to_datetime(s["date"])

def metrics(m9s,nqs,yms):
    w9=P.weekly(m9s,False); wnq=P.weekly(nqs,True); wym=P.weekly(yms,True)
    idx=w9.index.union(wnq.index).union(wym.index)
    a9=w9.reindex(idx,fill_value=0.0); anq=wnq.reindex(idx,fill_value=0.0); aym=wym.reindex(idx,fill_value=0.0)
    A=a9+anq; C=a9+0.5*anq+0.5*aym
    def m(x):
        pf,dd=P.pf_dd(x); n=len(x)
        return dict(total=x.sum(),pf=pf,dd=dd,rdd=(x.sum()/abs(dd) if dd else float('nan')),
                    wk=n, posfrac=(x>0).mean())
    return m(A),m(C),len(m9s),len(nqs),len(yms)

cut=pd.Timestamp("2025-01-01")
print("Frozen Book A / Book C  —  in-sample (2020-2024) vs out-of-sample (2025-2026-05)")
for label,lo,hi in [("IN-SAMPLE 2020-2024",pd.Timestamp("2000-01-01"),cut),
                     ("OUT-OF-SAMPLE 2025-2026",cut,pd.Timestamp("2100-01-01"))]:
    f=lambda s: s[(s.date>=lo)&(s.date<hi)]
    A,C,n9,nn,ny=metrics(f(m9),f(m5nq),f(m5ym))
    yrs=max(0.1,(min(hi,m9.date.max())-max(lo,m9.date.min())).days/365.25)
    print(f"\n== {label} ==  (trades: M9 {n9} / M5nq {nn} / M5ym {ny}; ~{yrs:.1f}y)")
    print(f"  Book A: total ${A['total']:>7,.0f}  ann ${A['total']/yrs:>6,.0f}  PF {A['pf']:>4}  maxDD ${A['dd']:>7,.0f}  return/DD {A['rdd']:>5.1f}  wk+ {A['posfrac']*100:.0f}%")
    print(f"  Book C: total ${C['total']:>7,.0f}  ann ${C['total']/yrs:>6,.0f}  PF {C['pf']:>4}  maxDD ${C['dd']:>7,.0f}  return/DD {C['rdd']:>5.1f}  wk+ {C['posfrac']*100:.0f}%")
print("\nPASS hint: OOS PF in same ballpark as IS PF + positive total + similar wk+% = edge survives OOS.")
print("FAIL hint: OOS PF -> ~1 or negative total = selection artifact (the edge was fit to 2020-2024).")
