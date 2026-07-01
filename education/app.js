/* The Framework — render + interaction. Reads window.EDU (data.js). Vanilla JS, no deps. */
(function(){
const E = window.EDU;
const V = E.verdicts;
const chip = v => '<span class="chip '+v+'">'+V[v]+'</span>';
const $ = s => document.querySelector(s);

/* ---------------- The Frame ---------------- */
const pipe = $('#pipe');
E.frame.forEach((s,i)=>{
  const d=document.createElement('div'); d.className='stage'; d.dataset.i=i;
  d.innerHTML='<div class="n">STEP '+s.n+'</div><div class="t">'+s.t+'</div>'+chip(s.verdict[0])+
    (i<E.frame.length-1?'<div class="arrow">›</div>':'');
  d.onclick=()=>showStage(i); pipe.appendChild(d);
});
function showStage(i){
  document.querySelectorAll('.stage').forEach(e=>e.classList.toggle('sel',+e.dataset.i===i));
  const s=E.frame[i], det=$('#stageDetail'); det.classList.add('on');
  det.innerHTML='<h3>Step '+s.n+' — '+s.t+' '+chip(s.verdict[0])+'</h3>'+
    row('What it means', s.meaning)+
    row('Concepts used', s.concepts.map(c=>'<span class="tag">'+c+'</span>').join(''))+
    row('Each mentor', s.mentors.map(m=>'<div class="mentorline"><b>'+m[0]+'</b> — '+m[1]+'</div>').join(''))+
    row('Our verdict', s.verdict[1]);
}
function row(k,v){return '<div class="row"><div class="k">'+k+'</div><div class="v">'+v+'</div></div>';}
showStage(0);

/* ---------------- Concept Library ---------------- */
function conceptCard(c){
  return '<div class="card" onclick="this.classList.toggle(\'open\')"><h4>'+c.t+' '+chip(c.v)+'</h4><p>'+c.d+'</p>'+
    '<div class="more">'+
      '<div><span class="lab">How to spot</span>'+c.spot+'</div>'+
      '<div><span class="lab">Bull vs bear</span>'+c.bb+'</div>'+
      '<div><span class="lab">In the frame</span>'+c.step+'</div>'+
    '</div></div>';
}
$('#pdgrid').innerHTML=E.pd_arrays.map(conceptCard).join('');
$('#mechgrid').innerHTML=E.mechanics.map(conceptCard).join('');
$('#timinggrid').innerHTML=(E.timing||[]).map(conceptCard).join('');
$('#modelsgrid').innerHTML=(E.models||[]).map(conceptCard).join('');

/* concept search — filters every card across all groups by title + body text */
const csearch=$('#conceptSearch');
if(csearch){
  csearch.addEventListener('input',()=>{
    const q=csearch.value.trim().toLowerCase();
    let any=false;
    document.querySelectorAll('#concepts .card').forEach(c=>{
      const hit = !q || c.textContent.toLowerCase().indexOf(q)>-1;
      c.classList.toggle('hide',!hit); if(hit) any=true;
    });
    // hide a group's sublabel when it has no visible cards
    document.querySelectorAll('#concepts .sublabel').forEach(lbl=>{
      let g=lbl.nextElementSibling;
      const vis=g && g.querySelectorAll('.card:not(.hide)').length>0;
      lbl.classList.toggle('hide',!!q && !vis);
    });
    $('#searchEmpty').style.display=(q && !any)?'block':'none';
  });
}

/* ---------------- Mentor Lenses ---------------- */
const mg=$('#mgrid');
E.mentors.forEach((m,i)=>{
  const c=document.createElement('div'); c.className='mcard'; c.dataset.i=i;
  c.innerHTML='<div class="owns">'+m.owns+'</div><h4>'+m.name+'</h4><p>'+m.ses+'</p>';
  c.onclick=()=>showMentor(i); mg.appendChild(c);
});
function showMentor(i){
  document.querySelectorAll('.mcard').forEach(e=>e.classList.toggle('sel',+e.dataset.i===i));
  const m=E.mentors[i], p=$('#mPanel'); p.classList.add('on');
  p.innerHTML='<h3>'+m.name+' <span class="owns" style="font-size:12px;color:var(--accent)">'+m.owns+'</span></h3>'+
    row('Philosophy', m.phil)+
    row('Sessions', m.ses)+
    row('Signature setups', m.setups.map(s=>'<span class="tag">'+s[0]+' '+chip(s[1])+'</span>').join(''))+
    row('Maps to frame', m.vocab);
}
showMentor(0);

/* ---------------- Session Playbook ---------------- */
$('#seslist').innerHTML=E.sessions.map(s=>
  '<div class="ses"><div class="head" onclick="this.parentNode.classList.toggle(\'open\')">'+
    '<div><b'+(s.star?' class="star"':'')+'>'+(s.star?'★ ':'')+s.name+'</b> <span class="time">'+s.time+'</span></div>'+
    '<div class="time">'+s.rows.length+' setups ›</div></div>'+
  '<div class="body"><table><tr><th>Setup</th><th>Mentor</th><th>Verdict</th></tr>'+
    s.rows.map(r=>'<tr><td>'+r[0]+'</td><td style="color:var(--dim)">'+r[1]+'</td><td>'+chip(r[2])+'</td></tr>').join('')+
  '</table></div></div>').join('');
document.querySelectorAll('.ses').forEach(el=>{ if(el.querySelector('.star')) el.classList.add('open'); });

/* ---------------- Self-Check (quiz + localStorage progress) ---------------- */
const PKEY='edu_progress_v1';
function loadP(){ try{return JSON.parse(localStorage.getItem(PKEY))||{}}catch(e){return {}} }
function saveP(p){ try{localStorage.setItem(PKEY,JSON.stringify(p))}catch(e){} }
let prog=loadP();
const qwrap=$('#quizzes');
qwrap.innerHTML=E.quiz.map((q,i)=>
  '<div class="quiz'+(prog['q'+i]?' got':'')+'" id="q'+i+'"><div class="qtype">'+q.type+'</div><div class="qq">'+q.q+'</div>'+
  '<div class="btns"><button data-rev="'+i+'">Reveal answer</button>'+
  '<button data-got="'+i+'">'+(prog['q'+i]?'✓ Got it':'Mark as understood')+'</button></div>'+
  '<div class="ans">'+q.a+'</div></div>').join('');
qwrap.addEventListener('click',e=>{
  const r=e.target.dataset.rev, g=e.target.dataset.got;
  if(r!==undefined){ $('#q'+r).classList.add('reveal'); }
  if(g!==undefined){ prog['q'+g]=true; saveP(prog); $('#q'+g).classList.add('got'); e.target.textContent='✓ Got it'; updateProgress(); }
});
function updateProgress(){
  const total=E.quiz.length, done=E.quiz.filter((q,i)=>prog['q'+i]).length;
  $('#pcount').textContent=done+' / '+total+' checks understood';
  $('#pbar').style.width=(total?Math.round(done/total*100):0)+'%';
  const gaps=E.quiz.filter((q,i)=>!prog['q'+i]).map(q=>q.type);
  $('#pgaps').innerHTML = done===total
    ? 'All checks passed — <span class="chip g">on track</span>'
    : 'Still open: '+[...new Set(gaps)].join(' · ')+' <span class="chip a">review these</span>';
}
updateProgress();

/* ---------------- Read It Live (interactive walk-through) ---------------- */
let state={}, step=0, trail=[];
function renderWalk(){
  const host=$('#walkHost');
  const dots=E.walk.map((s,i)=>'<div class="dot '+(i<step?'done':i===step?'on':'')+'">'+(i+1)+'</div>').join('');
  const trailHtml = trail.length ? '<div class="trail">'+trail.map(t=>'<b>'+t.k+':</b> '+t.v).join(' &nbsp;→&nbsp; ')+'</div>' : '';
  if(step>=E.walk.length){ // all passed
    const r=E.walkResult;
    const smtline = state.smt ? 'SMT confirms — highest conviction.' : 'No SMT — still valid, slightly lower conviction.';
    const lines=r.lines.map(l=>l.replace('{dir}',state.dir).replace('{ses}',state.ses).replace('{smtline}',smtline)).filter(x=>x.trim());
    host.innerHTML='<div class="steps">'+dots+'</div>'+trailHtml+
      '<div class="result s"><h3>'+chip('s')+' '+r.title+'</h3><ul>'+lines.map(l=>'<li>'+l+'</li>').join('')+'</ul>'+
      '<p class="demo">Framing illustration only — this is NOT a signal, is not sized, and does not clear you to trade. It means the pattern matches our in-sample edge; only a forward/live demo validates it.</p>'+
      '<div class="again"><button class="btn" id="wtRestart">Frame another</button></div></div>';
    $('#wtRestart').onclick=resetWalk; return;
  }
  const s=E.walk[step];
  host.innerHTML='<div class="steps">'+dots+'</div>'+trailHtml+
    '<div class="card2"><p class="q">'+s.q+'</p><p class="help">'+s.help+'</p>'+
    s.opts.map((o,i)=>'<button class="opt" data-i="'+i+'">'+o.label+'</button>').join('')+'</div>';
  host.querySelectorAll('.opt').forEach(b=>b.onclick=()=>choose(+b.dataset.i));
}
function choose(i){
  const s=E.walk[step], o=s.opts[i];
  trail.push({k:s.q.split('—')[0].trim(), v:o.label});
  if(o.stop){ showStop(o.stop); return; }
  if(o.set) Object.assign(state,o.set);
  step++; renderWalk();
}
function showStop(stop){
  const host=$('#walkHost');
  const dots=E.walk.map((s,i)=>'<div class="dot '+(i<=step?'done':'')+'">'+(i+1)+'</div>').join('');
  const trailHtml='<div class="trail">'+trail.map(t=>'<b>'+t.k+':</b> '+t.v).join(' &nbsp;→&nbsp; ')+'</div>';
  host.innerHTML='<div class="steps">'+dots+'</div>'+trailHtml+
    '<div class="result '+stop.v+'"><h3>'+chip(stop.v)+' '+stop.title+'</h3><p>'+stop.body+'</p>'+
    '<div class="again"><button class="btn" id="wtRestart">Start over</button></div></div>';
  $('#wtRestart').onclick=resetWalk;
}
function resetWalk(){ state={}; step=0; trail=[]; renderWalk(); }
resetWalk();
$('#gotoWalk') && ($('#gotoWalk').onclick=()=>switchView('live'));

/* ---------------- nav ---------------- */
function switchView(v){
  document.querySelectorAll('#nav button').forEach(x=>x.classList.toggle('on',x.dataset.v===v));
  document.querySelectorAll('.view').forEach(el=>el.classList.toggle('on',el.id===v));
  window.scrollTo({top:0,behavior:'smooth'});
}
document.querySelectorAll('#nav button').forEach(b=>b.onclick=()=>switchView(b.dataset.v));
})();
