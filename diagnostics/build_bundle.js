const fs=require('fs');
const base='education/mentors';
const ids=['ttrades','daye','dayement','gxt','ict','dexter','xyj'];
const guides=ids.map(id=>{ const src=fs.readFileSync(`${base}/data/${id}.js`,'utf8'); const window={}; new Function('window',src)(window); return window.GUIDE; });
const css=fs.readFileSync(`${base}/guide.css`,'utf8');
const modelsJs=fs.readFileSync('education/models.js','utf8');
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
</style>
</head>
<body>
<div class="bhead"><h1>Mentor Deep-Guides</h1><p>Offline copy · sourced from NotebookLM · tap a mentor</p></div>
<div class="tabbar" id="tabs"><button data-v="models" id="modelTab">Model Playbook</button></div>
<div id="guide"></div>
<section class="view" id="models" style="display:none;max-width:1100px;margin:0 auto;padding:16px 20px">
  <h2>Model Playbook</h2>
  <p>Every model the seven mentors teach — 33 in total — with its full tradable spec. Grouped by mentor. Filter by session or by our backtest verdict.</p>
  <div class="banner" style="background:#fff8e1;border-left:4px solid #f9a825;padding:10px 14px;margin:12px 0;font-size:13px">Verdicts grade OUR backtest <b>evidence</b>, not the mentors' claims. FORWARD-VALIDATED is deliberately empty — nothing here is proven live/OOS. <b>IN-SAMPLE</b> (only 2 models) = our in-sample edge (the v8.18 62T — never size up on it); <b>UNVALIDATED</b> = taught but not gated here; <b>DEAD</b> = net-negative in our engine. A learning catalog, not a signal source.</div>
  <div id="modelFilters" class="filters" style="display:flex;flex-wrap:wrap;gap:6px;margin:12px 0"></div>
  <input id="modelSearch" style="width:100%;box-sizing:border-box;padding:8px 12px;font-size:14px;border:1px solid #ccc;border-radius:6px;margin-bottom:12px" placeholder="Search model / trigger / tool…">
  <div id="modelGroups"></div>
</section>
<script>${modelsJs}</script>
<script>
var GUIDES=${JSON.stringify(guides)};
var host=document.getElementById('guide'), tabs=document.getElementById('tabs');
function esc(s){return String(s).replace(/[&<>]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
function render(g){
  var toc=g.sections.map(function(s){return '<a href="#'+s.id+'">'+esc(s.title)+'</a>';}).join('');
  var secs=g.sections.map(function(s){return '<section class="gsec"><h2 id="'+s.id+'">'+esc(s.title)+'</h2>'+(s.html||'<p class="nc">Not covered in this mentor\\'s corpus.</p>')+'</section>';}).join('');
  host.innerHTML='<div class="ghead"><h1>'+esc(g.name)+'</h1><div class="tag">'+esc(g.tagline||'')+'</div></div><nav class="toc">'+toc+'</nav><main class="body">'+secs+'</main>';
  window.scrollTo(0,0);
}
// Mentor guide tabs — prepend before the static Model Playbook button
GUIDES.forEach(function(g,i){var b=document.createElement('button');b.textContent=g.name;b.onclick=function(){select(i);};tabs.insertBefore(b,tabs.firstChild);});
// Wire the static Model Playbook button
var modelTabBtn=document.getElementById('modelTab');
modelTabBtn.onclick=function(){selectModels(modelTabBtn);};
var modSec=document.getElementById('models');
function selectModels(btn){
  var kids=tabs.children;
  for(var j=0;j<kids.length;j++){kids[j].classList.remove('on');}
  btn.classList.add('on');
  host.innerHTML='';
  modSec.style.display='block';
  window.scrollTo(0,0);
  if(window.MODELS && !document.getElementById('modelGroups').hasChildNodes()){
    renderModelPlaybook();
  }
}
function select(i){
  modSec.style.display='none';
  var kids=tabs.children;
  for(var j=0;j<kids.length;j++){kids[j].classList.toggle('on',j===i);}
  render(GUIDES[i]);
}
function renderModelPlaybook(){
  var groups={};
  (window.MODELS||[]).forEach(function(m){
    if(!groups[m.mentor])groups[m.mentor]=[];
    groups[m.mentor].push(m);
  });
  var verdictColor={'IN-SAMPLE':'#1558b0','FORWARD-VALIDATED':'#2e7d32','UNVALIDATED':'#f57c00','DEAD':'#c62828'};
  var gc=document.getElementById('modelGroups');
  gc.innerHTML=Object.keys(groups).map(function(mentor){
    var rows=groups[mentor].map(function(m){
      var vc=verdictColor[m.verdict]||'#666';
      return '<div style="border:1px solid #e0e0e0;border-radius:8px;padding:12px 14px;margin:8px 0">'
        +'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">'
        +'<b style="font-size:14px">'+esc(m.name)+'</b>'
        +'<span style="font-size:11px;font-weight:700;color:'+vc+';border:1px solid '+vc+';border-radius:4px;padding:2px 7px">'+esc(m.verdict)+'</span>'
        +'</div>'
        +(m.session?'<div style="font-size:12px;color:#888;margin:4px 0">'+esc(m.session)+'</div>':'')
        +(m.trigger?'<div style="font-size:13px;margin:6px 0"><b>Trigger:</b> '+esc(m.trigger)+'</div>':'')
        +(m.tool?'<div style="font-size:13px;margin:4px 0"><b>Tool:</b> '+esc(m.tool)+'</div>':'')
        +(m.description?'<div style="font-size:13px;color:#444;margin-top:6px">'+esc(m.description)+'</div>':'')
        +'</div>';
    }).join('');
    return '<details open style="margin:16px 0"><summary style="font-size:16px;font-weight:700;cursor:pointer;padding:6px 0">'+esc(mentor)+'</summary>'+rows+'</details>';
  }).join('');
}
// Wire search + filter for model playbook
document.getElementById('modelSearch').addEventListener('input',function(){
  var q=this.value.toLowerCase();
  var cards=document.querySelectorAll('#modelGroups [style*="border:1px solid #e0e0e0"]');
  cards.forEach(function(c){c.style.display=c.textContent.toLowerCase().includes(q)?'':'none';});
});
select(0);
</script>
<script>if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js');});}</script>
</body>
</html>`;
fs.writeFileSync('education/mentor-guides.html',html);
console.log('wrote education/mentor-guides.html  size='+html.length+' bytes  mentors='+guides.map(g=>g.name).join(','));
