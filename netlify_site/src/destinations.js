/* Shared destination symbols and a map layer for every selected mapped place. */
(()=>{
  const paths={
    supermarket:'<path d="M3 4h2l2 11h10l3-8H6"/><circle cx="9" cy="19" r="1"/><circle cx="17" cy="19" r="1"/>',
    pharmacy:'<path d="m8 16 8-8M7 17a4 4 0 0 1-1-6l5-5a4 4 0 1 1 6 6l-5 5a4 4 0 0 1-5 0Z"/>',
    park:'<path d="M12 3 6 11h3l-4 6h14l-4-6h3L12 3ZM12 17v4"/>',
    bank:'<path d="m3 8 9-5 9 5H3ZM5 10v8m5-8v8m4-8v8m5-8v8M3 21h18"/>',
    hospital:'<path d="M5 21V5h14v16M3 21h18M10 8h4m-2-2v4M9 21v-6h6v6"/>',
    library:'<path d="M3 5c4-1 7 0 9 2 2-2 5-3 9-2v14c-4-1-7 0-9 2-2-2-5-3-9-2V5Zm9 2v14"/>',
    church:'<path d="M12 2v7m-3-4h6m-9 8 6-5 6 5v8H6v-8Zm4 8v-5h4v5"/>',
    mosque:'<path d="M5 12c0-4 5-5 7-9 2 4 7 5 7 9M4 12h16M5 12v9h14v-9m-9 9v-5h4v5M2 8v13m20-13v13"/>',
    synagogue:'<path d="m12 3 8 14H4L12 3Zm0 18L4 7h16l-8 14Z"/>',
    temple:'<path d="M12 2 8 7h8l-4-5ZM7 11l5-4 5 4H7Zm-2 4 7-4 7 4H5Zm2 0v6m10-6v6M4 21h16m-10 0v-4h4v4"/>',
    other_worship:'<path d="m3 11 9-7 9 7M5 10v11h14V10m-9 11v-6h4v6"/><circle cx="12" cy="10" r="1"/>',
    beauty_supply:'<path d="M7 21h10V10H7v11Zm2-11V5l6-3v8M7 15h10"/>',
    cosmetics:'<path d="m12 2 2 6 6 2-6 2-2 6-2-6-6-2 6-2 2-6Zm7 13 1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3Z"/>',
    gym:'<path d="M3 9v6m3-9v12m0-6h12m0-6v12m3-9v6"/>',
    recreation_centre:'<path d="m3 10 9-7 9 7M5 9v12h14V9m-9 12v-6h4v6M9 10h6"/>',
    swimming_pool:'<path d="M3 20c3-3 5 3 9 0s6 3 9 0M3 16c3-3 5 3 9 0s6 3 9 0M7 14V5a2 2 0 0 1 4 0m3 9V5a2 2 0 0 1 4 0M7 8h7m-7 4h7"/>',
    sports_centre:'<circle cx="12" cy="12" r="9"/><path d="m12 7 5 4-2 6H9l-2-6 5-4Zm0-4v4m9 2-4 2m1 9-3-3m-9 3 3-3M3 9l4 2"/>',
    bus_station:'<rect x="5" y="3" width="14" height="16" rx="3"/><path d="M5 11h14M8 19v2m8-2v2M8 6h8"/><circle cx="8" cy="15" r="1"/><circle cx="16" cy="15" r="1"/>',
    station:'<rect x="6" y="2" width="12" height="16" rx="3"/><path d="M6 10h12M9 18l-3 4m9-4 3 4M8 21h8m-6-16h4"/><circle cx="9" cy="14" r="1"/><circle cx="15" cy="14" r="1"/>',
    community_centre:'<circle cx="12" cy="6" r="3"/><circle cx="4" cy="10" r="2"/><circle cx="20" cy="10" r="2"/><path d="M7 21v-5a5 5 0 0 1 10 0v5M1 20v-4a3 3 0 0 1 4-3m14 0a3 3 0 0 1 4 3v4"/>',
    convenience:'<path d="M4 9h16v12H4V9Zm-1 0 2-6h14l2 6M8 21v-7h5v7m3-7h1"/>',
    clinic:'<path d="M4 21V5h16v16M2 21h20M9 10h6m-3-3v6m-3 8v-5h6v5"/>',
    school:'<path d="m3 9 9-6 9 6M5 8v13h14V8m-9 13v-6h4v6M8 11h1m6 0h1"/>',
    college:'<path d="m2 8 10-5 10 5-10 5L2 8Zm4 3v6c4 3 8 3 12 0v-6m4-3v8"/>',
    playground:'<path d="M3 21 7 4h10l4 17M7 4l5 17M9 9h7m-5 6h4M16 4v9m-2 0h4"/>',
    place:'<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 0 1 14 0Z"/><circle cx="12" cy="10" r="2"/>'
  };
  const aliases={hindu_temple:'temple',buddhist_temple:'temple',gurdwara:'temple'};
  const colors={supermarket:'#a45d2c',pharmacy:'#167979',park:'#377442',bank:'#3a6698',hospital:'#ad4c62',library:'#765c97',church:'#8a648d',mosque:'#7b689a',synagogue:'#6b6799',hindu_temple:'#9b6b34',buddhist_temple:'#9b6b34',gurdwara:'#9b6b34',other_worship:'#816889',beauty_supply:'#a45d7c',cosmetics:'#a45d7c',gym:'#936242',recreation_centre:'#497e65',swimming_pool:'#367c9a',sports_centre:'#4e7e66',bus_station:'#536e97',station:'#536e97',community_centre:'#8a6650',convenience:'#9c6c36',clinic:'#a5566b',school:'#6d679c',college:'#6d679c',playground:'#65823e'};
  const escape=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const symbol=category=>'<svg viewBox="0 0 24 24" aria-hidden="true">'+(paths[aliases[category]||category]||paths.place)+'</svg>';
  function icon(category,{count=1,large=false}={}){
    const size=large?34:28;
    return L.divIcon({className:'destination-pin'+(large?' destination-pin-large':''),html:'<span class="destination-pin-face" data-category="'+escape(category)+'" style="--pin-color:'+(colors[category]||'#60755a')+'">'+symbol(category)+(count>1?'<span class="destination-pin-count">'+count+'</span>':'')+'</span>',iconSize:[size,size+6],iconAnchor:[size/2,size+6],popupAnchor:[0,-size-4],tooltipAnchor:[0,-size]});
  }
  window.EmPathDestinations={symbol,icon,color:category=>colors[category]||'#60755a'};
  (async()=>{
    for(let i=0;i<400&&(!window.empathGuided||!window.empathContextTools);i++)await new Promise(resolve=>setTimeout(resolve,100));
    const c=window.empathContext;if(!c?.publicMode||!window.empathGuided)return;
    try{
      const data=await window.empathContextTools.dataset('master_pois');
      const layer=L.layerGroup().addTo(c.map),byId=new Map(data.features.map(f=>[f.properties.poi_id,f]));
      let enabled=true,timer=0;
      const control=document.createElement('label');control.className='guided-pin-toggle';control.innerHTML='<input type="checkbox" id="show-destination-pins" checked> Show destination pins';
      const key=document.createElement('p');key.className='guided-pin-note';key.textContent='Pin symbols identify places. A number groups nearby places of the same type; select it to explore.';
      document.getElementById('guided-options').append(control,key);
      control.querySelector('input').onchange=event=>{enabled=event.target.checked;render();};
      function render(){
        layer.clearLayers();
        const categories=new Set(window.empathSelection.categories),activeRoutes=new Set();
        if(window.empathMode==='area')for(const route of window.empathRouteState?.routes||[])if(window.empathRouteVisibility?.[route.category]?.route)activeRoutes.add(route.poiId);
        const selected=data.features.filter(f=>categories.has(f.properties.category));
        const visible=enabled&&window.empathMode==='area'&&!document.getElementById('context-layer')?.value;
        const zoom=c.map.getZoom(),groups=new Map(),cluster=zoom<15,cell=zoom<13?144:zoom<14?72:44;
        if(visible)for(const feature of selected){
          if(activeRoutes.has(feature.properties.poi_id))continue;
          const [lon,lat]=feature.geometry.coordinates;if(!Number.isFinite(lat)||!Number.isFinite(lon))continue;
          const point=c.map.project([lat,lon]),key=cluster?feature.properties.category+':'+Math.floor(point.x/cell)+':'+Math.floor(point.y/cell):feature.properties.poi_id;
          if(!groups.has(key))groups.set(key,[]);groups.get(key).push(feature);
        }
        for(const members of groups.values()){
          const category=members[0].properties.category,label=c.labels[category]||category;
          const lat=members.reduce((sum,f)=>sum+f.geometry.coordinates[1],0)/members.length,lon=members.reduce((sum,f)=>sum+f.geometry.coordinates[0],0)/members.length;
          const title=members.length>1?members.length+' '+label:members[0].properties.name||label;
          const marker=L.marker([lat,lon],{icon:icon(category,{count:members.length}),title,alt:title,keyboard:true,bubblingMouseEvents:false}).bindTooltip(escape(title));
          if(members.length>1){marker.on('click',()=>{const bounds=L.latLngBounds(members.map(f=>[f.geometry.coordinates[1],f.geometry.coordinates[0]]));c.map.fitBounds(bounds,{padding:[45,45],maxZoom:15});});}
          else{const p=members[0].properties;marker.bindPopup('<strong>'+escape(p.name||label)+'</strong><br>'+escape(label)+'<p class="destination-pin-popup-note">Mapped destination; check entrances and access locally.</p>');}
          marker.addTo(layer);
        }
        window.empathDestinationPins={ready:true,enabled,visible,places:visible?selected.length:0,markers:groups.size,byId,layer};
      }
      const schedule=()=>{clearTimeout(timer);timer=setTimeout(render,0);};
      for(const event of ['empath-selection-changed','empath-mode-changed','empath-route-selected','empath-area-cleared'])window.addEventListener(event,schedule);
      c.map.on('zoomend',schedule);
      document.addEventListener('change',event=>{if(event.target.matches('.show-destination-route,.show-destination-comparison,#context-layer,#score-model'))schedule();});
      document.addEventListener('empath-tutorial-layer-changed',schedule);
      render();
    }catch(error){console.warn('Destination pins unavailable:',error.message);}
  })();
})();
