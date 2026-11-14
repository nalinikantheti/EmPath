/* Illustrated directions only. This guide never writes to the map or its inputs. */
(async()=>{
  for(let i=0;i<400&&!window.empathGuided;i++)await new Promise(resolve=>setTimeout(resolve,100));
  if(!window.empathContext?.publicMode||!window.empathGuided)return;
  const trigger=document.getElementById('guided-help');
  const icon=paths=>'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'+paths+'</svg>';
  const placeIcon=icon('<path d="M18 10c0 5-6 11-6 11S6 15 6 10a6 6 0 1 1 12 0Z"/><circle cx="12" cy="10" r="2"/>');
  const walkIcon=icon('<circle cx="5" cy="18" r="2"/><circle cx="19" cy="6" r="2"/><path d="M5 16v-5h8V6h4M7 18h12v-5"/>');
  const guides={
    nearby:{name:'Find nearby places',description:'Choose what you need nearby, then explore walks from an area.',icon:placeIcon,steps:[
      {title:'Choose the places you need',action:'Open <strong>Compare areas</strong>. Select the places you want nearby. For this example, choose <strong>Groceries</strong>, <strong>Pharmacies</strong> and <strong>Parks</strong>.',result:'Your selected places have check marks. The map compares walking access to those types of places.',image:'choose-places',height:200,alt:'Example destination tiles: Groceries, Pharmacies and Parks are checked; Banks, Hospitals and Libraries are unchecked.'},
      {title:'Find your starting area',action:'In <strong>Address (optional)</strong>, enter the example address below. Then choose <strong>Find</strong>.',address:{name:'Harrington Library',text:'1501 18th St, Plano, TX 75074'},result:'The map selects the area around the address. Results list a mapped destination for each type of place you chose.',image:'find-address',height:90,alt:'Example address field filled with Harrington Library’s address. The field and Find button have orange outlines.',note:'No address in mind? Choose See results, then choose a suggested area or a colored area on the map.'},
      {title:'Show or hide a walking path',action:'In the results, check the box beside a destination to show its walking path. Uncheck the same box to hide it.',result:'The path appears or disappears on the map. The destination card also shows its distance and estimated walking time.',image:'show-path',height:162,alt:'Example result for Green Vine Market, with its checked route box highlighted. The card shows 0.46 miles and 10 minutes walking.'},
      {title:'Choose a different area',action:'To start somewhere else, choose <strong>Change area</strong>. Then enter another address or select another area.',result:'The previous location and its paths are cleared. Your place choices stay selected.',image:'change-area',height:83,alt:'The selected-area summary, with the Change area button outlined in orange.',note:'Address searches select a Census area. Its walking paths start at an area reference point, rather than an exact doorstep.'}
    ]},
    walk:{name:'Plan a walk',description:'Choose a start and destination, then compare the walking routes.',icon:walkIcon,steps:[
      {title:'Open Plan a walk',action:'Choose the <strong>Plan a walk</strong> tab at the top of the controls panel.',result:'You will see two address fields: From for your start, and To for your destination.',image:'plan-tab',height:68,alt:'The Compare areas and Plan a walk tabs, with Plan a walk selected and outlined in orange.'},
      {title:'Enter your starting address',action:'In <strong>From</strong>, enter the example starting address below.',address:{name:'Harrington Library',text:'1501 18th St, Plano, TX 75074'},result:'The From field contains your starting address. You still need to choose where you are going.',image:'walk-from',height:85,alt:'The From field containing Harrington Library’s address, outlined in orange.'},
      {title:'Choose where you are going',action:'In <strong>To</strong>, enter the example destination below. Then choose <strong>Find my walk</strong>.',address:{name:'Haggard Park',text:'901 E 15th St, Plano, TX 75074'},result:'A walking route appears on the map, with its estimated time and distance in the results.',image:'walk-to',height:185,alt:'The To field containing Haggard Park’s address and the Find my walk button, both outlined in orange.'},
      {title:'Compare the routes',action:'Use the <strong>Show shortest walk</strong> checkbox to show or hide the purple dashed route. Compare the estimated walking times in the results.',result:'Solid teal is the EmPath route, which weighs tree cover, heat and traffic. Purple dashed is the shortest walk. The two routes may follow the same path.',image:'compare-walks',height:86,alt:'The checked Show shortest walk checkbox is highlighted, with the teal and purple route explanation below it.',routeKey:true,note:'Walking time estimates how long the walk takes. Walking effort is a separate comparison score that includes environmental conditions.'}
    ]}
  };
  const dialog=document.createElement('dialog');dialog.id='tool-help-dialog';dialog.className='tool-help';
  dialog.setAttribute('aria-labelledby','tool-help-title');
  dialog.innerHTML=`<header class="tool-help-header"><div><p>EmPath · Map guide</p><button class="tool-help-close" type="button">${icon('<path d="m6 6 12 12M18 6 6 18"/>')}Close</button></div><h2 id="tool-help-title" tabindex="-1">How to use this map</h2></header><div class="tool-help-body"></div><footer class="tool-help-footer"><button class="tool-help-back" type="button">Back</button><span id="tool-help-progress" role="status" aria-live="polite" aria-atomic="true"></span><button class="tool-help-next" type="button">Next</button></footer>`;
  document.body.append(dialog);
  const body=dialog.querySelector('.tool-help-body'),back=dialog.querySelector('.tool-help-back'),next=dialog.querySelector('.tool-help-next'),progress=dialog.querySelector('#tool-help-progress');
  let guide=null,index=0,opener=trigger;
  function tips(){return`<details class="tool-help-tips"><summary>Extra tips: keyboard, screen readers &amp; layout</summary><div><h4>Keyboard and screen readers</h4><p>Tab moves forward and Shift + Tab moves back. Space changes a checkbox. Enter activates a button. Escape closes this guide. The address fields and result cards have text labels, so you can use them without clicking the map.</p><h4>More room for the controls</h4><p>On desktop, drag the divider between the controls and map. With a keyboard, focus the divider and use Left or Right Arrow; Enter resets its width.</p><h4>Using a phone</h4><p>Use <strong>Show map</strong> and <strong>Back to controls</strong> to move around. Choose <strong>Move map</strong> to pan the map, then <strong>Done</strong> to scroll the page again.</p><h4>Other sections</h4><p>The numbered links at the top open Story, Tool, Method, Maps and Ideas.</p></div></details>`;}
  function resetScroll(){body.scrollTop=0;}
  function menu(focus=true){
    guide=null;index=0;dialog.dataset.view='menu';back.hidden=true;progress.textContent='';next.textContent='Close';
    body.innerHTML=`<p id="tool-help-intro">What would you like to do? Choose a guide, read the steps, then try them on your map.</p><div class="tool-help-choices">${Object.entries(guides).map(([key,item])=>`<button class="tool-help-choice" type="button" data-guide="${key}"><span class="tool-help-choice-icon">${item.icon}</span><span><strong>${item.name}</strong><span>${item.description}</span><small>${item.steps.length} short steps</small></span><span class="tool-help-choice-arrow" aria-hidden="true">→</span></button>`).join('')}</div><p class="tool-help-example-note">Examples use Harrington Library and Haggard Park in Plano.</p>${tips()}`;
    dialog.setAttribute('aria-describedby','tool-help-intro');
    body.querySelectorAll('[data-guide]').forEach(button=>button.onclick=()=>{guide=button.dataset.guide;index=0;renderStep();});
    resetScroll();if(focus)document.getElementById('tool-help-title').focus({preventScroll:true});
  }
  function renderStep(){
    const item=guides[guide],step=item.steps[index];dialog.dataset.view='step';back.hidden=false;next.textContent=index===item.steps.length-1?'Done':'Next';progress.textContent='Step '+(index+1)+' of '+item.steps.length;
    body.innerHTML=`<div class="tool-help-step-top"><p>${item.name}</p><button class="tool-help-change" type="button">Choose another guide</button></div><h3 id="tool-help-step-title" tabindex="-1" aria-describedby="tool-help-progress">${step.title}</h3><p class="tool-help-action">${step.action}</p>${step.address?`<div class="tool-help-address"><strong>${step.address.name}</strong><span>${step.address.text}</span></div>`:''}<figure class="tool-help-figure"><figcaption>Example controls · orange outlines show where to look</figcaption><img src="assets/how-to/${step.image}.png" width="370" height="${step.height}" alt="${step.alt}" decoding="async"></figure>${step.routeKey?'<div class="tool-help-route-key" aria-hidden="true"><span><i></i>EmPath route</span><span><i></i>Shortest walk</span></div>':''}<div class="tool-help-result"><h4>What you’ll see</h4><p>${step.result}</p></div>${step.note?`<p class="tool-help-note">${step.note}</p>`:''}${tips()}`;
    dialog.removeAttribute('aria-describedby');body.querySelector('.tool-help-change').onclick=()=>menu();
    resetScroll();document.getElementById('tool-help-step-title').focus({preventScroll:true});
  }
  function open(){
    if(dialog.open)return;
    const methodology=document.getElementById('guided-dialog');if(methodology?.open)methodology.close();
    opener=document.activeElement;menu(false);dialog.showModal();resetScroll();document.getElementById('tool-help-title').focus({preventScroll:true});
  }
  function close(){dialog.close();}
  back.onclick=()=>{if(index>0){index--;renderStep();}else menu();};
  next.onclick=()=>{if(!guide||index===guides[guide].steps.length-1)close();else{index++;renderStep();}};
  dialog.querySelector('.tool-help-close').onclick=close;
  dialog.addEventListener('keydown',event=>{if(event.key==='Escape')event.stopPropagation();});
  dialog.addEventListener('close',()=>{const target=opener?.isConnected&&opener!==document.body?opener:trigger;target.focus({preventScroll:true});});
  trigger.setAttribute('aria-controls',dialog.id);trigger.onclick=open;
  window.empathTutorial={open,close,get state(){return{view:dialog.open?(guide?'step':'menu'):'closed',guide,index};}};
})();
