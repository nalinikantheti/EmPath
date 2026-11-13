/* On-demand map help. The tutorial explains controls; technical methods load separately. */
(()=>{
  const storageKey='empath-tutorial-v1';
  const requested=Boolean(window.empathTutorialRequested);
  const steps=[
    {title:'Choose your everyday places',target:'#categories',body:'Choose the destination types that matter to you, such as groceries, pharmacies, parks or places of worship. You can select more than one. The groceries, pharmacy and park button restores the starting selection.',tip:'Changing these choices updates the area colors and suggested areas.'},
    {title:'Choose a starting area',target:'#address-form',body:'Select an area on the map, choose a suggested area from the sidebar, or enter a Plano street address and press Find. Walking routes appear automatically for your selected places.',tip:'Routes begin at a neighborhood reference point. Check your actual entrance before walking.'},
    {title:'Read the area colors',target:'#legend',body:'Blue areas have lower average walking effort to your selected places. Red areas have higher effort. Gray means route data is incomplete for at least one selected place.',tip:'Colors compare the current selection. Ordinary walking time is shown separately on each route card.'},
    {title:'Inspect a walking route',target:'#route-panel',body:'Scroll to the walking route cards beneath Areas to explore. Each card names a destination and shows distance, ordinary walking time and walking effort. Select a destination card to focus on that walk.',tip:'Use Show all selected routes to bring the routes back together.'},
    {title:'Remove or restore paths',target:'#route-instructions',body:'Use Remove route on a destination card to hide one path. Clear routes on the map hides every path while keeping your location selected. Show route or Show routes restores them.',tip:'Clear location removes the selected point and its routes so you can start again.'},
    {title:'Compare context and share',target:'.leaflet-top.leaflet-right',body:'Open Population & housing context to compare population or housing estimates with the walking map. Use Share this view in the sidebar to copy a link containing your selected places and area.',tip:'You can reopen this tutorial at any time using the Tutorial button on the map.'}
  ];
  let initialized=false,dialog,body,title,description,kicker,footer,view='',step=0,opener=null,highlighted=null,methodologyPromise=null,methodRequest=0;
  function seen(){try{return localStorage.getItem(storageKey)==='done';}catch{return false;}}
  function remember(){try{localStorage.setItem(storageKey,'done');}catch{}}
  function clearHighlight(){if(highlighted){highlighted.classList.remove('map-tour-highlight');highlighted=null;}}
  function button(label,action,primary=false){
    const el=document.createElement('button');el.type='button';el.textContent=label;
    if(primary)el.className='map-help-primary';el.onclick=action;return el;
  }
  function frame(nextView,heading,subheading){
    clearHighlight();
    if(!dialog.open)opener=document.activeElement;
    view=nextView;dialog.dataset.view=nextView;
    title.textContent=heading;description.textContent=subheading;
    kicker.textContent=nextView==='methodology'?'Behind the map':'Plano · Get started';
    body.replaceChildren();footer.replaceChildren();footer.hidden=true;body.scrollTop=0;
    if(!dialog.open)dialog.showModal();
  }
  function dismiss(){if(view!=='methodology')remember();clearHighlight();}
  function close(){dismiss();dialog.close();}
  function welcome(){
    frame('welcome','Welcome to EmPath','Explore the places you can reach on foot.');
    const intro=document.createElement('p');
    intro.textContent='EmPath helps you compare walking access across Plano, find everyday destinations and inspect the routes behind the map. Choose a walkthrough or start exploring.';
    const actions=document.createElement('div');actions.className='map-help-actions';
    actions.append(button('Start the short tutorial',()=>tour(0),true),button('Open the screen reader walkthrough',textWalkthrough),button('Skip and explore the map',close));
    body.append(intro,actions);
    actions.querySelector('button').focus();
  }
  function tour(index){
    step=index;
    const current=steps[step];
    frame('tour',current.title,'Step '+(step+1)+' of '+steps.length);
    const progress=document.createElement('progress');progress.max=steps.length;progress.value=step+1;progress.className='map-help-progress';progress.setAttribute('aria-label','Tutorial progress');
    const paragraph=document.createElement('p');paragraph.textContent=current.body;
    const tip=document.createElement('p');tip.className='map-help-tip';tip.textContent=current.tip;
    body.append(progress,paragraph,tip);
    footer.hidden=false;
    const back=button('Back',()=>tour(step-1));back.disabled=step===0;
    footer.append(back,button(step===steps.length-1?'Start exploring':'Next',()=>step===steps.length-1?close():tour(step+1),true));
    highlighted=document.querySelector(current.target);
    if(highlighted){highlighted.classList.add('map-tour-highlight');if(highlighted.closest('aside'))highlighted.scrollIntoView({block:'center'});}
    title.focus({preventScroll:true});
  }
  function textWalkthrough(){
    frame('walkthrough','Screen reader walkthrough','Use the sidebar to explore without clicking the map.');
    const intro=document.createElement('p');intro.textContent='Close this walkthrough when you are ready to use the controls. Tab moves forward, Shift + Tab moves back, Space changes a checkbox, and Enter activates a button.';
    const list=document.createElement('ol');
    for(const text of [
      'Choose destination types in What do you want nearby? Each choice is a labeled checkbox.',
      'To look up an address, use the labeled address field and Find button. You can also go to Areas to explore and activate one of the suggested area buttons. Those buttons provide an alternative to clicking the visual map.',
      'The area summary announces how many areas have route data for your selection. Suggested area buttons name their location and average walking effort.',
      'After selecting an area, use the destination buttons in its walking route cards. Distance, walking time and effort are provided as text beside each button.',
      'Remove route hides one path. Clear routes hides all paths; the selected location stays in place. Show route or Show routes restores paths. Route visibility is announced as a count.',
      'Clear location resets the selected area and its routes. Your destination choices remain available.',
      'Share this view copies an area-and-destination link. Open Tutorial to revisit these instructions. Escape closes any help dialog.'
    ]){const item=document.createElement('li');item.textContent=text;list.appendChild(item);}
    body.append(intro,list);footer.hidden=false;
    footer.append(button('Back to welcome',welcome),button('Explore the map',close,true));
    title.focus({preventScroll:true});
  }
  async function methodology(){
    const request=++methodRequest;
    frame('methodology','Methodology','Data, techniques, algorithms and limits of the current Plano map.');
    const loading=document.createElement('p');loading.setAttribute('role','status');loading.textContent='Loading methodology…';body.appendChild(loading);
    footer.hidden=false;
    const note=document.createElement('p');note.textContent='Technical detail is kept in this optional map panel.';
    footer.append(note,button('Back to the map',close,true));
    title.focus({preventScroll:true});
    try{
      if(!methodologyPromise)methodologyPromise=fetch('map-methodology.html').then(response=>{if(!response.ok)throw Error('Methodology unavailable');return response.text();}).catch(error=>{methodologyPromise=null;throw error;});
      const html=await methodologyPromise;
      if(request!==methodRequest||!dialog.open||view!=='methodology')return;
      body.innerHTML=html;
    }catch{
      if(request!==methodRequest||!dialog.open||view!=='methodology')return;
      body.replaceChildren();const error=document.createElement('p');error.className='map-help-error';error.textContent='Methodology could not load. Check your connection and try again.';
      body.append(error,button('Try again',methodology));
    }
  }
  function init(){
    const c=window.empathContext;
    if(initialized||!c||!window.empathSelection)return;
    initialized=true;
    dialog=document.createElement('dialog');dialog.id='map-help-dialog';dialog.className='map-help-dialog';dialog.setAttribute('aria-labelledby','map-help-title');dialog.setAttribute('aria-describedby','map-help-description');
    dialog.innerHTML='<header class="map-help-header"><p class="map-help-kicker"></p><h2 id="map-help-title" tabindex="-1"></h2><p id="map-help-description"></p><button type="button" class="map-help-close" aria-label="Close help">×</button></header><div class="map-help-body"></div><footer class="map-help-footer" hidden></footer>';
    document.body.appendChild(dialog);
    title=dialog.querySelector('h2');description=dialog.querySelector('#map-help-description');kicker=dialog.querySelector('.map-help-kicker');body=dialog.querySelector('.map-help-body');footer=dialog.querySelector('.map-help-footer');
    dialog.querySelector('.map-help-close').onclick=close;
    dialog.addEventListener('cancel',dismiss);
    dialog.addEventListener('close',()=>{if(dialog.open)return;dismiss();const target=opener?.isConnected&&opener!==document.body?opener:document.getElementById('map-tutorial');if(typeof target?.focus==='function')target.focus({preventScroll:true});});
    body.addEventListener('click',event=>{const link=event.target.closest('a[href^="#method-"]');if(link){const target=body.querySelector(link.getAttribute('href'));if(target){event.preventDefault();target.scrollIntoView({block:'start'});}}});
    const control=L.control({position:'topright'});
    control.onAdd=()=>{
      const container=L.DomUtil.create('div','map-help-control');
      const tutorial=button('Tutorial',welcome);tutorial.id='map-tutorial';
      const method=button('Methodology',methodology);method.id='map-methodology';
      container.append(tutorial,method);L.DomEvent.disableClickPropagation(container);L.DomEvent.disableScrollPropagation(container);return container;
    };
    control.addTo(c.map);
    for(const [id,action]of [['replay-tutorial',welcome],['open-methodology',methodology]]){const el=document.getElementById(id);if(el){el.disabled=false;el.onclick=action;}}
    window.empathHelp={openWelcome:welcome,openTutorial:()=>tour(0),openTextWalkthrough:textWalkthrough,openMethodology:methodology,close};
    if(c.publicMode&&(requested||!seen()))welcome();
  }
  window.addEventListener('empath-selection-changed',init);
  init();
})();
