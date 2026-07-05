/* Mentor deep-guide renderer. Reads window.GUIDE, renders into #guide. Vanilla, no deps. */
(function(){
  var ORDER=[["ttrades","TTrades"],["daye","Daye"],["dayement","Daye Mentorship"],["gxt","GxT"],["ict","ICT"],["dexter","Dexter"],["xyj","XYJ"]];
  var G=window.GUIDE, host=document.getElementById('guide');
  if(!G||!host){ console.error('GUIDE data or #guide host missing'); return; }
  function esc(s){return String(s).replace(/[&<>]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
  var toc=G.sections.map(function(s){return '<a href="#'+s.id+'">'+esc(s.title)+'</a>';}).join('');
  var secs=G.sections.map(function(s){
    return '<section class="gsec"><h2 id="'+s.id+'">'+esc(s.title)+'</h2>'+(s.html||'<p class="nc">Not covered in this mentor\'s corpus.</p>')+'</section>';
  }).join('');
  var i=ORDER.findIndex(function(m){return m[0]===G.id;});
  var prev=i>0?ORDER[i-1]:null, next=i>=0&&i<ORDER.length-1?ORDER[i+1]:null;
  var nav='<div class="gnav">'+
    (prev?'<a href="'+prev[0]+'.html">← '+esc(prev[1])+'</a>':'<span></span>')+
    (next?'<a href="'+next[0]+'.html">'+esc(next[1])+' →</a>':'<span></span>')+'</div>';
  host.innerHTML=
    '<div class="ghead"><div class="back"><a href="../index.html">← Back to The Framework</a></div>'+
      '<h1>'+esc(G.name)+'</h1><div class="tag">'+esc(G.tagline||'')+'</div></div>'+
    '<nav class="toc">'+toc+'</nav>'+
    '<main class="body">'+secs+'</main>'+nav;
  document.title=G.name+' — Deep Guide';
})();
