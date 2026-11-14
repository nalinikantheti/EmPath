(()=>{
  document.documentElement.classList.add('js-ready');
  // Existing deep links still reveal content inside the optional technical guide.
  function revealSection(){let id;try{id=decodeURIComponent(location.hash.slice(1))}catch{return}const target=document.getElementById(id);if(!target)return;let opened=false;for(let parent=target.parentElement;parent;parent=parent.parentElement)if(parent.tagName==='DETAILS'&&!parent.open){parent.open=true;opened=true}if(opened)requestAnimationFrame(()=>target.scrollIntoView({block:'start'}));}
  revealSection();window.addEventListener('hashchange',revealSection);
  const byId=id=>document.getElementById(id);
  const controls=['time','trees','heat','traffic'];
  function score(){
    const [time,trees,heat,traffic]=controls.map(key=>Number(byId('segment-'+key).value));
    const multiplier=1+6*(1-trees/100)**2*(1+heat/100)+traffic/100;
    for(const [i,key] of controls.entries())byId(key+'-label').textContent=[time,trees,heat,traffic][i]+(i?'%':' min');
    byId('segment-result').textContent=(time*multiplier).toFixed(1);
    byId('segment-explanation').textContent=`${time} minutes × ${multiplier.toFixed(2)} multiplier`;
  }
  controls.forEach(key=>byId('segment-'+key).addEventListener('input',score));score();
  const stages=[
    {title:'Start with zero',description:'The start costs zero. No route to the other points has been found yet (∞).',totals:[0,'∞','∞','∞'],current:'s',visited:[],edges:[]},
    {title:'Look at the first connections',description:'From Start, A costs 4 and B costs 2. B has the lowest unsettled total, so examine B next.',totals:[0,4,2,'∞'],current:'b',visited:['s'],edges:['sa','sb']},
    {title:'A better way to A',description:'Through B, A costs 2 + 1 = 3, improving its previous total of 4. End can be reached through B for 2 + 6 = 8.',totals:[0,3,2,8],current:'a',visited:['s','b'],edges:['sb','ba','bd']},
    {title:'Improve the destination total',description:'Through A, End costs 3 + 3 = 6. That improves the previous total of 8. End now has the lowest unsettled total.',totals:[0,3,2,6],current:'d',visited:['s','b','a'],edges:['sb','ba','ad']},
    {title:'The lowest-cost route totals 6',description:'Start → B → A → End costs 2 + 1 + 3 = 6. Choosing the cheapest next segment alone would not provide this guarantee; the search compares accumulated totals.',totals:[0,3,2,6],visited:['s','b','a','d'],edges:['sb','ba','ad'],finished:true}
  ];let stage=0;
  function draw(){const s=stages[stage];byId('algorithm-stage').textContent=s.title;byId('algorithm-description').textContent=s.description;['s','a','b','d'].forEach((id,i)=>{const node=byId('node-'+id);node.dataset.current=String(s.current===id);node.dataset.visited=String(s.visited.includes(id));node.dataset.finished=String(!!s.finished);byId('total-'+id).textContent='Total '+s.totals[i];});['sa','sb','ba','ad','bd'].forEach(id=>byId('edge-'+id).dataset.selected=String(s.edges.includes(id)));byId('algorithm-next').disabled=stage===stages.length-1;byId('algorithm-next').textContent=stage===stages.length-1?'Route found':'Next step →';}
  byId('algorithm-next').onclick=()=>{if(stage<stages.length-1)stage++;draw();};byId('algorithm-reset').onclick=()=>{stage=0;draw();};draw();
  const values=[[8,5,7],[6,9,8],[4,8,6]],categoryControls=[...document.querySelectorAll('[name="example-category"]')];
  function compare(){const selected=categoryControls.filter(c=>c.checked).map(c=>Number(c.value)),missing=byId('example-unreachable').checked;byId('area-b-pharmacy').textContent=missing?'Unreachable':'8';const scores=values.map((row,i)=>!selected.length||(i===1&&missing&&selected.includes(2))?null:selected.reduce((sum,j)=>sum+row[j],0)/selected.length);const finite=scores.filter(v=>v!==null),best=finite.length?Math.min(...finite):null;const winners=[];['a','b','c'].forEach((id,i)=>{const row=byId('area-'+id),valid=scores[i]!==null;row.dataset.best=String(valid&&scores[i]===best);row.dataset.unavailable=String(selected.length>0&&!valid);row.querySelector('.area-average').textContent=valid?scores[i].toFixed(1):selected.length?'Unavailable':'—';if(valid&&scores[i]===best)winners.push(id.toUpperCase());});byId('area-result').textContent=!selected.length?'Choose at least one category to compare areas.':`Area${winners.length>1?'s':''} ${winners.join(' and ')} ${winners.length>1?'tie for':'has'} the lowest average cost: ${best.toFixed(1)} effort minutes.`;}
  categoryControls.forEach(c=>c.addEventListener('change',compare));byId('example-unreachable').addEventListener('change',compare);compare();
})();
