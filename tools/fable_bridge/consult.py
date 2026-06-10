#!/usr/bin/env python3
"""Consult Fable (claude.ai) from Claude Code via the Kimi WebBridge daemon.

Posts a question into the "Trading automation" claude.ai project (model Fable 5),
which carries FABLE_PROJECT_BRIEF (live) as project knowledge, then waits for the
reply and prints it. This is the Claude-Code <-> claude.ai concurrency bridge.

Usage:
    python3 tools/fable_bridge/consult.py "your question"
    python3 tools/fable_bridge/consult.py --new "start a fresh chat then ask this"
    echo "long multi-line question" | python3 tools/fable_bridge/consult.py -

Notes:
  - Reuses the currently-open project chat tab unless --new is given.
  - The brief lives in PROJECT KNOWLEDGE, so a --new chat is still fully Fable-aware.
  - Regenerate + re-upload the brief separately when state changes materially
    (build_brief.py + the upload step in the fable-consult skill).
"""
import argparse
import json
import sys
import time
import urllib.request

DAEMON = "http://127.0.0.1:10086/command"
SESSION = "fable"
PROJECT_URL = "https://claude.ai/project/019d51f7-f663-718d-a59e-9e4acea898fd"


def cmd(action, args, timeout=60):
    payload = {"action": action, "args": args, "session": SESSION}
    req = urllib.request.Request(DAEMON, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())


def ev(code, timeout=60):
    r = cmd("evaluate", {"code": code}, timeout=timeout)
    if not r.get("ok"):
        raise RuntimeError("evaluate failed: %s" % r.get("error"))
    return r.get("data", {}).get("value")


def post_question(question, new_chat):
    if new_chat:
        cmd("navigate", {"url": PROJECT_URL, "newTab": False})
        time.sleep(3)
    # Set the ProseMirror composer text via fill (handles contenteditable).
    r = cmd("fill", {"selector": "div[contenteditable=true]", "value": question})
    if not r.get("ok"):
        raise RuntimeError("could not fill composer: %s" % r.get("error"))
    time.sleep(0.5)
    # Click the send button (aria-label "Send message").
    clicked = ev(
        "(function(){var b=document.querySelector('button[aria-label=\"Send message\"]')"
        "||Array.from(document.querySelectorAll('button')).find(function(x){"
        "return /send/i.test(x.getAttribute('aria-label')||'')});"
        "if(!b)return 'NOSEND';b.click();return 'sent';})()")
    return clicked


def read_last_assistant():
    # Assistant content lives in .standard-markdown / .font-claude-response.
    # Pick the LONGEST such block (the actual answer), not the last DOM node --
    # the trailing node can be an 18-char artifact (e.g. the project title).
    return ev(
        "(function(){var s=document.querySelectorAll("
        "'.standard-markdown,.font-claude-response');"
        "var best='';for(var i=0;i<s.length;i++){var t=s[i].innerText||'';"
        "if(t.length>best.length)best=t;}return best;})()")


def complete():
    # The action bar (copy/retry) renders only when the response has finished.
    return ev(
        "(function(){return !!document.querySelector('[data-testid=action-bar-copy]');})()")


def wait_for_reply(max_wait=300):
    t0 = time.time()
    time.sleep(4)  # let streaming start
    last = ""
    stable = 0
    while time.time() - t0 < max_wait:
        try:
            done = complete()
        except Exception:
            done = False
        cur = read_last_assistant() or ""
        if done and cur and cur == last:
            stable += 1
            if stable >= 2:
                return cur
        else:
            stable = 0
        last = cur
        time.sleep(3)
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", help="question text, or '-' to read stdin")
    ap.add_argument("--new", action="store_true", help="start a fresh project chat first")
    ap.add_argument("--max-wait", type=int, default=300)
    args = ap.parse_args()

    q = sys.stdin.read() if args.question == "-" else args.question
    q = q.strip()
    if not q:
        print("empty question", file=sys.stderr)
        return 2

    status = cmd("evaluate", {"code": "1"})
    if not status.get("ok"):
        print("WebBridge not reachable. Run: ~/.kimi-webbridge/bin/kimi-webbridge status",
              file=sys.stderr)
        return 1

    sent = post_question(q, args.new)
    if sent == "NOSEND":
        print("Could not find the send button (UI changed?).", file=sys.stderr)
        return 1
    reply = wait_for_reply(args.max_wait)
    print(reply if reply else "(no reply captured within timeout)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
