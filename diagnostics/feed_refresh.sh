#!/bin/bash
# Daily AI-news feed refresh (run by launchd or manually):
#   pull text-only -> classify/digest -> rebuild JARVIS dashboard.
# Add/remove handles by editing ~/social_rips/handles.txt (one per line, no @).
cd "$HOME/mnq_trading/diagnostics" || exit 1
PY=/usr/local/bin/python3
mkdir -p "$HOME/social_rips"
LOG="$HOME/social_rips/feed_refresh.log"
HANDLES=$(grep -vE '^\s*#' "$HOME/social_rips/handles.txt" 2>/dev/null | tr '\n' ' ')
[ -z "${HANDLES// }" ] && HANDLES="RoundtableSpace"
{
  echo "==== refresh $(date) :: handles=$HANDLES ===="
  "$PY" feed_pull.py $HANDLES --limit 1-400
  "$PY" feed_digest.py
  "$PY" bounty_scan.py
  "$PY" build_dashboard.py
  echo "---- done $(date) ----"
} >> "$LOG" 2>&1
