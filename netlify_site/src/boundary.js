/* Flag longer trips that may be affected by the edge of the mapped region. */
(async()=>{
  for(let i=0;i<300&&!window.empathContext;i++)await new Promise(r=>setTimeout(r,100));
  const c=window.empathContext;
  if(!c)return;
  try{
    const response=await fetch('data/boundary_corrected_method.json');
    if(!response.ok)return;
    await response.json();
  }catch{return;}
  const box=document.createElement('div');
  box.id='boundary-review';
  box.className='notice';
  box.style.marginTop='12px';
  document.getElementById('summary').after(box);
  function update(){
    const s=window.empathSelection,active=window.empathRouteState;
    const p=active&&c.blocks.features.find(f=>f.properties.GEOID20===active.blockId)?.properties;
    const bound=Number(p?.boundary_exit_lower_bound_min);
    const longerTrips=p?s.categories.filter(cat=>{
      const cost=c.lookup[active.blockId]?.[cat]?.min_friction_equivalent_minutes;
      return Number.isFinite(cost)&&cost>=bound;
    }):[];
    if(c.publicMode){
      box.hidden=!longerTrips.length;
      if(!box.hidden)box.innerHTML='Some longer walks may have closer alternatives beyond the mapped region. <a href="validation.html#boundary">Coverage details</a>';
    }else{
      box.hidden=false;
      let text='<strong>Expanded coverage: 3 km beyond Plano</strong><br>Network, services and environmental weights were extended together. Route comparisons use an origin-specific coverage check.';
      if(longerTrips.length)text+='<br>Some selected longer trips exceed this origin’s '+bound.toFixed(1)+'-minute outer-boundary lower bound and are not extent-certified.';
      box.innerHTML=text+'<br><a href="validation.html#boundary">Proof, comparison and limitations</a>';
    }
    window.empathBoundaryState={corrected:true,publicMode:Boolean(c.publicMode),blockId:active?.blockId||null};
  }
  window.addEventListener('empath-route-selected',update);
  window.addEventListener('empath-route-cleared',update);
  window.addEventListener('empath-selection-changed',update);
  update();
})();
