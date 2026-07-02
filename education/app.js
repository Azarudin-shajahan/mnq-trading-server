/* The Framework — render + interaction. Reads window.EDU (data.js). Vanilla JS, no deps. */
(function(){
const E = window.EDU;
const V = E.verdicts;
const chip = v => '<span class="chip '+v+'">'+V[v]+'</span>';
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
const MCLS = {ttrades:'m-tt',daye:'m-daye',gxt:'m-gxt',ict:'m-ict',dexter:'m-dx',all:'m-all'};
const mcls = name => MCLS[name.toLowerCase().replace(/[^a-z]/g,'')] || 'm-all';

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
      (function(){var u=c.use||(E.uses&&E.uses[c.t]);return u?'<div><span class="lab">How to use it</span>'+u+'</div>':'';})()+
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

/* ---------------- How to Trade (cheat sheet) ---------------- */
(function(){
  const groups=[['Layer 0 — PD Arrays (the atoms)',E.pd_arrays],['Layer 1 — Mechanics',E.mechanics],['Quarterly Theory & Time — Daye',E.timing],['Mentor Models & Named Vocabulary',E.models]];
  let html='';
  groups.forEach(g=>{
    html+='<div class="htgroup"><div class="sublabel">'+g[0]+'</div>';
    g[1].forEach(c=>{
      const u=c.use||(E.uses&&E.uses[c.t])||'<span class="mnone">(no recipe yet)</span>';
      html+='<div class="htrow"><div class="hthead"><span class="httitle">'+esc(c.t)+'</span>'+chip(c.v)+'<span class="htstep">'+esc(c.step)+'</span></div><div class="htuse">'+u+'</div></div>';
    });
    html+='</div>';
  });
  const host=$('#howtoList'); host.innerHTML=html;
  const box=$('#howtoSearch');
  if(box) box.addEventListener('input',()=>{
    const q=box.value.trim().toLowerCase();
    host.querySelectorAll('.htrow').forEach(r=>r.classList.toggle('hide', !!q && r.textContent.toLowerCase().indexOf(q)===-1));
    host.querySelectorAll('.htgroup').forEach(gr=>{ const vis=gr.querySelectorAll('.htrow:not(.hide)').length>0; gr.classList.toggle('hide', !!q && !vis); });
  });
})();

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
    '<p><a class="guidelink" href="mentors/'+m.id+'.html">📖 Full guide →</a></p>'+
    row('Philosophy', m.phil)+
    row('Sessions', m.ses)+
    row('Signature setups', m.setups.map(s=>'<span class="tag">'+s[0]+' '+chip(s[1])+'</span>').join(''))+
    row('Maps to frame', m.vocab);
}
showMentor(0);

/* ---------------- Mind Map ---------------- */
(function(){
  const all = [].concat(E.pd_arrays, E.mechanics, E.timing, E.models);
  const stepsOf = c => [...new Set(((c.step||'').match(/\d{1,2}/g)||[]).map(x=>parseInt(x,10)))].filter(n=>n>=1&&n<=7);
  const byStep = {}; for(let i=1;i<=7;i++) byStep[i]=[];
  all.forEach(c => stepsOf(c).forEach(n => byStep[n].push(c)));
  const host=$('#mapHost'), meter=$('#mapMeter');
  const nm = id => { const m=E.mentors.find(x=>x.id===id); return m?m.name:id; };
  const conceptChips = num => (byStep[num]||[]).map(c=>'<button class="mchip '+c.v+'" data-concept="'+esc(c.t)+'">'+esc(c.t.replace(/\s*\(.*\)\s*/,''))+'</button>').join('') || '<span class="mnone">—</span>';

  function renderCombined(){
    meter.innerHTML='';
    let html='<div class="maproot">🎯 Framing a high-probability setup</div>';
    E.frame.forEach((s,i)=>{
      const num=i+1, mentors=s.mentors;
      const isAll = mentors.some(m=>/^all$/i.test(m[0]));
      const syncN = isAll ? 5 : new Set(mentors.map(m=>m[0].toLowerCase())).size;
      const mChips = mentors.map(m=>'<button class="mchip '+mcls(m[0])+'" data-mentor="'+m[0].toLowerCase()+'" title="'+esc(m[1])+'">'+esc(m[0])+'</button>').join('');
      html += '<div class="mapstep'+(syncN>=4?' sync':'')+'">'+
        '<div class="mcluster left">'+conceptChips(num)+'</div>'+
        '<div class="mnode"><div class="mnum">STEP '+s.n+'</div><div class="mttl">'+esc(s.t)+'</div>'+chip(s.verdict[0])+
          '<div class="msync">'+(syncN>=5?'all 5 mentors sync ⚡':syncN+' mentors')+'</div></div>'+
        '<div class="mcluster right">'+mChips+'</div></div>';
    });
    host.innerHTML=html;
  }

  function renderMentor(id){
    const cov=E.coverage.mentors[id], auth=E.coverage.authorities, M=E.mentors.find(x=>x.id===id);
    let solo=0; const fillSet=new Set();
    for(let n=1;n<=7;n++){ const covered=cov.steps[n].c==='full'||auth[n]===id; if(covered) solo++; else fillSet.add(auth[n]); }
    const fills=[...fillSet].map(a=>'<span class="mchip '+mcls(a)+'">'+esc(nm(a))+'</span>').join(' ');
    meter.innerHTML='<span class="mchip '+mcls(id)+'">'+esc(M.name)+'</span> <b>'+esc(M.owns)+'</b> — covers <b>'+solo+'/7</b> steps on its own; '+(7-solo)+' gap-filled via '+(fills||'—')+'.';
    let html='<div class="maproot '+mcls(id)+'">'+esc(M.name)+' — '+esc(M.owns)+'</div>';
    E.frame.forEach((s,i)=>{
      const num=i+1, cell=cov.steps[num], isAuth=auth[num]===id, covered=cell.c==='full'||isAuth;
      let teach='';
      if(cell.own) teach+='<div class="teach own '+mcls(id)+'"><span class="tlab">'+esc(M.name)+(cell.c==='partial'&&!isAuth?' (partial)':'')+'</span>'+esc(cell.own)+'</div>';
      if(!covered){ const a=auth[num]; teach+='<div class="teach fill"><span class="tlab">via '+esc(nm(a))+'</span>'+esc(E.coverage.mentors[a].steps[num].own)+'</div>'; }
      (cov.dead||[]).filter(d=>d.step===num).forEach(d=>{ teach+='<div class="teach drop"><span class="tlab">✕ drop '+chip(d.tier)+'</span>'+esc(d.label)+' — '+esc(d.why)+'</div>'; });
      html += '<div class="mapstep'+(covered?'':' gap')+'">'+
        '<div class="mcluster left">'+conceptChips(num)+'</div>'+
        '<div class="mnode"><div class="mnum">STEP '+s.n+'</div><div class="mttl">'+esc(s.t)+'</div>'+chip(s.verdict[0])+
          '<div class="msync">'+(covered?'own':'gap → via '+esc(nm(auth[num])))+'</div></div>'+
        '<div class="mcluster right teachcol">'+teach+'</div></div>';
    });
    host.innerHTML=html;
  }

  function setMap(mode){
    document.querySelectorAll('#mapMode button').forEach(b=>b.classList.toggle('on',b.dataset.map===mode));
    if(mode==='combined') renderCombined(); else renderMentor(mode);
    host.scrollIntoView({behavior:'smooth',block:'nearest'});
  }
  document.querySelectorAll('#mapMode button, .maplegend [data-map]').forEach(b=>b.onclick=()=>setMap(b.dataset.map));
  host.addEventListener('click',e=>{
    const c=e.target.getAttribute&&e.target.getAttribute('data-concept');
    const m=e.target.getAttribute&&e.target.getAttribute('data-mentor');
    if(c){ switchView('concepts'); const box=$('#conceptSearch'); if(box){ box.value=c; box.dispatchEvent(new Event('input')); } }
    if(m){ switchView('mentors'); const idx=E.mentors.findIndex(x=>x.id===m); if(idx>=0) showMentor(idx); }
  });
  renderCombined();
})();

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
