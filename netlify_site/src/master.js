/* Topic-first presentation. Dataset values, route weights and display ranges are unchanged. */
(async()=>{
  const T=empathContextTools,E=T.esc,$=id=>document.getElementById(id);
  const fields={
    family_shade_min:{topic:'walking',label:'How hard is the walk?',copy:'Longer walks, fewer trees, more traffic and hotter ground add walking effort.',low:'Less effort',high:'More effort',unit:'effort',detail:'Average modeled effort to the nearest mapped destination in each available category. Equivalent minutes are a comparison measure, not actual walking time.'},
    family_time_min:{topic:'walking',label:'How long is the walk?',copy:'Compare the average walking time to everyday places, using distance only.',low:'Shorter walks',high:'Longer walks',unit:'minutes',detail:'Average walking time to the nearest mapped destination in each available category. These are separate trips, not one journey visiting all the places.'},
    family_rank_delta:{topic:'walking',label:'Friction Ranking Change',copy:'See which areas move up or down when we consider trees, heat and traffic alongside walking time.',low:'Moves up',high:'Moves down',unit:'rank',detail:'Change in cost percentile: modeled effort minus walking time only. Negative values improve the ranking; positive values worsen it. This is a comparison of rankings, not extra minutes.'},
    edge_tree_cover:{topic:'environment',label:'Trees beside walking paths',copy:'See which paths have more trees growing nearby.',low:'Fewer trees',high:'More trees',unit:'percent',detail:'AI-predicted trees in a 20 m-wide corridor beside each path, using 2022 aerial imagery. Nearby trees are a shade proxy, not a measurement of shade at a particular time.'},
    ai_canopy_cover_pct:{topic:'environment',label:'Trees in each area',copy:'See how much of each area is covered by predicted trees.',low:'Fewer trees',high:'More trees',unit:'percent',detail:'AI-estimated tree cover from 2022 NAIP aerial imagery, summarized for Census blocks. Predicted tree cover is not the same as measured shade.'},
    landsat_summer_surface_temp_c:{topic:'environment',label:'How hot is the ground?',copy:'Compare cooler and hotter ground during summer.',low:'Cooler ground',high:'Hotter ground',unit:'temperature',detail:'Summer 2025 Landsat surface temperature in degrees Celsius. This describes surfaces, not air temperature or today’s weather.'},
    traffic_index_0_100:{topic:'environment',label:'How busy are the roads?',copy:'See where nearby roads carry less or more traffic.',low:'Less traffic',high:'More traffic',unit:'traffic',detail:'Nearby mapped TxDOT traffic counts, expressed as a city-referenced index. It is a traffic-volume comparison, not a crash-risk score.'},
    population_density:{topic:'people',label:'People living close together',copy:'Compare how many people live in the same-sized space.',low:'Fewer people',high:'More people',unit:'density',detail:'2020 Census residents per square kilometer of land. Border fragments retain the population density of the original whole Census block.'},
    no_vehicle_pct:{topic:'people',label:'Homes with no car',copy:'See how many households have no vehicle available.',low:'Fewer without a car',high:'More without a car',unit:'householdPercent',detail:'Percentage of households with no vehicle available, from 2020–2024 ACS block-group estimates.'},
    age65_pct:{topic:'people',label:'People age 65 and older',copy:'See the share of residents who are 65 or older.',low:'Smaller share',high:'Larger share',unit:'peoplePercent',detail:'Percentage of residents aged 65 and older, from 2020–2024 ACS block-group estimates.'},
    disability_pct:{topic:'people',label:'People with disabilities',copy:'See the share of people with a reported disability.',low:'Smaller share',high:'Larger share',unit:'peoplePercent',detail:'2020–2024 ACS estimate for the civilian noninstitutionalized population. This layer uses Census tracts, not individual homes or blocks.'},
    median_gross_rent:{topic:'homes',label:'Rent each month',copy:'Compare the middle monthly rent for homes in each area.',low:'Lower rent',high:'Higher rent',unit:'rent',detail:'2020–2024 ACS median gross rent, including utilities, for a Census block group. This is an area estimate, not a current listing.'},
    median_home_value:{topic:'homes',label:'Home values',copy:'Compare the middle estimated home value in each area.',low:'Lower value',high:'Higher value',unit:'value',detail:'2020–2024 ACS median owner-reported home value for a Census block group. This is not a sale price, appraisal or value for a particular home.'},
    median_household_income:{topic:'homes',label:'Income each year',copy:'Compare the middle yearly income of households in each area.',low:'Lower income',high:'Higher income',unit:'income',detail:'2020–2024 ACS median household income for a Census block group. Household income includes more than wages alone.'}
  };
  // Only the seven formerly purple layers get new colors.
  const palettes={
    population_density:['#edf4fb','#91b9db','#205d91'],
    median_gross_rent:['#fff4d8','#e0bb66','#a66a24'],
    median_home_value:['#e7f4f1','#76b8b1','#226c69'],
    median_household_income:['#edf5e8','#98bf83','#3a783f'],
    no_vehicle_pct:['#edf0f3','#9caeba','#4d687d'],
    age65_pct:['#f8ede2','#ceaa83','#8b5c36'],
    disability_pct:['#edf5f1','#8fb8a7','#416f5e']
  };
  const menuLabels={
    family_shade_min:'Shade-priority access · all categories',
    family_time_min:'Walking time only · all categories',
    family_rank_delta:'Friction Ranking Change',
    edge_tree_cover:'GeoAI tree adjacency · walking paths',
    ai_canopy_cover_pct:'GeoAI canopy summary · census blocks',
    landsat_summer_surface_temp_c:'Summer surface temperature',
    traffic_index_0_100:'Traffic volume index',
    population_density:'Population density',
    median_gross_rent:'Area median rent',
    median_home_value:'Area median home value',
    median_household_income:'Household income',
    no_vehicle_pct:'Households without a vehicle',
    age65_pct:'Residents aged 65+',
    disability_pct:'Residents with a disability · tracts'
  };
  const select=$('master-theme'),remembered={walking:'family_shade_min',environment:'edge_tree_cover',people:'population_density',homes:'median_gross_rent'};
  let topic='walking',thematic=null,themeToken=0,treePromise=null,activeRange=[0,1];
  const requested=new URLSearchParams(location.search).get('theme');if(requested&&Object.hasOwn(fields,requested)){topic=fields[requested].topic;remembered[topic]=requested;}
  function chooseTopic(next){
    topic=next;select.replaceChildren();for(const [key,info]of Object.entries(fields))if(info.topic===topic)select.add(new Option(menuLabels[key]||info.label,key));select.value=remembered[topic];
    document.querySelectorAll('[data-topic]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.topic===topic)));
  }
  chooseTopic(topic);
  const map=L.map('master-map',{preferCanvas:true,scrollWheelZoom:!document.documentElement.classList.contains('master-embedded'),zoomSnap:.25});
  L.tileLayer('/.netlify/functions/basemap?z={z}&x={x}&y={y}',{attribution:'© OpenStreetMap contributors · © CARTO',maxNativeZoom:19,maxZoom:20}).addTo(map);
  map.createPane('borders').style.zIndex=430;
  const legendControl=L.control({position:'bottomleft'});legendControl.onAdd=()=>{const element=L.DomUtil.create('div','master-legend');element.id='master-legend';L.DomEvent.disableClickPropagation(element);return element;};legendControl.addTo(map);
  const [blocks,pop,bg,tr,boundary,meta]=await Promise.all([T.dataset('master_blocks'),T.dataset('population_blocks'),T.dataset('social_block_groups'),T.dataset('social_tracts'),fetch('data/plano_boundary.geojson').then(r=>r.json()),T.method()]);
  const byId=new Map(blocks.features.map(f=>[f.properties.GEOID20,f])),pBy=new Map(pop.features.map(f=>[f.properties.GEOID20,f.properties]));
  const outlines=L.geoJSON(boundary,{style:{color:'#172f28',weight:2.3,fill:false},interactive:false}).addTo(map);
  const borderLayer=L.geoJSON(blocks,{pane:'borders',style:{color:'#55675b',weight:.45,fill:false},interactive:false});
  function centerOf(geometry){let west=Infinity,east=-Infinity,south=Infinity,north=-Infinity;function scan(coords){if(typeof coords[0]==='number'){west=Math.min(west,coords[0]);east=Math.max(east,coords[0]);south=Math.min(south,coords[1]);north=Math.max(north,coords[1]);}else coords.forEach(scan);}scan(geometry.coordinates);return L.latLng((south+north)/2,(west+east)/2);}
  const candidates=blocks.features.filter(f=>Number(f.properties.HU100)>0&&Number.isFinite(f.properties.access_network_node)&&f.properties.access_snap_gap_m<=100).map(f=>({id:f.properties.GEOID20,group:pBy.get(f.properties.GEOID20)?.GEOID_BG,center:centerOf(f.geometry)}));
  function routeReference(feature,point){
    const p=feature.properties;if(p.GEOID20&&byId.has(p.GEOID20)&&Number.isFinite(byId.get(p.GEOID20).properties.access_network_node))return p.GEOID20;
    const area=p.GEOID_BG,list=candidates.filter(item=>area?.length===11?item.group?.slice(0,11)===area:item.group===area),choices=list.length?list:candidates;
    return choices.reduce((best,item)=>!best||point.distanceTo(item.center)<point.distanceTo(best.center)?item:best,null)?.id;
  }
  function color(field,value,lo,hi){
    if(value==null||!Number.isFinite(value))return '#d7dcda';const t=Math.max(0,Math.min(1,(value-lo)/(hi-lo||1)));
    if(palettes[field])return EmPathColors.blend(palettes[field],t);
    if(field==='family_rank_delta')return EmPathColors.change(t*100);
    if(field==='ai_canopy_cover_pct')return EmPathColors.tree(t);
    if(field==='landsat_summer_surface_temp_c')return EmPathColors.heat(t);
    if(field==='traffic_index_0_100')return EmPathColors.traffic(t);
    return EmPathColors.access(t*100);
  }
  const number=(value,digits=0)=>Number(value).toLocaleString(undefined,{maximumFractionDigits:digits});
  function valueText(field,value,short=false){
    if(value==null||!Number.isFinite(value))return 'No estimate available';const unit=fields[field].unit;
    if(unit==='effort'){const t=Math.max(0,Math.min(.999,(value-activeRange[0])/(activeRange[1]-activeRange[0]||1)));return ['Less effort','A bit less effort','In the middle','A bit more effort','More effort'][Math.floor(t*5)];}
    if(unit==='rank')return value<0?'Moves up':value>0?'Moves down':'No change';
    if(unit==='rent'||unit==='value'||unit==='income')return '$'+number(value)+(short?'':unit==='rent'?' / month':unit==='income'?' / year':'');
    if(unit==='householdPercent'||unit==='peoplePercent')return short?number(value,1)+'%':'About '+number(value)+' out of 100 '+(unit==='householdPercent'?'households':'people');
    if(unit==='minutes')return number(value,1)+' min';
    if(unit==='density')return number(value)+(short?'':' people / km²');
    if(unit==='temperature')return number(value,1)+' °C';
    if(unit==='traffic')return ['Less traffic','Some traffic','More traffic'][Math.min(2,Math.floor(Math.max(0,(value-activeRange[0])/(activeRange[1]-activeRange[0]||1))*3))];
    return number(value,1)+'%';
  }
  function popup(feature,field,point){
    const info=fields[field],p=feature.properties,value=p[field],reference=routeReference(feature,point),target=reference?'app.html?block='+encodeURIComponent(reference):'app.html';
    const technical=info.unit==='effort'?number(value,1)+' equivalent minutes':info.unit==='rank'?number(value,1)+' percentile points':info.unit==='traffic'?number(value,1)+' on the traffic index':valueText(field,value,true);
    const moeField=meta.fields[field]?.moe_field,moe=moeField&&p[moeField];
    return '<div class="master-popup"><p class="master-popup-kicker">'+E(info.label)+'</p><strong class="master-popup-value">'+E(valueText(field,value))+'</strong><p>'+E(info.copy)+'</p><details><summary>About this number</summary><p>'+E(value==null?'This area has no usable estimate.':technical)+'. '+E(info.detail)+(moe!=null?' 90% margin of error: ±'+E(number(moe,1))+'.':'')+'</p></details><a class="master-route-link" href="'+target+'" target="_top">See walks nearby →</a><small>Routes start at a mapped area reference point.</small></div>';
  }
  function showLegend(field,lo,hi){
    const info=fields[field],ramp=field==='edge_tree_cover'?t=>EmPathColors.tree(t):t=>color(field,lo+(hi-lo)*t,lo,hi);
    const range=['effort','rank','traffic'].includes(info.unit)?'':`<div class="master-legend-numbers"><span>${E(valueText(field,lo,true))}</span><span>${E(valueText(field,hi,true))}</span></div>`;
    const unit=info.unit==='density'?'People in each km²':info.unit==='rent'?'Per month':info.unit==='income'?'Per household, per year':info.unit==='minutes'?'Average walking minutes':'';
    $('master-legend').innerHTML='<strong>'+E(info.label)+'</strong><div class="ramp" style="background:linear-gradient(90deg,'+ramp(0)+','+ramp(.5)+','+ramp(1)+')"></div><div class="master-legend-ends"><span>'+E(info.low)+'</span><span>'+E(info.high)+'</span></div>'+range+(unit?'<div class="master-legend-unit">'+E(unit)+'</div>':'')+'<p class="master-missing"><i></i>Gray: no estimate</p>';
  }
  async function update(){
    map.closePopup();
    const field=select.value,info=fields[field],mine=++themeToken;remembered[info.topic]=field;select.title=menuLabels[field]||info.label;
    $('master-description').textContent=info.copy;$('master-explanation').textContent=info.detail;$('master-map').setAttribute('aria-busy','true');$('master-status').textContent='Loading '+info.label.toLowerCase()+'…';
    if(thematic){map.removeLayer(thematic);thematic=null;}
    try{
      if(field==='edge_tree_cover'){
        const data=await(treePromise||(treePromise=empathLoadGeo('data/ai_tree_paths.json.gz')));if(mine!==themeToken)return;
        const layer=L.featureGroup();let count=0;
        for(const [value,coverage,length,lines]of data.paths){
          L.polyline(lines.map(line=>line.map(([x,y])=>[y,x])),{weight:2,opacity:.95,color:value==null?'#aaa':EmPathColors.tree(value)}).bindPopup('<div class="master-popup"><p class="master-popup-kicker">Trees beside this path</p><strong class="master-popup-value">'+(value==null?'No estimate':Math.round(value*100)+'% nearby tree cover')+'</strong><p>Predicted trees beside this '+Math.round(length)+' m path. Nearby trees do not show exact shade.</p><a class="master-route-link" href="app.html?mode=route" target="_top">Plan a walk →</a></div>').addTo(layer);
          if(++count%6000===0){await new Promise(requestAnimationFrame);if(mine!==themeToken)return;}
        }
        thematic=layer.addTo(map);activeRange=[0,100];showLegend(field,0,100);
        window.empathMasterState={field,topic,features:data.paths.length,geometry:'walking_paths',scope:'Plano + 3 km routing context',housingIncluded:true,colors:[EmPathColors.tree(0),EmPathColors.tree(.5),EmPathColors.tree(1)]};
      }else{
        const data=field==='population_density'?pop:field==='disability_pct'?tr:palettes[field]&&field!=='population_density'?bg:blocks;
        let [lo,hi]=T.range(data,field);if(field==='family_rank_delta'){const limit=Math.max(Math.abs(lo),Math.abs(hi));lo=-limit;hi=limit;}activeRange=[lo,hi];
        thematic=L.geoJSON(data,{style:f=>({color:'#53685c',weight:.15,fillOpacity:.78,fillColor:color(field,f.properties[field],lo,hi)}),onEachFeature:(f,l)=>{let clicked;l.on('click',event=>clicked=event.latlng);l.bindPopup(()=>popup(f,field,clicked||l.getBounds().getCenter()),{maxWidth:330});}}).addTo(map);
        showLegend(field,lo,hi);window.empathMasterState={field,topic,features:data.features.length,scope:'Plano municipality',housingIncluded:true,range:[lo,hi],colors:[color(field,lo,lo,hi),color(field,(lo+hi)/2,lo,hi),color(field,hi,lo,hi)]};
      }
      outlines.bringToFront();window.empathMasterLayer=thematic;$('master-status').textContent='Choose an area or path to learn more.';
      const query=new URLSearchParams(location.search);query.set('theme',field);history.replaceState(null,'','?'+query);
    }catch(error){if(mine===themeToken)$('master-status').textContent='This map could not load. Choose another topic or try again.';}
    finally{if(mine===themeToken)$('master-map').setAttribute('aria-busy','false');}
  }
  select.onchange=update;document.querySelectorAll('[data-topic]').forEach(button=>button.onclick=()=>{chooseTopic(button.dataset.topic);update();});
  $('master-blocks').onchange=event=>event.target.checked?borderLayer.addTo(map):map.removeLayer(borderLayer);
  const fit=()=>map.fitBounds(outlines.getBounds(),{padding:[24,24]});$('master-fit').onclick=fit;
  window.empathMasterMap=map;await update();fit();
  const id=new URLSearchParams(location.search).get('block'),match=id&&byId.get(id);
  if(match){const highlight=L.geoJSON(match,{style:{color:'#101f19',weight:3,fill:false}}).addTo(map);map.fitBounds(highlight.getBounds(),{maxZoom:13});}
})().catch(()=>{document.getElementById('master-status').textContent='The map could not load. Please refresh to try again.';});
