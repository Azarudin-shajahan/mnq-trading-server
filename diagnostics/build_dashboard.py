#!/usr/bin/env python3
"""Project dashboard generator (deterministic, zero-LLM).

Pulls from three sources and renders a single project view:
  1. project_state.yaml   - small hand-edited "now / next" file (same dir)
  2. git log of ~/mnq_trading  - "what happened"
  3. memory *_result.md frontmatter - validated-engine ledger

Outputs:
  - project_dashboard.html  (local; also the future Railway /research page)
  - Project_Dashboard.md    (Obsidian vault root; syncs to phone)

Regenerate any time with:  python3 build_dashboard.py
ASCII-only source on purpose (this Python 3.10 rejects U+2014 in literals).
"""
import datetime
import glob
import html
import json
import os
import re
import subprocess

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "project_state.yaml")
MNQ_REPO = os.path.expanduser("~/mnq_trading")
MEM_DIR = os.path.expanduser("~/.claude/projects/-Users-azarudin/memory")
OUT_HTML = os.path.join(HERE, "project_dashboard.html")
VAULT = "/Users/azarudin/Documents/MNQ trading/Trading"
OUT_MD = os.path.join(VAULT, "Project_Dashboard.md")
CAP_MD = os.path.join(MEM_DIR, "capabilities.md")  # auto-loaded registry (anti-re-derivation)
SKILLS_DIR = os.path.expanduser("~/.claude/skills")
FEED_FILE = os.path.expanduser("~/social_rips/feed.json")  # text-only knowledge feed (feed_pull.py)
BOUNTY_FILE = os.path.expanduser("~/social_rips/bounties.json")  # scored software bounties (bounty_scan.py)


