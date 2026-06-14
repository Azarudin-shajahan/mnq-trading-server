#!/usr/bin/env python3
"""Local dashboard server: serves the repo over http AND proxies ElevenLabs TTS
so the API key NEVER lives in the dashboard HTML or the page.

Key resolution (first hit wins):
  1. env ELEVENLABS_API_KEY
  2. first line of ~/.mnq_tts_key   (create with: echo 'sk_...' > ~/.mnq_tts_key && chmod 600 ~/.mnq_tts_key)

Run:  /usr/local/bin/python3 ~/mnq_trading/diagnostics/dashboard_server.py [port]
Dashboard then at http://127.0.0.1:<port>/diagnostics/project_dashboard.html
"""
import json
import os
import secrets
import subprocess
import sys
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.expanduser("~/mnq_trading")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
KEY_FILE = os.path.expanduser("~/.mnq_tts_key")
# Default voice = ElevenLabs "Daniel" (authoritative British male, JARVIS-ish).
DEFAULT_VOICE = os.environ.get("ELEVENLABS_VOICE_ID", "onwK4e9ZLuTAKqWW03F9")
MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# --- embedded terminal (/exec): OFF unless DASH_ENABLE_EXEC=1; guarded by a
# per-launch token + localhost-origin check. Token is readable only same-origin. ---
EXEC_ON = os.environ.get("DASH_ENABLE_EXEC") == "1"
TOKEN = secrets.token_hex(16)
CWD = {"d": REPO}


def get_key():
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if k:
        return k
    try:
        with open(KEY_FILE) as f:
            return f.readline().strip()
    except Exception:
        return ""


class Handler(SimpleHTTPRequestHandler):
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.split("?")[0] == "/token":
            return self._json(200, {"token": TOKEN, "exec": EXEC_ON})
        return super().do_GET()

    def do_POST(self):
        p = self.path.split("?")[0]
        if p == "/tts":
            return self._tts()
        if p == "/exec":
            return self._exec()
        return self._json(404, {"error": "not found"})

    def _exec(self):
        if not EXEC_ON:
            return self._json(403, {"error": "exec_disabled",
                                    "hint": "relaunch server with DASH_ENABLE_EXEC=1"})
        if self.headers.get("X-Token", "") != TOKEN:
            return self._json(403, {"error": "bad_token"})
        org = self.headers.get("Origin") or self.headers.get("Referer") or ""
        if org and not org.startswith("http://127.0.0.1:%d" % PORT):
            return self._json(403, {"error": "bad_origin"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            cmd = (json.loads(self.rfile.read(n) or b"{}").get("cmd") or "").strip()
        except Exception:
            return self._json(400, {"error": "bad request"})
        if not cmd:
            return self._json(400, {"error": "no cmd"})
        if cmd == "cd" or cmd.startswith("cd "):
            tgt = os.path.expanduser(cmd[2:].strip() or "~")
            if not os.path.isabs(tgt):
                tgt = os.path.normpath(os.path.join(CWD["d"], tgt))
            if os.path.isdir(tgt):
                CWD["d"] = tgt
                return self._json(200, {"out": "", "code": 0, "cwd": CWD["d"]})
            return self._json(200, {"out": "cd: no such directory: " + tgt, "code": 1, "cwd": CWD["d"]})
        try:
            r = subprocess.run(["/bin/bash", "-lc", cmd], cwd=CWD["d"],
                               capture_output=True, text=True, timeout=60)
            out = (r.stdout or "") + (r.stderr or "")
            return self._json(200, {"out": out[-20000:], "code": r.returncode, "cwd": CWD["d"]})
        except subprocess.TimeoutExpired:
            return self._json(200, {"out": "[timeout after 60s]", "code": 124, "cwd": CWD["d"]})
        except Exception as ex:
            return self._json(200, {"out": "[error] " + str(ex)[:300], "code": 1, "cwd": CWD["d"]})

    def _tts(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json(400, {"error": "bad request"})
        text = (req.get("text") or "").strip()
        if not text:
            return self._json(400, {"error": "no text"})
        key = get_key()
        if not key:
            return self._json(503, {"error": "no_key",
                                    "hint": "set ELEVENLABS_API_KEY or write the key to ~/.mnq_tts_key"})
        voice = req.get("voice_id") or DEFAULT_VOICE
        url = "https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps" % voice
        body = json.dumps({
            "text": text, "model_id": MODEL,
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.8,
                               "style": 0.25, "use_speaker_boost": True},
        }).encode()
        r = urllib.request.Request(url, data=body, method="POST", headers={
            "xi-api-key": key, "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=30) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as ex:
            return self._json(502, {"error": "tts_http", "status": ex.code,
                                    "detail": ex.read().decode("utf-8", "ignore")[:300]})
        except Exception as ex:
            return self._json(502, {"error": "tts_fail", "detail": str(ex)[:300]})
        return self._json(200, {
            "audio_base64": data.get("audio_base64"),
            "alignment": data.get("alignment") or data.get("normalized_alignment"),
        })

    def log_message(self, *a):
        pass  # quiet


if __name__ == "__main__":
    os.chdir(REPO)
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=REPO))
    print("serving %s on http://127.0.0.1:%d  (POST /tts -> ElevenLabs; key %s)"
          % (REPO, PORT, "FOUND" if get_key() else "MISSING"))
    httpd.serve_forever()
