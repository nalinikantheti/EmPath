/* Presentation-only local draft. Routing, environmental weights and data stay in the shared engine. */
(async()=>{
  for(let i=0;i<400&&(!window.empathWayfinderReady||!window.empathSelection||!document.getElementById('score-model')||document.getElementById('share')?.textContent!=='Share ranked areas');i++)await new Promise(resolve=>setTimeout(resolve,100));
  const c=window.empathContext;
  if(!c?.publicMode||!window.empathWayfinderReady)return;
  const $=id=>document.getElementById(id),entry=window.empathGuidedEntry||{},aside=document.querySelector('aside');
  const names={supermarket:'Groceries',pharmacy:'Pharmacies',park:'Parks',bank:'Banks',hospital:'Hospitals',library:'Libraries'};
  const common=['supermarket','pharmacy','park','bank','hospital','library'];
  const icons={supermarket:'<path d="M3 4h2l2 11h10l3-8H6"/><circle cx="9" cy="19" r="1"/><circle cx="17" cy="19" r="1"/>',pharmacy:'<path d="m8 16 8-8M7 17a4 4 0 0 1-1-6l5-5a4 4 0 1 1 6 6l-5 5a4 4 0 0 1-5 0Z"/>',park:'<path d="M12 3 6 11h3l-4 6h14l-4-6h3L12 3ZM12 17v4"/>',bank:'<path d="m3 8 9-5 9 5H3ZM5 10v8m5-8v8m4-8v8m5-8v8M3 21h18"/>',hospital:'<path d="M5 21V5h14v16M3 21h18M10 8h4m-2-2v4M9 21v-6h6v6"/>',library:'<path d="M3 5c4-1 7 0 9 2 2-2 5-3 9-2v14c-4-1-7 0-9 2-2-2-5-3-9-2V5Zm9 2v14"/>'};
  let step=entry.block?3:1,selectedArea=null,overlayLegend='',restoreSelection=Boolean(entry.block);
  const root=$('area-controls'),categories=$('categories'),form=$('address-form'),addressStatus=$('address-status'),summary=$('summary'),recommendations=$('recommendations'),share=$('share'),gray=$('gray-explanation');
  const all=$('all'),clear=$('clear'),scope=$('scope'),county=$('county-notice'),shareMessage=$('share-message');
  const placeLabels=Array.from(categories.children);
  const originalAccess=window.EmPathColors.access.bind(window.EmPathColors);
  const palette=['#235d4b','#78a387','#e0e6bf','#d3af80','#b16d4d'];
  window.EmPathColors.access=value=>value==null?originalAccess(value):window.EmPathColors.blend(palette,value/100);
  document.body.classList.add('guided-view');
  document.querySelector('.app-nav').innerHTML='<a class="brand" href="index.html">EmPath</a><span class="guided-scope">Plano, Texas</span><button class="guided-help-button" type="button" id="guided-help">How it works</button>';
  const heading=document.querySelector('aside>h1');heading.className='guided-heading';
  const description=document.createElement('p');description.className='guided-description';heading.after(description);
  document.querySelector('.model-tag')?.remove();
  const story=document.querySelector('.app-story-intro'),demo=$('show-route-demo');story?.remove();
  document.querySelectorAll('aside>.journey-next').forEach(node=>node.remove());
  $('mode-area').textContent='Compare areas';
  const stepper=document.createElement('nav');stepper.className='guided-steps';stepper.setAttribute('aria-label','Compare areas steps');
  for(const [index,label]of ['Places','Location','Results'].entries()){
    const button=document.createElement('button');button.type='button';button.dataset.step=index+1;button.innerHTML='<span>'+(index+1)+'</span>'+label;button.onclick=()=>setStep(index+1);stepper.appendChild(button);
  }
  document.querySelector('.mode-switch').after(stepper);
  const scroll=document.createElement('div');scroll.className='guided-scroll';scroll.id='guided-scroll';
  const steps=[1,2,3].map(index=>{const section=document.createElement('section');section.className='guided-pane';section.id='guided-step-'+index;section.setAttribute('aria-labelledby','guided-title-'+index);return section;});
  steps[0].innerHTML='<h2 id="guided-title-1" tabindex="-1">What does your family need nearby?</h2><p class="guided-step-copy">Choose a few everyday places. We’ll compare the walks to each.</p>';
  const presets=document.createElement('div');presets.className='guided-preset-row';
  const everyday=document.createElement('button');everyday.type='button';everyday.id='guided-essentials';everyday.textContent='Everyday essentials';everyday.onclick=()=>preset(['supermarket','pharmacy','park']);
  all.textContent='Select all';all.classList.remove('primary');clear.textContent='Clear';clear.className='guided-clear';
  presets.append(everyday,all,clear);steps[0].append(presets,categories);
  const popular=document.createElement('div');popular.className='guided-place-grid';
  const more=document.createElement('details');more.className='guided-more-places';more.id='guided-more-places';
  more.innerHTML='<summary>More places</summary><input type="search" id="guided-place-search" placeholder="Find a type of place" aria-label="Search destination types">';
  const groups=new Map();
  function groupFor(key){if(/temple|church|mosque|worship|synagogue|gurdwara/.test(key))return 'Community & worship';if(/clinic|hospital|pharmacy/.test(key))return 'Health';if(/school|college|library/.test(key))return 'Learning';if(/park|playground|gym|sports|swimming|recreation/.test(key))return 'Outdoors & recreation';return 'Shops & everyday life';}
  for(const label of placeLabels){
    const input=label.querySelector('input'),key=input.value;
    if(common.includes(key)){
      const icon=document.createElement('span');icon.className='guided-place-icon';icon.setAttribute('aria-hidden','true');icon.innerHTML='<svg viewBox="0 0 24 24">'+icons[key]+'</svg>';
      const title=document.createElement('span');title.className='guided-place-title';title.textContent=names[key];label.replaceChildren(icon,title,input);popular.append(label);
    }else{
      const groupName=groupFor(key);
      if(!groups.has(groupName)){const group=document.createElement('section');group.className='guided-place-group';const title=document.createElement('h3');title.textContent=groupName;group.append(title);groups.set(groupName,group);more.append(group);}
      groups.get(groupName).append(label);
    }
  }
  common.forEach(key=>{const label=Array.from(popular.children).find(label=>label.querySelector('input').value===key);if(label)popular.append(label);});
  categories.replaceChildren(popular,more);
  const count=document.createElement('p');count.className='guided-selection-count';count.id='guided-selection-count';count.setAttribute('aria-live','polite');steps[0].append(count);
  more.querySelector('input').oninput=event=>{
    const query=event.target.value.toLowerCase().trim();
    for(const group of groups.values()){for(const label of group.querySelectorAll('label'))label.hidden=!label.textContent.toLowerCase().includes(query);group.hidden=!Array.from(group.querySelectorAll('label')).some(label=>!label.hidden);}
  };
  steps[1].innerHTML='<h2 id="guided-title-2" tabindex="-1">Where would you like to look?</h2><p class="guided-step-copy">Look up an address, choose a colored area on the map, or compare all of Plano.</p><div class="guided-choice-tags" id="guided-choice-tags"></div>';
  form.querySelector('label').textContent='Have a home or address in mind?';$('address-input').placeholder='Street address in Plano';
  const alternative=document.createElement('div');alternative.className='guided-location-alternative';alternative.innerHTML='<strong>Still exploring?</strong><p>Use the button below to start with areas across Plano. You can inspect the walks and housing context for any area.</p>';
  steps[1].append(form,addressStatus,alternative);
  steps[2].innerHTML='<h2 id="guided-title-3" tabindex="-1">Areas to explore</h2><p class="guided-step-copy">Choose an area to see its everyday walks and housing context.</p><div class="guided-selected-area" id="guided-selected-area" hidden><div><small>Your selected area</small><strong id="guided-area-name"></strong></div><button type="button" id="guided-clear-area">Change area</button></div>';
  const coverage=$('boundary-review');steps[2].append(summary);if(coverage)steps[2].append(coverage);steps[2].append(recommendations);
  const routePanel=recommendations.querySelector('#route-panel'),rankList=recommendations.querySelector('#rank-list'),rankSummary=recommendations.querySelector('#rank-summary');
  recommendations.querySelector(':scope>h2')?.remove();
  const shortlist=document.createElement('details');shortlist.className='guided-shortlist';shortlist.id='guided-shortlist';shortlist.open=true;shortlist.innerHTML='<summary>Explore the suggested areas</summary>';
  shortlist.append(rankSummary,rankList,share.parentElement,shareMessage);recommendations.insertBefore(shortlist,routePanel);
  if(gray)steps[2].append(gray);
  const areaContext=$('area-context');if(areaContext)steps[2].append(areaContext);
  const note=document.createElement('p');note.className='guided-note';note.textContent='Area comparisons, not available home listings. Walking routes begin at neighborhood reference points.';steps[2].append(note);
  root.replaceChildren(...steps,scope,county);
  const options=document.createElement('details');options.className='guided-options';options.id='guided-options';options.innerHTML='<summary>Map options</summary><p>Compare another walking priority or add housing, tree cover and other context.</p>';
  const contextPanel=$('context-panel');options.append(contextPanel);
  const model=contextPanel.querySelector('#score-model');model.setAttribute('aria-label','Walking comparison');
  for(const option of model.options)option.textContent=option.value==='shade'?'Prefer more tree cover':option.value==='time'?'Shortest walking time':'How priorities change the ranking';
  const contextSelect=contextPanel.querySelector('#context-layer');contextSelect.setAttribute('aria-label','What to show on the map');if(contextSelect.options[0])contextSelect.options[0].textContent='Walking effort';
  const optionHeadings=contextPanel.querySelectorAll('h2');optionHeadings[0].textContent='Walking comparison';optionHeadings[1].textContent='Show on the map';
  const footer=document.querySelector('.app-footer');footer.innerHTML='<button type="button" id="guided-methodology">Methodology</button><a href="master-map.html" target="_blank" rel="noopener">All maps ↗</a><a href="feedback.html">Share feedback</a>';
  if(demo){demo.className='text-button';demo.textContent='Try an example walk';options.append(demo);}
  const wayfinder=$('wayfinder');
  scroll.append(root,wayfinder,options,footer);aside.append(scroll);
  const actions=document.createElement('div');actions.className='guided-actions';actions.innerHTML='<button type="button" id="guided-back">Back</button><button type="button" class="guided-next" id="guided-next">Next: choose an area →</button>';aside.append(actions);
  $('guided-back').onclick=()=>setStep(step-1);
  $('guided-next').onclick=()=>setStep(step===1?2:3);
  const hint=document.createElement('section');hint.className='guided-map-hint';hint.id='guided-map-hint';c.map.getContainer().append(hint);
  const legend=$('legend');document.querySelector('#map .leaflet-bottom.leaflet-left')?.append(legend);
  const dialog=document.createElement('dialog');dialog.id='guided-dialog';dialog.className='guided-dialog';dialog.setAttribute('aria-labelledby','guided-dialog-title');dialog.innerHTML='<header class="guided-dialog-header"><h2 id="guided-dialog-title"></h2><button type="button" aria-label="Close help">×</button></header><div class="guided-dialog-body"></div>';document.body.append(dialog);dialog.querySelector('button').onclick=()=>dialog.close();
  function help(){
    $('guided-dialog-title').textContent='Three steps to explore';
    dialog.querySelector('.guided-dialog-body').innerHTML='<ol><li><strong>Choose places.</strong> Start with everyday essentials or select your own destination types.</li><li><strong>Choose a location.</strong> Find a Plano address, choose a colored area, or compare areas across the city.</li><li><strong>Explore results.</strong> Select a suggested area. Check a destination to show its walking route, or expand its card to compare routes.</li></ol><p>Walking effort combines distance with estimates of nearby trees, traffic and surface heat. Actual walking time is shown with each route.</p><p>You can change your choices at any time using the step buttons. Advanced comparisons and environmental layers are under Map options.</p>';
    dialog.showModal();
  }
  $('guided-help').onclick=help;
  $('guided-methodology').onclick=async()=>{
    $('guided-dialog-title').textContent='Methodology';dialog.querySelector('.guided-dialog-body').textContent='Loading methodology…';dialog.showModal();
    try{const response=await fetch('behind.html');if(!response.ok)throw Error();const doc=new DOMParser().parseFromString(await response.text(),'text/html'),main=doc.querySelector('main');if(!main)throw Error();if(dialog.open&&$('guided-dialog-title').textContent==='Methodology'){dialog.querySelector('.guided-dialog-body').innerHTML=main.innerHTML;dialog.querySelector('.guided-dialog-body>h1')?.remove();}}
    catch{dialog.querySelector('.guided-dialog-body').innerHTML='<p>Methodology could not load. <a href="behind.html">Read the methodology page</a>.</p>';}
  };
  function preset(keys){for(const input of categories.querySelectorAll('input[type=checkbox]'))input.checked=keys.includes(input.value);window.empathRefresh();}
  function setStep(next){
    if(next<1||next>3||next>1&&!window.empathSelection.categories.length)return;
    step=next;render();scroll.scrollTop=0;$('guided-title-'+step).focus({preventScroll:true});
  }
  function quietMap(){
    if(window.empathMode==='route')return;
    const selected=window.empathSelection.categories.length>0;
    c.layer.eachLayer(layer=>{const style={color:'#85947f',weight:c.map.getZoom()<13?.2:.45,opacity:.43};if(!selected)style.fillColor='#eef1e9';else if(!(Number(layer.feature.properties.HU100)>0))style.fillColor='#e4e8e0';layer.setStyle(style);});
  }
  function visibleRoutes(){return Object.values(window.empathRouteVisibility||{}).some(state=>state.route);}
  function updateLegend(){
    if(window.empathMode==='route'){
      if(!window.empathWayfindingState){legend.hidden=false;legend.innerHTML='<b>Plan your walk</b><p>Choose a start and destination to compare walking routes.</p>';}
      return;
    }
    if(visibleRoutes())return;
    if(contextSelect.value){if(overlayLegend){legend.innerHTML=overlayLegend;legend.hidden=false;}else legend.hidden=true;return;}
    legend.hidden=false;
    if(!window.empathSelection.categories.length){legend.innerHTML='<b>Choose your everyday places</b><p>Select at least one place type to compare walking access across Plano.</p>';return;}
    const mode=window.empathScoreMode,gradient=mode==='difference'?'#2166ac,#f7f7f7,#b2182b':palette.join(',');
    const title=mode==='time'?'Walking time':mode==='difference'?'How the ranking changes':'Walking effort';
    const lower=mode==='time'?'Shorter walks':mode==='difference'?'Improves':'Less effort',higher=mode==='time'?'Longer walks':mode==='difference'?'Worsens':'More effort';
    legend.innerHTML='<b>'+title+'</b><div class="ramp" style="background:linear-gradient(90deg,'+gradient+')"></div><div class="guided-legend-range"><span>'+lower+'</span><span>'+higher+'</span></div><div class="guided-legend-keys"><span><i></i>Not residential</span><span><i></i>Needs data review</span></div>';
  }
  const originalOverlayChange=contextSelect.onchange;
  contextSelect.onchange=async function(...args){await originalOverlayChange?.apply(this,args);overlayLegend=this.value&&!legend.hidden&&window.empathActiveContext?.field===this.value?legend.innerHTML:'';updateLegend();};
  function render(){
    const selection=window.empathSelection,keys=selection.categories,routeMode=window.empathMode==='route';
    heading.textContent=routeMode?'Plan an everyday walk.':'Find an area that fits.';
    description.textContent=routeMode?'Choose your start and destination. Compare the actual paths.':'Compare walks to the places your family needs.';
    stepper.hidden=routeMode;actions.hidden=routeMode;options.hidden=routeMode;
    if(!keys.length&&step>1)step=1;
    steps.forEach((pane,index)=>pane.hidden=index+1!==step);
    for(const button of stepper.children){const index=Number(button.dataset.step);button.disabled=index>1&&!keys.length;button.classList.toggle('is-complete',index<step);if(index===step)button.setAttribute('aria-current','step');else button.removeAttribute('aria-current');}
    count.textContent=keys.length?keys.length+' place '+(keys.length===1?'type':'types')+' selected':'Choose at least one place to begin.';
    more.querySelector('summary').textContent='More places'+(keys.filter(key=>!common.includes(key)).length?' · '+keys.filter(key=>!common.includes(key)).length+' selected':'');
    $('guided-choice-tags').replaceChildren(...keys.map(key=>{const tag=document.createElement('span');tag.textContent=names[key]||c.labels[key]||key;return tag;}));
    $('guided-back').hidden=step===1;$('guided-next').hidden=step===3;$('guided-next').disabled=!keys.length;$('guided-next').textContent=step===1?'Next: choose an area →':'Compare areas in Plano →';
    summary.textContent=keys.length?selection.scores.complete.toLocaleString()+' residential areas compared for your '+keys.length+' chosen '+(keys.length===1?'place.':'places.'):'Choose a place type to compare areas.';
    rankSummary.textContent=window.empathScoreMode==='time'?'Shorter average walks first':window.empathScoreMode==='difference'?'Largest changes in the ranking first':'Lower estimated walking effort first';
    const current=window.empathRouteState?.blockId||selectedArea;selectedArea=current||null;
    $('guided-selected-area').hidden=!current;
    if(current)$('guided-area-name').textContent=c.byId[current]?.public_area_label||'Selected area';
    if(gray){gray.querySelector('summary').textContent='About areas without a score';gray.querySelector('p').textContent='Gray areas have no recorded housing. Pale amber areas need route or connection data review. Colors compare the places you selected.';}
    const h=wayfinder.querySelector(':scope>h2');if(h)h.textContent='Where would you like to walk?';
    const find=wayfinder.querySelector('.find-walk');if(find)find.textContent='Find my walk →';
    const resultHeading=$('walk-result')?.querySelector('h2');if(resultHeading)resultHeading.textContent='Your suggested walk';
    hint.hidden=routeMode;
    hint.replaceChildren();
    const label=document.createElement('small');label.textContent=keys.length?'Your comparison':'Start with step 1';
    const value=document.createElement('strong');value.textContent=keys.length?keys.slice(0,3).map(key=>names[key]||c.labels[key]||key).join(' · ')+(keys.length>3?' + '+(keys.length-3)+' more':''):'Choose the places that matter';
    const copy=document.createElement('p');copy.textContent=step===2?'Choose a colored area, enter an address, or explore the whole city.':'Map colors compare walking access to your chosen places.';hint.append(label,value,copy);
    quietMap();updateLegend();
  }
  $('guided-clear-area').onclick=()=>{selectedArea=null;window.empathClearAreaSelection?.();shortlist.open=true;setStep(2);};
  window.addEventListener('empath-area-picked',event=>{selectedArea=event.detail.blockId;step=3;shortlist.open=false;render();scroll.scrollTop=0;});
  window.addEventListener('empath-area-cleared',()=>{selectedArea=null;restoreSelection=false;shortlist.open=true;render();});
  window.addEventListener('empath-selection-changed',()=>queueMicrotask(render));
  window.addEventListener('empath-mode-changed',()=>queueMicrotask(render));
  window.addEventListener('empath-route-selected',()=>{
    selectedArea=window.empathRouteState?.blockId;
    if(restoreSelection){step=3;restoreSelection=false;shortlist.open=false;}
    render();
  });
  window.addEventListener('empath-walk-ready',()=>queueMicrotask(render));
  c.map.on('zoomend',quietMap);
  document.addEventListener('change',event=>{if(event.target.matches('.show-destination-route,.show-destination-comparison'))queueMicrotask(updateLegend);});
  if(!entry.hasCategories&&window.empathMode!=='route')preset(['supermarket','pharmacy','park']);else window.empathRefresh();
  if(window.empathRouteState?.blockId){selectedArea=window.empathRouteState.blockId;step=3;restoreSelection=false;shortlist.open=false;}
  render();c.map.options.zoomSnap=.25;c.map.invalidateSize();
  if(!selectedArea&&window.empathMode!=='route')c.map.fitBounds(c.layer.getBounds(),{padding:[28,28]});
  window.empathGuided={setStep,get step(){return step;},showHelp:help};
})();