def load_state():
    with open(STATE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_feed():
    try:
        with open(FEED_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_bounties():
    try:
        with open(BOUNTY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def git_log(n=15):
    try:
        res = subprocess.run(
            ["git", "-C", MNQ_REPO, "log",
             "--pretty=format:%h|%ad|%s", "--date=short", "-%d" % n],
            capture_output=True, text=True, timeout=15,
        )
    except Exception:
        return []
    rows = []
    for line in res.stdout.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            rows.append(parts)
    return rows


def result_engines():
    items = []
    for path in sorted(glob.glob(os.path.join(MEM_DIR, "*_result.md"))):
        try:
            txt = open(path, encoding="utf-8").read()
        except Exception:
            continue
        name, desc = os.path.basename(path), ""
        m = re.match(r"^---\n(.*?)\n---", txt, re.S)
        if m:
            fm = m.group(1)
            nm = re.search(r"^name:\s*(.+)$", fm, re.M)
            dm = re.search(r"^description:\s*(.+)$", fm, re.M)
            if nm:
                name = nm.group(1).strip().strip('"')
            if dm:
                desc = dm.group(1).strip().strip('"')
        items.append((name, desc))
    return items


# ---------- HTML rendering ----------

CSS = """
:root{--c:#39d6ff;--c2:#8be9ff;--amber:#ffb648;--green:#56f0a0;--red:#ff7a7a;
  --panel:rgba(10,22,34,.72);--line:rgba(57,214,255,.28)}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;color:#cfe9f5;letter-spacing:.02em;
  font:14px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  background:radial-gradient(1200px 600px at 50% -10%,rgba(57,214,255,.10),transparent 60%),
    radial-gradient(900px 500px at 100% 100%,rgba(57,214,255,.06),transparent 60%),#03060c}
.scan{position:fixed;inset:0;pointer-events:none;z-index:9;opacity:.5;mix-blend-mode:screen;
  background:repeating-linear-gradient(to bottom,rgba(57,214,255,.04) 0 1px,transparent 1px 3px)}
.wrap{max-width:1080px;margin:0 auto;padding:18px 22px 60px}
#boot{position:fixed;inset:0;z-index:50;background:#03060c;display:flex;align-items:center;
  justify-content:center;color:var(--c);font-size:17px;letter-spacing:.35em;
  text-shadow:0 0 14px var(--c);transition:opacity .6s}
#boot.gone{opacity:0;pointer-events:none}
.hud{display:flex;align-items:center;gap:18px;padding:12px 0 16px;border-bottom:1px solid var(--line)}
.reactor{width:54px;height:54px;border-radius:50%;flex:none;position:relative;
  background:radial-gradient(circle,#dffaff 0%,var(--c) 32%,rgba(57,214,255,.15) 62%,transparent 72%);
  box-shadow:0 0 18px var(--c),0 0 42px rgba(57,214,255,.5)}
.reactor::before,.reactor::after{content:"";position:absolute;inset:4px;border-radius:50%;
  border:2px solid rgba(57,214,255,.6);border-top-color:transparent;border-bottom-color:transparent;
  animation:spin 3.2s linear infinite}
.reactor::after{inset:11px;border-style:dashed;animation-duration:5s;animation-direction:reverse}
@keyframes spin{to{transform:rotate(360deg)}}
.htitle{flex:1}
.htitle h1{margin:0;font-size:20px;color:#eaffff;letter-spacing:.12em;text-transform:uppercase;
  text-shadow:0 0 10px rgba(57,214,255,.6)}
.htitle .sub{margin:3px 0 0;color:#6fb7cf;font-size:11px;letter-spacing:.08em}
.clock{text-align:right;color:var(--c);text-shadow:0 0 8px var(--c);white-space:nowrap}
.clock .t{font-size:21px}
.clock .st{font-size:10px;color:#6fb7cf;letter-spacing:.12em}
.led{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--green);
  box-shadow:0 0 8px var(--green);margin-right:6px;animation:pulse 1.6s ease-in-out infinite}
@keyframes pulse{50%{opacity:.35}}
.cmdbar{display:flex;gap:10px;margin:16px 0 6px;align-items:center;flex-wrap:wrap}
.cmdbar input{flex:1;min-width:220px;background:rgba(57,214,255,.06);border:1px solid var(--line);
  color:#eaffff;padding:10px 12px;border-radius:6px;font:inherit;letter-spacing:.04em;outline:none}
.cmdbar input:focus{box-shadow:0 0 0 1px var(--c),0 0 14px rgba(57,214,255,.4)}
.btn{background:rgba(57,214,255,.10);border:1px solid var(--line);color:var(--c);cursor:pointer;
  padding:10px 13px;border-radius:6px;font:inherit;letter-spacing:.08em;text-transform:uppercase;
  font-size:11px;transition:.15s;white-space:nowrap}
.btn:hover{background:rgba(57,214,255,.22);box-shadow:0 0 12px rgba(57,214,255,.45)}
.panel{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:8px;
  margin:14px 0;padding:0 16px 4px;backdrop-filter:blur(3px);animation:rise .5s both;
  box-shadow:0 0 0 1px rgba(57,214,255,.05),0 0 22px rgba(0,0,0,.5)}
@keyframes rise{from{opacity:0;transform:translateY(8px)}}
.panel::before,.panel::after{content:"";position:absolute;width:14px;height:14px;
  border:2px solid var(--c);opacity:.6}
.panel::before{top:-1px;left:-1px;border-right:0;border-bottom:0}
.panel::after{bottom:-1px;right:-1px;border-left:0;border-top:0}
.phead{cursor:pointer;user-select:none;color:var(--c2);font-size:13px;letter-spacing:.12em;
  text-transform:uppercase;margin:0;padding:12px 0 10px;display:flex;align-items:center;gap:8px;
  text-shadow:0 0 8px rgba(57,214,255,.4)}
.phead .car{transition:.2s;color:var(--c);font-size:10px}
.panel.col .phead .car{transform:rotate(-90deg)}
.panel.col .pbody{display:none}
.pbody{padding-bottom:10px}
h3{font-size:11px;color:#6fb7cf;margin:12px 0 4px;text-transform:uppercase;letter-spacing:.08em}
.sub{color:#6fb7cf}
table{border-collapse:collapse;width:100%;margin:6px 0;font-size:13px}
td,th{border:1px solid rgba(57,214,255,.14);padding:6px 9px;text-align:left;vertical-align:top}
th{background:rgba(57,214,255,.08);color:var(--c2);font-weight:600;text-transform:uppercase;
  font-size:11px;letter-spacing:.06em}
tr:hover td{background:rgba(57,214,255,.05)}
a{color:var(--c);text-decoration:none;border-bottom:1px dotted rgba(57,214,255,.5)}
a:hover{color:#eaffff;text-shadow:0 0 8px var(--c)}
code{background:rgba(57,214,255,.10);padding:1px 5px;border-radius:4px;color:#bff6ff}
ul{margin:6px 0;padding-left:20px}li{margin:3px 0}
.tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:10px;font-weight:700;
  letter-spacing:.05em;border:1px solid transparent}
.PRODUCTION,.VALIDATED,.TESTED,.LIVE,.PASS{background:rgba(86,240,160,.14);color:var(--green);
  border-color:rgba(86,240,160,.4);text-shadow:0 0 6px rgba(86,240,160,.4)}
.SHELVED,.LOCKED,.SCAFFOLD{background:rgba(255,182,72,.14);color:var(--amber);
  border-color:rgba(255,182,72,.4)}
.REFINE,.FUNDEDSTAGE,.FALLBACK,.INSAMPLE{background:rgba(57,214,255,.14);color:var(--c);
  border-color:var(--line)}
.DEAD{background:rgba(255,90,90,.14);color:var(--red);border-color:rgba(255,90,90,.4)}
.foot{color:#4f7a8c;font-size:11px;margin-top:24px;border-top:1px solid var(--line);padding-top:10px}
.hidden{display:none!important}
#cap{position:fixed;left:0;right:0;bottom:0;z-index:20;padding:22px 28px 28px;max-height:42vh;
  overflow:auto;text-align:center;font-size:19px;line-height:1.95;letter-spacing:.03em;color:#5f93a8;
  background:linear-gradient(to top,rgba(3,6,12,.97),rgba(3,6,12,0));
  opacity:0;transform:translateY(24px);transition:.45s;pointer-events:none}
#cap.on{opacity:1;transform:none}
#cap span{transition:color .12s,text-shadow .12s,opacity .12s;opacity:.40}
#cap span.w{color:#eaffff;opacity:1;text-shadow:0 0 12px var(--c),0 0 24px rgba(57,214,255,.65)}
.termout{background:#02040a;border:1px solid var(--line);border-radius:6px;padding:10px 12px;
  height:240px;overflow:auto;white-space:pre-wrap;word-break:break-word;font-size:12.5px;
  color:#bfe9d8;margin:6px 0}
.termout div{margin:1px 0}.termout .cmd{color:var(--c2)}.termout .err{color:#ff9a9a}
.termline{display:flex;align-items:center;gap:8px}
.termcwd{color:var(--amber);white-space:nowrap;font-size:12px}
.terminp{flex:1;background:rgba(57,214,255,.06);border:1px solid var(--line);color:#eaffff;
  padding:8px 10px;border-radius:6px;font:inherit;outline:none}
.terminp:focus{box-shadow:0 0 0 1px var(--c),0 0 12px rgba(57,214,255,.35)}
"""


_TAG_KEYS = ("PRODUCTION", "VALIDATED", "TESTED", "LIVE", "PASS", "SHELVED",
             "LOCKED", "SCAFFOLD", "DEAD", "REFINE", "FUNDEDSTAGE", "FALLBACK", "INSAMPLE")


def tag(text):
    u = re.sub(r"[^A-Z]", "", str(text).upper())
    cls = next((k for k in _TAG_KEYS if k in u), "")
    return '<span class="tag %s">%s</span>' % (cls, html.escape(str(text)))


def _tagcls(tag):
    return {"release": "LIVE", "model": "REFINE", "tool": "FUNDEDSTAGE",
            "research": "LOCKED", "funding": "VALIDATED", "agent": "SCAFFOLD"}.get(str(tag), "")


def _href(p):
    p = str(p)
    if p.startswith("http://") or p.startswith("https://"):
        return p
    ap = os.path.abspath(os.path.expanduser(p))
    # Relative to the dashboard's own dir (HERE) so links work BOTH as a raw
    # file:// open AND when the repo root is served over http (Chrome blocks
    # file:// links from an http page). Falls back to file:// for far-away paths.
    rel = os.path.relpath(ap, HERE)
    if not rel.startswith(os.path.join("..", "..")):
        return rel
    return "file://" + ap


def h_rows(rows, cols):
    out = ["<table><tr>" + "".join("<th>%s</th>" % c for c in cols) + "</tr>"]
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</table>")
    return "".join(out)


def panel(title, body):
    return ('<section class="panel"><div class="phead"><span class="car">&#9660;</span>%s</div>'
            '<div class="pbody">%s</div></section>') % (html.escape(title), body)


def _brief(st):
    proj = str(st.get("project", "")).strip()
    parts = ["Good day. All systems are online."]
    if proj:
        parts.append("You are reviewing %s." % proj)
    f = str(st.get("focus", "")).strip()
    if f:
        parts.append("Current focus. " + f.split(". ")[0].strip(". ") + ".")
    pb = st.get("production_book", [])
    if pb:
        names = ", and ".join(x.get("name", "") for x in pb[:3])
        parts.append("The production book comprises %s." % names)
    na = st.get("next_action", [])
    if na:
        parts.append("If I may, your priority next action is, " + str(na[0]))
    parts.append("I shall be standing by.")
    return " ".join(p for p in parts if p)


JS = r"""
(function(){
  var boot=document.getElementById('boot');
  setTimeout(function(){if(boot)boot.classList.add('gone');},900);
  var t=document.getElementById('clk');
  function tick(){if(t)t.textContent=new Date().toLocaleTimeString([],{hour12:false});}
  setInterval(tick,1000);tick();
  document.querySelectorAll('.phead').forEach(function(h){
    h.addEventListener('click',function(){h.parentElement.classList.toggle('col');});});
  var q=document.getElementById('cmd');
  function applyFilter(){
    var v=(q.value||'').trim().toLowerCase();
    document.querySelectorAll('.panel').forEach(function(p){
      var any=false;
      p.querySelectorAll('tbody tr, .pbody li').forEach(function(row){
        var hit=!v||row.textContent.toLowerCase().indexOf(v)>=0;
        row.classList.toggle('hidden',!hit); if(hit)any=true;});
      if(v){p.classList.toggle('hidden',!any);} else {p.classList.remove('hidden');}
    });
  }
  if(q)q.addEventListener('input',applyFilter);

  /* ---- caption helpers (word-by-word) ---- */
  var cap=document.getElementById('cap');
  function buildCaption(text){
    cap.innerHTML=''; var spans=[],re=/\S+/g,m;
    while((m=re.exec(text))){
      var sp=document.createElement('span');
      sp.textContent=m[0]+' '; sp.dataset.s=m.index; sp.dataset.e=m.index+m[0].length;
      cap.appendChild(sp); spans.push(sp);
    }
    cap.classList.add('on'); return spans;
  }
  function lite(spans,idx){spans.forEach(function(s,i){s.classList.toggle('w',i===idx);});
    if(idx>=0&&spans[idx])spans[idx].scrollIntoView({block:'nearest',inline:'center'});}
  function clearCap(spans){spans.forEach(function(s){s.classList.remove('w');});
    setTimeout(function(){cap.classList.remove('on');},1400);}

  /* ---- browser-voice fallback (used only if cloud TTS unavailable) ---- */
  var VOICE=null;
  function pickVoice(){
    var v=(window.speechSynthesis&&speechSynthesis.getVoices())||[]; if(!v.length)return;
    var pref=[/google uk english male/i,/daniel/i,/google uk english/i,/(^|[^a-z])en[-_]GB/i,/samantha/i];
    for(var i=0;i<pref.length;i++){var m=v.find(function(x){return pref[i].test(x.name)||pref[i].test(x.lang);});if(m){VOICE=m;break;}}
    if(!VOICE)VOICE=v[0];
  }
  if('speechSynthesis' in window){pickVoice();speechSynthesis.onvoiceschanged=pickVoice;}
  function speakBrowser(text,spans){
    if(!('speechSynthesis' in window)){clearCap(spans);return;}
    speechSynthesis.cancel();
    var u=new SpeechSynthesisUtterance(text); if(VOICE)u.voice=VOICE; u.rate=0.9; u.pitch=0.8;
    u.onboundary=function(ev){if(ev.name&&ev.name!=='word')return;var ci=ev.charIndex||0,idx=-1;
      spans.forEach(function(sp,i){if(ci>=(+sp.dataset.s)&&ci<(+sp.dataset.e))idx=i;});lite(spans,idx);};
    u.onend=function(){clearCap(spans);busy(false);};
    speechSynthesis.speak(u);
  }

  /* ---- JARVIS voice: ElevenLabs cloud first (true human), browser fallback ---- */
  var bb=document.getElementById('brief');
  var curAudio=null, curSpans=null, speaking=false;
  function busy(b){speaking=b; if(bb)bb.textContent=b?'■ Stop':'▶ Brief me';}
  function stopBrief(){
    if(curAudio){try{curAudio.pause();curAudio.currentTime=0;}catch(e){} curAudio=null;}
    if('speechSynthesis' in window){try{speechSynthesis.cancel();}catch(e){}}
    if(curSpans)clearCap(curSpans);
    busy(false);
  }
  async function speakBrief(){
    if(speaking){stopBrief();return;}                 /* click again = stop */
    var text=((window.DASH&&window.DASH.brief)||'').trim(); if(!text||!cap)return;
    var spans=buildCaption(text); curSpans=spans; busy(true);
    try{
      var resp=await fetch('/tts',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({text:text})});
      var d=await resp.json();
      if(!resp.ok||!d.audio_base64){throw new Error((d&&d.error)||('tts '+resp.status));}
      if(!speaking)return;                            /* stopped while fetching */
      var au=new Audio('data:audio/mpeg;base64,'+d.audio_base64); curAudio=au;
      var starts=[],al=d.alignment;
      if(al&&al.character_start_times_seconds){var cs=al.character_start_times_seconds;
        starts=spans.map(function(sp){var i=+sp.dataset.s;return cs[Math.min(i,cs.length-1)]||0;});}
      au.onloadedmetadata=function(){if(!starts.length&&isFinite(au.duration)){var L=text.length;
        starts=spans.map(function(sp){return au.duration*(+sp.dataset.s)/L;});}};
      au.ontimeupdate=function(){var ct=au.currentTime,cur=-1;
        for(var i=0;i<starts.length;i++){if(starts[i]<=ct)cur=i;else break;}lite(spans,cur);};
      au.onended=function(){clearCap(spans);busy(false);curAudio=null;};
      au.onerror=function(){curAudio=null;busy(false);speakBrowser(text,spans);};
      await au.play();
    }catch(e){curAudio=null;busy(false);speakBrowser(text,spans);}
  }
  if(bb)bb.addEventListener('click',speakBrief);
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape')stopBrief();});

  /* ---- voice command -> filter ---- */
  var lb=document.getElementById('listen');
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(lb){
    if(!SR){lb.style.display='none';}
    else{var r=new SR();r.lang='en-GB';r.interimResults=false;
      lb.addEventListener('click',function(){try{r.start();lb.textContent='● LISTENING';}catch(e){}});
      r.onresult=function(ev){q.value=ev.results[0][0].transcript;applyFilter();};
      r.onerror=function(){lb.textContent='◉ Voice';};
      r.onend=function(){lb.textContent='◉ Voice';};}
  }

  /* ---- embedded terminal (token-guarded, localhost) ---- */
  var TOKEN=null, EXEC=false;
  var termout=document.getElementById('termout'), terminp=document.getElementById('terminp'),
      termcwd=document.getElementById('termcwd'), termnote=document.getElementById('termnote'),
      hist=[], hi=0;
  function termln(txt,cls){if(!termout)return;var d=document.createElement('div');if(cls)d.className=cls;
    d.textContent=txt;termout.appendChild(d);termout.scrollTop=termout.scrollHeight;}
  fetch('/token').then(function(r){return r.json();}).then(function(d){
    TOKEN=d.token; EXEC=d.exec;
    if(termnote)termnote.textContent=EXEC
      ? 'cwd-aware bash via the local server (token-guarded, localhost only).'
      : 'terminal disabled - relaunch the server with DASH_ENABLE_EXEC=1 to enable.';
    if(terminp&&!EXEC)terminp.disabled=true;
  }).catch(function(){if(termnote)termnote.textContent='server token unavailable.';});
  if(terminp)terminp.addEventListener('keydown',async function(ev){
    if(ev.key==='ArrowUp'){if(hist.length){hi=Math.max(0,hi-1);terminp.value=hist[hi]||'';}ev.preventDefault();return;}
    if(ev.key==='ArrowDown'){if(hist.length){hi=Math.min(hist.length,hi+1);terminp.value=hist[hi]||'';}ev.preventDefault();return;}
    if(ev.key!=='Enter')return;
    var cmd=terminp.value; if(!cmd.trim())return; terminp.value=''; hist.push(cmd); hi=hist.length;
    termln('$ '+cmd,'cmd');
    if(!EXEC){termln('[terminal disabled]','err');return;}
    try{
      var r=await fetch('/exec',{method:'POST',
        headers:{'Content-Type':'application/json','X-Token':TOKEN},
        body:JSON.stringify({cmd:cmd})});
      var d=await r.json();
      if(d.error){termln('['+d.error+'] '+(d.hint||''),'err');return;}
      if(d.out)termln(d.out.replace(/\s+$/,''), d.code?'err':null);
      if(d.cwd&&termcwd)termcwd.textContent=d.cwd.replace(/^\/Users\/[^/]+/,'~');
    }catch(e){termln('[network error] '+e,'err');}
  });
})();
"""


def render_html(st, commits, results):
    e = html.escape
    proj = e(st.get("project", "Project"))
    panels = []

    focus = st.get("focus", "")
    if focus:
        panels.append(panel("Mission focus", "<p>%s</p>" % e(focus)))

    feed = load_feed()
    fposts = feed.get("posts", []) if isinstance(feed, dict) else []

    dg = feed.get("digest") if isinstance(feed, dict) else None
    if dg:
        chips = " ".join('<span class="tag %s">%s: %d</span>'
                         % (_tagcls(k), e(k), v) for k, v in dg.get("by_tag", {}).items())
        hl = []
        for h in dg.get("highlights", []):
            link = ' <a href="%s">open</a>' % e(h.get("url", "")) if h.get("url") else ""
            hl.append('<li><span class="tag %s">%s</span> '
                      '<span class="sub">%s &middot; %s likes</span> &mdash; %s%s</li>'
                      % (_tagcls(h.get("tag", "")), e(h.get("tag", "")),
                         e(str(h.get("date", ""))[:16]), e(str(h.get("likes", 0))),
                         e(h.get("text", "")), link))
        dnote = ('<p class="sub">generated %s &middot; %d posts in last %dh</p>'
                 % (e(str(dg.get("generated", "?"))), dg.get("recent_count", 0),
                    dg.get("window_hours", 72)))
        panels.append(panel("What's new - digest",
                            dnote + "<p>" + chips + "</p><ul>" + "".join(hl) + "</ul>"))

    if fposts:
        N = 150
        items = []
        for p in fposts[:N]:
            txt = e((p.get("text") or "").replace("\n", " ").strip()[:220])
            meta = "%s &middot; %s likes" % (e(str(p.get("date", ""))[:16]), e(str(p.get("likes", 0))))
            ptag = ' <span class="tag %s">%s</span>' % (_tagcls(p.get("tag", "")), e(p["tag"])) if p.get("tag") else ""
            mtag = ' <span class="tag LIVE">%s</span>' % e(p["media"]) if p.get("media") else ""
            link = ' <a href="%s">open</a>' % e(p.get("url", "")) if p.get("url") else ""
            items.append('<li><span class="sub">%s</span>%s%s &mdash; %s%s</li>'
                         % (meta, ptag, mtag, txt, link))
        note = ('<p class="sub">showing %d of %d posts &middot; handles: %s &middot; '
                'updated %s &middot; full feed: social_rips/feed.json</p>'
                % (min(N, len(fposts)), feed.get("count", len(fposts)),
                   e(", ".join(feed.get("handles", []))), e(str(feed.get("updated", "?")))))
        panels.append(panel("AI News Feed (knowledge)", note + "<ul>" + "".join(items) + "</ul>"))

    bdata = load_bounties()
    bz = bdata.get("bounties", []) if isinstance(bdata, dict) else []
    if bz:
        M = 50
        rows = []
        for b in bz[:M]:
            usd = ("$%s" % b["usd"]) if b.get("usd") else "-"
            sc = b.get("score", 0)
            scls = "TESTED" if sc >= 55 else "REFINE" if sc >= 35 else "SCAFFOLD"
            rows.append([
                '<span class="tag %s">%.0f</span>' % (scls, sc),
                e(usd), e(str(b.get("lang", "?"))),
                '<a href="%s">%s</a>' % (e(b.get("url", "")), e(b.get("title", "")[:90])),
                e(b.get("repo", "")) + (" &#9733;%d" % b["stars"] if b.get("stars") else ""),
                e(str(b.get("comments", 0)))])
        bnote = ('<p class="sub">%d open bounties &middot; ranked by win-fit (stack/payout/clarity/'
                 'freshness) &middot; updated %s &middot; edit stack: social_rips/stack.txt</p>'
                 % (bdata.get("count", len(bz)), e(str(bdata.get("updated", "?")))))
        panels.append(panel("Bounties (winnable software tasks)",
                            bnote + h_rows(rows, ["Fit", "$", "Stack", "Task", "Repo", "Comts"])))

    lk = st.get("links", [])
    if lk:
        body = "<ul>" + "".join(
            '<li><a href="%s">%s</a> &mdash; %s</li>'
            % (e(_href(x.get("path", ""))), e(x.get("name", "")), e(x.get("note", "")))
            for x in lk) + "</ul>"
        panels.append(panel("Artifacts & links", body))

    pb = st.get("production_book", [])
    if pb:
        rows = [[e(x.get("name", "")), e(x.get("role", "")),
                 tag(x.get("status", "")), e(x.get("metric", ""))] for x in pb]
        panels.append(panel("Production book", h_rows(rows, ["Engine", "Role", "Status", "Metric"])))

    eng = st.get("engines", [])
    if eng:
        rows = [[e(x.get("id", "")), e(x.get("type", "")),
                 tag(x.get("verdict", "")), e(x.get("note", ""))] for x in eng]
        panels.append(panel("Engine ledger", h_rows(rows, ["Engine", "Type", "Verdict", "Note"])))

    cap = st.get("capabilities", {})
    if cap:
        panels.append(panel("Capabilities & skills (already built - do not rebuild)",
                            render_caps_html(cap, installed_skill_count())))

    term_body = ('<div id="termout" class="termout"></div>'
                 '<div class="termline"><span id="termcwd" class="termcwd">~</span>'
                 '<input id="terminp" class="terminp" autocomplete="off" spellcheck="false" '
                 'placeholder="run a command - Enter to execute, Up/Down for history"></div>'
                 '<p class="sub" id="termnote">initializing...</p>')
    panels.append(panel("Terminal", term_body))

    na = st.get("next_action", [])
    if na:
        panels.append(panel("Next action",
                            "<ul>" + "".join("<li>%s</li>" % e(x) for x in na) + "</ul>"))

    kn = st.get("key_numbers", [])
    if kn:
        panels.append(panel("Key numbers (do not re-derive)",
                            "<ul>" + "".join("<li>%s</li>" % e(x) for x in kn) + "</ul>"))

    oi = st.get("open_items", [])
    if oi:
        panels.append(panel("Open items",
                            "<ul>" + "".join("<li>%s</li>" % e(x) for x in oi) + "</ul>"))

    if results:
        rows = [["<code>%s</code>" % e(n), e(d)] for n, d in results]
        panels.append(panel("Validated-engine ledger (from memory)",
                            h_rows(rows, ["Result note", "Summary"])))

    if commits:
        rows = [["<code>%s</code>" % e(h), e(d), e(s)] for h, d, s in commits]
        panels.append(panel("Recent commits (mnq_trading)", h_rows(rows, ["Hash", "Date", "Subject"])))

    gen = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    head = ("<!doctype html><html><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>%s</style></head><body>" % (proj, CSS))
    boot = '<div id="boot">INITIALIZING J.A.R.V.I.S.</div><div class="scan"></div>'
    hud = (
        '<div class="wrap">'
        '<div class="hud"><div class="reactor"></div>'
        '<div class="htitle"><h1>%s</h1>'
        '<p class="sub">Updated %s &middot; generated %s</p></div>'
        '<div class="clock"><div class="t" id="clk">--:--:--</div>'
        '<div class="st"><span class="led"></span>SYSTEM ONLINE</div></div></div>'
        '<div class="cmdbar">'
        '<input id="cmd" placeholder="⌖ filter everything — type to search panels...">'
        '<button class="btn" id="brief">▶ Brief me</button>'
        '<button class="btn" id="listen">◉ Voice</button></div>'
        % (proj, e(str(st.get("updated", "?"))), gen))
    foot = ('<p class="foot">JARVIS HUD &middot; static + deterministic. Regenerate: '
            '<code>/usr/local/bin/python3 ~/mnq_trading/diagnostics/build_dashboard.py</code></p>'
            '</div>')
    data = '<script>window.DASH=%s;</script>' % json.dumps({"brief": _brief(st)})
    cap = '<div id="cap"></div>'
    return (head + boot + hud + "".join(panels) + foot + cap + data
            + "<script>%s</script>" % JS + "</body></html>")


# ---------- Markdown rendering (Obsidian / mobile) ----------

def render_md(st, commits, results):
    L = []
    L.append("# %s" % st.get("project", "Project"))
    L.append("> Updated %s &middot; generated %s &middot; auto-generated, do not hand-edit"
             % (st.get("updated", "?"),
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    L.append("")
    L.append(st.get("focus", ""))

    lk = st.get("links", [])
    if lk:
        L += ["", "## Artifacts & links", ""]
        for x in lk:
            L.append("- [%s](%s) - %s" % (x.get("name", ""), _href(x.get("path", "")),
                                          x.get("note", "")))

    pb = st.get("production_book", [])
    if pb:
        L += ["", "## Production book", "", "| Engine | Role | Status | Metric |",
              "|---|---|---|---|"]
        for x in pb:
            L.append("| %s | %s | **%s** | %s |" % (x.get("name", ""), x.get("role", ""),
                                                    x.get("status", ""), x.get("metric", "")))

    eng = st.get("engines", [])
    if eng:
        L += ["", "## Engine ledger", "", "| Engine | Type | Verdict | Note |",
              "|---|---|---|---|"]
        for x in eng:
            L.append("| %s | %s | **%s** | %s |" % (x.get("id", ""), x.get("type", ""),
                                                    x.get("verdict", ""), x.get("note", "")))

    for title, key in [("Next action", "next_action"),
                       ("Key numbers (do not re-derive)", "key_numbers"),
                       ("Open items", "open_items")]:
        vals = st.get(key, [])
        if vals:
            L += ["", "## %s" % title, ""]
            L += ["- %s" % v for v in vals]

    cap = st.get("capabilities", {})
    if cap:
        L += render_caps_md(cap, installed_skill_count())

    if results:
        L += ["", "## Validated-engine ledger (from memory)", ""]
        for n, d in results:
            L.append("- **%s** - %s" % (n, d))

    if commits:
        L += ["", "## Recent commits (mnq_trading)", "", "| Hash | Date | Subject |",
              "|---|---|---|"]
        for h, d, s in commits:
            L.append("| `%s` | %s | %s |" % (h, d, s.replace("|", "\\|")))

    L += ["", "---", "_Regenerate: `python3 ~/mnq_trading/diagnostics/build_dashboard.py`_"]
    return "\n".join(L) + "\n"


def installed_skill_count():
    try:
        return sum(1 for d in os.listdir(SKILLS_DIR)
                   if os.path.isdir(os.path.join(SKILLS_DIR, d)))
    except Exception:
        return 0


def render_caps_html(cap, n_installed):
    e = html.escape
    out = []
    bt = cap.get("built_tools", [])
    if bt:
        out.append("<h3>Built tools</h3>")
        rows = [[e(x.get("name", "")), e(x.get("what", "")),
                 "<code>%s</code>" % e(x.get("run", "")), tag(x.get("status", ""))]
                for x in bt]
        out.append(h_rows(rows, ["Tool", "What", "Run", "Status"]))
    cs = cap.get("custom_skills", [])
    if cs:
        out.append("<h3>Custom skills</h3>")
        rows = [[e(x.get("name", "")), e(x.get("what", ""))] for x in cs]
        out.append(h_rows(rows, ["Skill", "What"]))
    oi = cap.get("outsourced_index", [])
    if oi:
        out.append("<h3>Outsourced skills index (%d in ~/.claude/skills)</h3>" % n_installed)
        out.append("<ul>" + "".join("<li>%s</li>" % e(s) for s in oi) + "</ul>")
    return "".join(out)


def render_caps_md(cap, n_installed):
    L = ["", "## Capabilities & skills (already built - do not rebuild)"]
    bt = cap.get("built_tools", [])
    if bt:
        L += ["", "### Built tools", "", "| Tool | What | Run | Status |", "|---|---|---|---|"]
        for x in bt:
            L.append("| %s | %s | `%s` | **%s** |" % (
                x.get("name", ""), x.get("what", ""),
                x.get("run", "").replace("|", "\\|"), x.get("status", "")))
    cs = cap.get("custom_skills", [])
    if cs:
        L += ["", "### Custom skills", ""]
        L += ["- **%s** - %s" % (x.get("name", ""), x.get("what", "")) for x in cs]
    oi = cap.get("outsourced_index", [])
    if oi:
        L += ["", "### Outsourced skills index (%d in ~/.claude/skills)" % n_installed, ""]
        L += ["- %s" % s for s in oi]
    return L


def render_caps_registry(cap, n_installed):
    """The auto-loaded memory file: capabilities.md (frontmatter + concise registry)."""
    L = [
        "---",
        "name: capabilities",
        'description: "Registry of BUILT + TESTED tools and CUSTOM skills already created in '
        "this environment. Read at session start; do NOT re-derive or rebuild anything listed "
        'here - run it. Auto-generated by build_dashboard.py from project_state.yaml."',
        "metadata:",
        "  type: reference",
        "---",
        "",
        "# Capabilities registry (auto-generated; do not hand-edit)",
        "> Single source: `~/mnq_trading/diagnostics/project_state.yaml` -> "
        "regenerate with `python3 ~/mnq_trading/diagnostics/build_dashboard.py`.",
        "> RULE: if something is listed TESTED/LIVE here, it EXISTS and works - USE it, never rebuild it.",
    ]
    L += render_caps_md(cap, n_installed)
    L += ["", "_Auto-generated %s._" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M")]
    return "\n".join(L) + "\n"


def main():
    st = load_state()
    commits = git_log(15)
    results = result_engines()
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(render_html(st, commits, results))
    wrote = [OUT_HTML]
    try:
        if os.path.isdir(VAULT):
            with open(OUT_MD, "w", encoding="utf-8") as f:
                f.write(render_md(st, commits, results))
            wrote.append(OUT_MD)
    except Exception as exc:
        print("WARN: vault write skipped: %s" % exc)
    try:
        with open(CAP_MD, "w", encoding="utf-8") as f:
            f.write(render_caps_registry(st.get("capabilities", {}), installed_skill_count()))
        wrote.append(CAP_MD)
    except Exception as exc:
        print("WARN: capabilities.md write skipped: %s" % exc)
    print("dashboard: %d commits, %d validated-engine notes" % (len(commits), len(results)))
    for w in wrote:
        print("  wrote " + w)


if __name__ == "__main__":
    main()
