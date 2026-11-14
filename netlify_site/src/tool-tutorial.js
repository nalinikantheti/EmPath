/* Replayable practice using fixed municipal addresses. Personal inputs stay in memory. */
(async()=>{
  for(let i=0;i<400&&(!window.empathGuided||!window.empathAddressControls||!window.empathWayfinderControls);i++)await new Promise(resolve=>setTimeout(resolve,100));
  const c=window.empathContext,g=window.empathGuided;if(!c?.publicMode||!g)return;
  const $=id=>document.getElementById(id),E=window.empathContextTools.esc,trigger=$('guided-help');
  let locations;
  try{const response=await fetch('data/tutorial_presets.json');if(!response.ok)throw Error();locations=(await response.json()).locations;if(locations.length!==2||locations.some(p=>!c.byId[p.blockId]))throw Error();}
  catch{
    const failure=document.createElement('dialog');failure.className='tool-tutorial-welcome';failure.innerHTML='<div class="tool-tutorial-welcome-body"><h2>How to Use</h2><p>The preset examples could not load. Refresh the page to try again.</p><button type="button">Close</button></div>';document.body.append(failure);failure.querySelector('button').onclick=()=>failure.close();trigger.onclick=()=>failure.showModal();failure.showModal();return;
  }
  const [origin,destination]=locations;
  const welcome=document.createElement('dialog');welcome.id='tool-tutorial-welcome';welcome.className='tool-tutorial-welcome';welcome.setAttribute('aria-labelledby','tool-tutorial-welcome-title');
  welcome.innerHTML='<header class="tool-tutorial-welcome-header"><p>EmPath · How to Use</p><h2 id="tool-tutorial-welcome-title" tabindex="-1"></h2><button class="tool-tutorial-close" type="button" aria-label="Close tutorial">×</button></header><div class="tool-tutorial-welcome-body"></div>';
  document.body.append(welcome);
  const coach=document.createElement('dialog');coach.id='tool-tutorial-coach';coach.className='tool-tutorial-coach';coach.setAttribute('aria-labelledby','tool-tutorial-step-title');coach.setAttribute('aria-describedby','tool-tutorial-step-copy');
  coach.innerHTML='<header><p id="tool-tutorial-progress"></p><button class="tool-tutorial-close" type="button" aria-label="Exit tutorial">×</button></header><h2 id="tool-tutorial-step-title" tabindex="-1"></h2><button id="tool-tutorial-details" class="tool-tutorial-text" type="button" aria-controls="tool-tutorial-step-copy">Show instructions</button><div id="tool-tutorial-step-copy"></div><p class="tool-tutorial-status" id="tool-tutorial-status" role="status"></p><div class="tool-tutorial-controls"><button id="tool-tutorial-back" type="button">Back</button><button id="tool-tutorial-next" class="tool-tutorial-primary" type="button">Next</button></div><button id="tool-tutorial-keep" class="tool-tutorial-text" type="button" hidden>Keep this example walk</button>';
  document.body.append(coach);
  const toast=document.createElement('p');toast.className='tool-tutorial-toast';toast.setAttribute('role','status');toast.hidden=true;document.body.append(toast);
  const mobile=matchMedia('(max-width:860px)');
  let view='closed',index=0,snapshot=null,version=0,busy=false,highlight=null,closing=null,toastTimer=0,detailsExpanded=!mobile.matches;
  const steps=[
    {title:'Choose your everyday places',target:'#categories',next:'Next: try an address',copy:'<p>Start with <strong>groceries, pharmacies and parks</strong>. We have selected them for this practice run.</p><p>Each category has its own pin symbol. Numbered pins group nearby places.</p>'},
    {title:'Start with a preset address',target:'#address-form',next:'Find this preset address',copy:'<p>The address field is filled with our first example:</p>'+addressCard(origin)+'<p>Continue to load its area and walking results. You do not need to enter a personal address.</p>'},
    {title:'Read the area results',target:'#route-panel',next:'Next: plan a preset walk',copy:'<p>These cards show mapped destinations and walking times from the area around <strong>'+E(origin.name)+'</strong>.</p><p>Check a destination to show its route; uncheck it to remove the path. <strong>Change area</strong> clears the location and its paths.</p>'},
    {title:'Plan a walk between two addresses',target:'#walk-form',next:'Next: compare the routes',copy:'<p><strong>Plan a walk</strong> uses a start and destination. We have loaded both examples and calculated their connected route.</p>'+addressPair()+'<p>The teal line is the EmPath route. Times are estimates; check actual entrances and crossings.</p>'},
    {title:'Compare, then make it your own',target:'#walk-result',next:'Finish and return to my view',copy:'<p>The <strong>Show shortest walk</strong> checkbox adds the purple dashed alternative. Compare the walking times and environmental estimates for the same two addresses.</p><p>Use the numbered workflow to open Methodology, or drag the divider to widen the controls panel.</p><p>Finish to return to your original view, or keep the example walk. You can replay this tutorial with <strong>How to Use</strong>.</p>'}
  ];
  function addressCard(point){return'<div class="tool-tutorial-address"><strong>'+E(point.name)+'</strong><span>'+E(point.address)+'</span></div>';}
  function addressPair(){return'<div class="tool-tutorial-address-pair">'+addressCard(origin)+addressCard(destination)+'</div>';}
  function showToast(text){clearTimeout(toastTimer);toast.textContent=text;toast.hidden=false;toastTimer=setTimeout(()=>toast.hidden=true,7000);}
  function capture(){return{
    categories:window.empathSelection.categories.slice(),model:window.empathScoreMode,mode:window.empathMode,url:location.href,
    blockId:window.empathRouteState?.blockId||new URLSearchParams(location.search).get('block'),
    visibility:JSON.parse(JSON.stringify(window.empathRouteVisibility||{})),address:window.empathAddressControls.capture(),walk:window.empathWayfinderControls.capture(),
    layer:$('context-layer').value,view:g.captureView(),center:c.map.getCenter(),zoom:c.map.getZoom(),pins:$('show-destination-pins')?.checked??true
  };}
  function setCategories(keys){for(const input of document.querySelectorAll('#categories input[type=checkbox]'))input.checked=keys.includes(input.value);window.empathRefresh();}
  function settleMap(){return new Promise(resolve=>{const done=()=>{clearTimeout(timer);c.map.off('zoomend',done);resolve();};const timer=setTimeout(done,400);c.map.once('zoomend',done);});}
  async function setLayer(value){const select=$('context-layer');select.value=value;await select.onchange();document.dispatchEvent(new Event('empath-tutorial-layer-changed'));}
  async function restore(saved){
    window.empathAddressControls.cancel();window.empathWayfinderControls.cancel();window.empathClearAreaSelection();window.empathSetMode('area');
    const model=$('score-model');model.value=saved.model;model.onchange();setCategories(saved.categories);
    // Restore any previous walk directly from its saved endpoints; no address lookup is repeated.
    window.empathSetMode('route');await window.empathWayfinderControls.restore(saved.walk);window.empathSetMode('area');
    if(saved.blockId&&c.byId[saved.blockId])await window.empathSelectBlock(saved.blockId,false);
    if(window.empathRouteState){
      for(const [position,route]of window.empathRouteState.routes.entries()){
        const card=$('route-panel').querySelectorAll('.route-card')[position],state=saved.visibility[route.category];if(!card||!state)continue;
        const show=card.querySelector('.show-destination-route'),comparison=card.querySelector('.show-destination-comparison');
        if(show&&state.route){show.checked=true;show.onchange();}if(comparison&&state.comparison){comparison.checked=true;comparison.onchange();}
      }
    }
    window.empathAddressControls.restore(saved.address);
    if(saved.mode==='route')window.empathSetMode('route');
    await setLayer(saved.layer);
    const pins=$('show-destination-pins');if(pins&&pins.checked!==saved.pins){pins.checked=saved.pins;pins.onchange({target:pins});}
    await settleMap();g.restoreView(saved.view);c.map.stop();c.map.setView(saved.center,saved.zoom,{animate:false});history.replaceState(null,'',saved.url);
  }
  function clearHighlight(){highlight?.classList.remove('tool-tutorial-highlight');highlight=null;}
  function pointTo(selector){
    clearHighlight();highlight=document.querySelector(selector);if(!highlight)return;highlight.classList.add('tool-tutorial-highlight');
    const scroll=$('guided-scroll'),rect=highlight.getBoundingClientRect(),container=scroll.getBoundingClientRect();
    if(rect.top<container.top||rect.bottom>container.bottom)scroll.scrollTop+=rect.top-container.top-12;
  }
  function setBusy(value,message=''){
    busy=value;$('tool-tutorial-back').disabled=value;$('tool-tutorial-next').disabled=value;$('tool-tutorial-keep').disabled=value;
    $('tool-tutorial-status').textContent=message;coach.setAttribute('aria-busy',String(value));
  }
  function updateDetails(){const expanded=!mobile.matches||detailsExpanded;$('tool-tutorial-details').hidden=!mobile.matches;$('tool-tutorial-details').setAttribute('aria-expanded',String(expanded));$('tool-tutorial-details').textContent=expanded?'Hide instructions':'Show instructions';$('tool-tutorial-step-copy').hidden=!expanded;}
  async function ensureWalk(){
    if(window.empathMode!=='route')window.empathSetMode('route');
    if(window.empathWayfindingState?.from.label!==origin.address||window.empathWayfindingState?.to.label!==destination.address){
      await window.empathWayfinderControls.usePreset(origin.address,destination.address);const state=window.empathWayfindingState;if(!state)return;
      const graph=await window.empathRouting.load();await settleMap();if(window.empathWayfindingState!==state)return;
      const bounds=L.latLngBounds([]);for(const index of state.least.indices)for(const line of graph.edges[index][10])for(const [lon,lat]of line)bounds.extend([lat,lon]);
      if(bounds.isValid())c.map.fitBounds(bounds,{padding:[45,45],maxZoom:14,animate:false});
    }
  }
  async function prepareStep(next,mine){
    if(next===0){
      window.empathSetMode('area');window.empathClearAreaSelection();window.empathWayfinderControls.cancel();
      const model=$('score-model');model.value='shade';model.onchange();await setLayer('');if(mine!==version)return;
      setCategories(['supermarket','pharmacy','park']);g.setStep(1);
      const pins=$('show-destination-pins');if(pins&&!pins.checked){pins.checked=true;pins.onchange({target:pins});}
    }else if(next===1){
      window.empathSetMode('area');window.empathClearAreaSelection();g.setStep(2);$('address-input').value=origin.address;
    }else if(next===2){
      window.empathSetMode('area');window.empathClearAreaSelection();await window.empathAddressControls.usePreset(origin);if(mine!==version)return;g.setStep(3);
    }else{
      await ensureWalk();if(mine!==version)return;
      const comparison=$('compare-quickest');if(comparison){comparison.checked=next===4;comparison.dispatchEvent(new Event('change',{bubbles:true}));}
    }
  }
  async function go(next){
    if(next<0||next>=steps.length||view!=='tour')return;
    const mine=++version;index=next;const step=steps[index];
    clearHighlight();$('tool-tutorial-progress').textContent='Step '+(index+1)+' of '+steps.length;
    $('tool-tutorial-step-title').textContent=step.title;$('tool-tutorial-step-copy').innerHTML=step.copy;updateDetails();
    $('tool-tutorial-back').hidden=index===0;$('tool-tutorial-next').textContent=step.next;$('tool-tutorial-keep').hidden=index!==steps.length-1;
    setBusy(true,next>=2?'Loading the preset example…':'Setting up your practice view…');
    try{await prepareStep(next,mine);if(mine!==version)return;setBusy(false);pointTo(step.target);$('tool-tutorial-step-title').focus({preventScroll:true});}
    catch(error){if(mine!==version)return;setBusy(false,'The example could not load. Go back to retry, or close the tutorial.');$('tool-tutorial-next').disabled=true;}
  }
  async function finish({keep=false,completed=false,focus=true}={}){
    if(closing)return closing;
    ++version;const saved=snapshot;snapshot=null;view='closed';clearHighlight();document.body.classList.remove('tool-tutorial-active');if(coach.open)coach.close();if(welcome.open)welcome.close();
    if(!saved){if(focus)trigger.focus({preventScroll:true});return;}
    trigger.disabled=true;
    closing=Promise.resolve().then(async()=>{
      try{if(!keep)await restore(saved);showToast(completed?'Tutorial complete. Reopen it any time with How to Use.':'Your original map view has been restored.');}
      catch{window.empathAddressControls.restore(saved.address);setCategories(saved.categories);g.restoreView(saved.view);showToast('Your choices are back, but a saved route could not be reloaded.');}
      finally{trigger.disabled=false;closing=null;if(focus)trigger.focus({preventScroll:true});}
    });return closing;
  }
  async function start(){
    if(snapshot||closing)return;snapshot=capture();view='tour';if(welcome.open)welcome.close();toast.hidden=true;document.body.classList.add('tool-tutorial-active');coach.show();await go(0);
  }
  function reader(){
    view='reader';$('tool-tutorial-welcome-title').textContent='How to Use EmPath';
    welcome.querySelector('.tool-tutorial-welcome-body').innerHTML='<p>This text walkthrough uses two preset addresses. Your map will stay as it is while you read.</p>'+addressPair()+'<ol class="tool-tutorial-reader"><li><strong>Choose destinations.</strong> Under Compare areas, select the places you want nearby. Next moves to the Location step.</li><li><strong>Choose an address.</strong> Our example starts at '+E(origin.address)+'. Enter an address and activate Find, or select an area on the map.</li><li><strong>Review the results.</strong> Destination checkboxes show or hide each walking route. Change area removes the selected location and its paths.</li><li><strong>Plan a specific walk.</strong> Open Plan a walk. Use '+E(origin.address)+' in From and '+E(destination.address)+' in To. Activate Find my walk. The guided tutorial fills both for you.</li><li><strong>Compare routes.</strong> Show shortest walk toggles the purple dashed alternative. Read the ordinary walking time separately from environmental effort estimates.</li><li><strong>Navigate and resize.</strong> The numbered workflow links to Story, Tool, Method, Maps and Ideas. On desktop, focus the panel divider and press Left or Right Arrow to resize; Enter resets its width.</li></ol><div class="tool-tutorial-welcome-actions"><button class="tool-tutorial-primary" id="tool-reader-start" type="button">Try the guided tutorial</button><button id="tool-reader-done" type="button">Start exploring</button></div>';
    $('tool-reader-start').onclick=start;$('tool-reader-done').onclick=()=>finish();$('tool-tutorial-welcome-title').focus({preventScroll:true});
  }
  async function open(){
    if(snapshot||closing)await finish({focus:false});
    const methodDialog=$('guided-dialog');if(methodDialog?.open)methodDialog.close();
    view='welcome';$('tool-tutorial-welcome-title').textContent='Welcome to EmPath';
    welcome.querySelector('.tool-tutorial-welcome-body').innerHTML='<p class="tool-tutorial-intro">Find everyday places within reach.</p><p>Compare walking access across Plano, then inspect an actual walk. Try the tutorial with two preset addresses—there is nothing to type.</p>'+addressPair()+'<div class="tool-tutorial-welcome-actions"><button class="tool-tutorial-primary" id="tool-start-tutorial" type="button">Start the short tutorial</button><button id="tool-screen-reader" type="button">Screen reader walkthrough</button><button id="tool-skip-tutorial" type="button">I’m ready to explore</button></div><p class="tool-tutorial-small">You can skip now and reopen this with <strong>How to Use</strong>. Practice changes are temporary unless you choose to keep the example.</p>';
    $('tool-start-tutorial').onclick=start;$('tool-screen-reader').onclick=reader;$('tool-skip-tutorial').onclick=()=>finish();
    if(!welcome.open)welcome.showModal();$('tool-tutorial-welcome-title').focus({preventScroll:true});
  }
  welcome.querySelector('.tool-tutorial-close').onclick=()=>finish();welcome.addEventListener('cancel',event=>{event.preventDefault();finish();});
  coach.querySelector('.tool-tutorial-close').onclick=()=>finish();
  $('tool-tutorial-back').onclick=()=>{if(!busy)go(index-1);};
  $('tool-tutorial-next').onclick=()=>{if(!busy){if(index===steps.length-1)finish({completed:true});else go(index+1);}};
  $('tool-tutorial-keep').onclick=()=>finish({keep:true,completed:true});
  $('tool-tutorial-details').onclick=()=>{detailsExpanded=!detailsExpanded;updateDetails();};mobile.addEventListener('change',updateDetails);
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&view==='tour'){event.preventDefault();finish();}});
  document.addEventListener('click',async event=>{
    const link=event.target.closest('.guided-site-header a');if(!link||!snapshot||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
    event.preventDefault();await finish({focus:false});location.href=link.href;
  },true);
  trigger.setAttribute('aria-controls',welcome.id);trigger.onclick=open;
  window.empathTutorial={open,close:finish,get state(){return{view,index,busy,restoring:Boolean(closing)};},presets:locations};
  window.addEventListener('pageshow',event=>{if(event.persisted)open();});
  open();
})();
