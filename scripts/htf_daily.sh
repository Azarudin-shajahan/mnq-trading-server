#!/bin/zsh
# Daily HTF loop (launchd). Refresh NQ/ES/YM bars, then fill any pending journal
# outcomes. On a Databento low-balance/limit block (refresh exit 3), post a macOS
# notification so the user knows to top up + re-anchor. Key is read from keychain
# (launchd runs in the user GUI session, so keychain access works).
export PATH=/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin
ROOT="$HOME/mnq_trading"
LOG="$ROOT/data/htf_daily.log"
cd "$ROOT" || exit 1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') htf_daily =====" >> "$LOG"
KEY=$(security find-generic-password -s DATABENTO_API_KEY -w 2>/dev/null)
if [ -z "$KEY" ]; then
  osascript -e 'display notification "Keychain key missing - re-store DATABENTO_API_KEY." with title "Databento" sound name "Basso"' 2>/dev/null
  echo "ERROR: no keychain key" >> "$LOG"
  exit 1
fi

DATABENTO_API_KEY="$KEY" /usr/local/bin/python3 scripts/databento_daily_refresh.py >> "$LOG" 2>&1
RC=$?
if [ $RC -eq 3 ]; then
  osascript -e 'display notification "Pull blocked: low balance/limit. Top up at databento.com." with title "Databento" sound name "Basso"' 2>/dev/null
  echo "ALERT: low-balance pull block (rc=3)" >> "$LOG"
elif [ $RC -ne 0 ]; then
  # any other failure - notify too, in case a low-balance error was worded
  # differently than expected (check the log for the cause).
  osascript -e 'display notification "Refresh failed (could be low balance). Check ~/mnq_trading/data/htf_daily.log" with title "Databento" sound name "Basso"' 2>/dev/null
  echo "WARN: refresh rc=$RC (notified)" >> "$LOG"
fi

# always try to fill pending outcomes from whatever data we now have
/usr/local/bin/python3 diagnostics/htf_outcomes.py --update-pending >> "$LOG" 2>&1
echo "----- done (refresh rc=$RC) -----" >> "$LOG"
