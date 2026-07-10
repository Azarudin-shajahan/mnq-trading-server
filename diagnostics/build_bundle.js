const fs=require('fs');
const base='education/mentors';
const ids=['ttrades','daye','dayement','gxt','ict','dexter','xyj'];
const guides=ids.map(id=>{ const src=fs.readFileSync(`${base}/data/${id}.js`,'utf8'); const window={}; new Function('window',src)(window); return window.GUIDE; });
const css=fs.readFileSync(`${base}/guide.css`,'utf8');
const modelsJs=fs.readFileSync('education/models.js','utf8');
// sessions data from the main dashboard (window.EDU.sessions)
const dataSrc=fs.readFileSync('education/data.js','utf8');
const w2={}; new Function('window',dataSrc)(w2);
const sessions=w2.EDU.sessions;
const html=`<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#ffffff">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-192.png">
<title>Mentor Deep-Guides</title>
<style>
${css}
.tabbar{position:sticky;top:0;z-index:5;background:var(--bg);display:flex;flex-wrap:wrap;gap:8px;padding:12px 16px;border-bottom:1px solid var(--line)}
.tabbar button{font:inherit;cursor:pointer;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:999px;padding:8px 14px}
.tabbar button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
section.gsec h2{scroll-margin-top:64px}
.bhead{max-width:1100px;margin:0 auto;padding:16px 20px 0}
.bhead h1{margin:0;font-size:18px}
.bhead p{margin:4px 0 0;color:var(--muted);font-size:13px}
.vchip{font-size:11px;font-weight:700;border-radius:4px;padding:2px 7px;white-space:nowrap}
.mp-row{border:1px solid #e0e0e0;border-radius:8px;padding:12px 14px;margin:8px 0}
.mp-row .lab{font-weight:700}
.mp-row .fld{font-size:13px;margin:5px 0;line-height:1.4}
.ses{border:1px solid #e0e0e0;border-radius:8px;margin:10px 0;overflow:hidden}
.ses .shead{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:12px 14px;cursor:pointer;background:#fafafa}
.ses .sbody{display:none;padding:0 14px 12px}
.ses.open .sbody{display:block}
.ses table{width:100%;border-collapse:collapse;font-size:13px}
.ses th,.ses td{text-align:left;padding:6px 8px;border-bottom:1px solid #eee}
.ses .star{color:#f9a825}
</style>
</head>
<body>
<div class="bhead"><h1>Mentor Deep-Guides</h1><p>Offline copy · sourced from NotebookLM · tap a mentor</p></div>
<div class="tabbar" id="tabs"><button data-v="sessions" id="sesTab">Session Playbook</button><button data-v="models" id="modelTab">Model Playbook</button></div>
<div id="guide"></div>
<section class="view" id="sessions" style="display:none;max-width:1100px;margin:0 auto;padding:16px 20px">
  <h2>Session Playbook — the day, hour by hour</h2>
  <p>What each mentor trades, when. Verdict colors tell you where to focus. Tap a session to expand; the ★ killzones (NY AM / NY PM) are where the proven edge lives.</p>
  <div id="seslist"></div>
</section>
<section class="view" id="models" style="display:none;max-width:1100px;margin:0 auto;padding:16px 20px">
  <h2>Model Playbook</h2>
  <p>Every model the seven mentors teach — 33 in total — with its full tradable spec. Grouped by mentor. Search by model / trigger / tool.</p>
  <div class="banner" style="background:#fff8e1;border-left:4px solid #f9a825;padding:10px 14px;margin:12px 0;font-size:13px">Verdicts grade OUR backtest <b>evidence</b>, not the mentors' claims. FORWARD-VALIDATED is deliberately empty — nothing here is proven live/OOS. <b>IN-SAMPLE</b> (only 2 models) = our in-sample edge (the v8.18 62T — never size up on it); <b>UNVALIDATED</b> = taught but not gated here; <b>DEAD</b> = net-negative in our engine. A learning catalog, not a signal source.</div>
  <input id="modelSearch" style="width:100%;box-sizing:border-box;padding:8px 12px;font-size:14px;border:1px solid #ccc;border-radius:6px;margin-bottom:12px" placeholder="Search model / trigger / tool…">
  <div id="modelGroups"></div>
</section>
<script>${modelsJs}</script>
<script>
var GUIDES=${JSON.stringify(guides)};
var SESSIONS=${JSON.stringify(sessions)};
var VLABEL={s:'IN-SAMPLE',a:'UNVALIDATED',r:'DEAD',g:'FORWARD-VALIDATED',w:'MECHANIC'};
var VCOL={s:'#1558b0',a:'#f57c00',r:'#c62828',g:'#2e7d32',w:'#6a1b9a'};
function vchip(code){var l=VLABEL[code]||code,c=VCOL[code]||'#666';return '<span class="vchip" style="color:'+c+';border:1px solid '+c+'">'+l+'</span>';}
var host=document.getElementById('guide'), tabs=document.getElementById('tabs');
function esc(s){return String(s==null?'':s).replace(/[&<>]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
function render(g){
  var toc=g.sections.map(function(s){return '<a href="#'+s.id+'">'+esc(s.title)+'</a>';}).join('');
  var secs=g.sections.map(function(s){return '<section class="gsec"><h2 id="'+s.id+'">'+esc(s.title)+'</h2>'+(s.html||'<p class="nc">Not covered in this mentor\\'s corpus.</p>')+'</section>';}).join('');
  host.innerHTML='<div class="ghead"><h1>'+esc(g.name)+'</h1><div class="tag">'+esc(g.tagline||'')+'</div></div><nav class="toc">'+toc+'</nav><main class="body">'+secs+'</main>';
  window.scrollTo(0,0);
}
var sesSec=document.getElementById('sessions'), modSec=document.getElementById('models');
// Mentor guide tabs — prepend before the static Session/Model buttons
GUIDES.forEach(function(g,i){var b=document.createElement('button');b.textContent=g.name;b.onclick=function(){select(i);};tabs.insertBefore(b,tabs.firstChild);});
function clearOn(){for(var j=0;j<tabs.children.length;j++)tabs.children[j].classList.remove('on');}
document.getElementById('sesTab').onclick=function(){clearOn();this.classList.add('on');host.innerHTML='';modSec.style.display='none';sesSec.style.display='block';window.scrollTo(0,0);renderSessions();};
document.getElementById('modelTab').onclick=function(){clearOn();this.classList.add('on');host.innerHTML='';sesSec.style.display='none';modSec.style.display='block';window.scrollTo(0,0);if(window.MODELS&&!document.getElementById('modelGroups').hasChildNodes())renderModelPlaybook();};
function select(i){sesSec.style.display='none';modSec.style.display='none';var kids=tabs.children;for(var j=0;j<kids.length;j++)kids[j].classList.toggle('on',j===i);render(GUIDES[i]);}
function renderSessions(){
  document.getElementById('seslist').innerHTML=SESSIONS.map(function(s){
    var rows=s.rows.map(function(r){return '<tr><td>'+esc(r[0])+'</td><td style="color:#888">'+esc(r[1])+'</td><td>'+vchip(r[2])+'</td></tr>';}).join('');
    return '<div class="ses'+(s.star?' open':'')+'"><div class="shead" onclick="this.parentNode.classList.toggle(\\'open\\')">'
      +'<div><b'+(s.star?' class="star"':'')+'>'+(s.star?'★ ':'')+esc(s.name)+'</b> <span style="color:#888;font-size:12px">'+esc(s.time)+'</span></div>'
      +'<div style="color:#888;font-size:12px">'+s.rows.length+' setups ›</div></div>'
      +'<div class="sbody"><table><tr><th>Setup</th><th>Mentor</th><th>Verdict</th></tr>'+rows+'</table></div></div>';
  }).join('');
}
function renderModelPlaybook(){
  var groups={};
  (window.MODELS||[]).forEach(function(m){if(!groups[m.mentor])groups[m.mentor]=[];groups[m.mentor].push(m);});
  function fld(lab,v){return v?'<div class="fld"><span class="lab">'+lab+':</span> '+esc(v)+'</div>':'';}
  document.getElementById('modelGroups').innerHTML=Object.keys(groups).map(function(mentor){
    var rows=groups[mentor].map(function(m){
      var tools=(m.tools&&m.tools.length)?m.tools.join(' · '):'';
      return '<div class="mp-row">'
        +'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px"><b style="font-size:14px">'+esc(m.name)+'</b>'+vchip(m.verdict)+'</div>'
        +(m.session?'<div style="font-size:12px;color:#1558b0;font-weight:600;margin:4px 0">'+esc(m.session)+'</div>':'')
        +fld('HTF context',m.htf)+fld('Trigger',m.trigger)+fld('Entry',m.entry)+fld('Stop',m.stop)+fld('Target',m.target)+fld('Timeframes',m.tfs)+fld('Tools',tools)+fld('Example',m.example)
        +'</div>';
    }).join('');
    return '<details open style="margin:16px 0"><summary style="font-size:16px;font-weight:700;cursor:pointer;padding:6px 0">'+esc(mentor)+' ('+groups[mentor].length+')</summary>'+rows+'</details>';
  }).join('');
}
document.getElementById('modelSearch').addEventListener('input',function(){
  var q=this.value.toLowerCase();
  document.querySelectorAll('#modelGroups .mp-row').forEach(function(c){c.style.display=c.textContent.toLowerCase().includes(q)?'':'none';});
});
select(0);
</script>
<script>if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js');});}</script>
</body>
</html>`;
fs.writeFileSync('education/mentor-guides.html',html);
console.log('wrote education/mentor-guides.html  size='+html.length+' bytes  mentors='+guides.map(g=>g.name).join(',')+'  sessions='+sessions.length);
