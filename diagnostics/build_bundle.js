const fs=require('fs');
const base='education/mentors';
const ids=['ttrades','daye','dayement','gxt','ict','dexter','xyj'];
const guides=ids.map(id=>{ const src=fs.readFileSync(`${base}/data/${id}.js`,'utf8'); const window={}; new Function('window',src)(window); return window.GUIDE; });
const css=fs.readFileSync(`${base}/guide.css`,'utf8');
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
<div class="tabbar" id="tabs"></div>
<div id="guide"></div>
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
GUIDES.forEach(function(g,i){var b=document.createElement('button');b.textContent=g.name;b.onclick=function(){select(i);};tabs.appendChild(b);});
function select(i){var kids=tabs.children;for(var j=0;j<kids.length;j++){kids[j].classList.toggle('on',j===i);}render(GUIDES[i]);}
select(0);
</script>
<script>if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js');});}</script>
</body>
</html>`;
fs.writeFileSync('education/mentor-guides.html',html);
console.log('wrote education/mentor-guides.html  size='+html.length+' bytes  mentors='+guides.map(g=>g.name).join(','));
