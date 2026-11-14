/* Shared route statistics: retain the existing comparison calculations and add a complete map card. */
(()=>{
  const benefits=window.empathBenefits;if(!benefits)return;
  const originalMetrics=benefits.metrics,originalSummary=benefits.summary,originalClear=benefits.clearMap;
  const escape=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  function metrics(graph,path){
    const base=originalMetrics(graph,path),edges=path.indices.map(i=>graph.edges[i]);
    const weighted=(field,transform=value=>value)=>{let sum=0,known=0;for(const edge of edges){const value=transform(edge[field]);if(Number.isFinite(value)&&edge[4]>0){sum+=edge[4]*value;known+=edge[4];}}return known?100*sum/known:null;};
    const seen=new Set();let repeated=0;for(const edge of edges){const key=[edge[0],edge[1]].sort((a,b)=>a-b).join(':');if(seen.has(key))repeated+=edge[4];seen.add(key);}
    return{...base,busy:weighted(8),treeSampleCoverage:weighted(14),pathPercent:weighted(7,value=>typeof value==='boolean'?Number(value):null),retracePercent:base.length?100*repeated/base.length:null,effortMultiplier:base.minutes?base.cost/base.minutes:null};
  }
  benefits.metrics=metrics;
  benefits.summary=(graph,least,quickest)=>({...originalSummary(graph,least,quickest),least:metrics(graph,least),quickest:metrics(graph,quickest)});
  let control=null,owner=null;
  const originalShow=benefits.showOnMap;
  function clearMap(context,onlyOwner){if(onlyOwner&&owner!==onlyOwner)return;if(control){context.map.removeControl(control);control=null;}owner=null;originalClear(context);}
  const icon=paths=>'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+paths+'</svg>';
  const icons={tree:icon('<path d="M20 3C8 1 2 7 5 14s15 4 15-11ZM4 21 16 8"/>'),heat:icon('<path d="M10 14V5a2 2 0 0 1 4 0v9a4 4 0 1 1-4 0Z"/><path d="M12 10v8m6-12h3m-3 5h2"/>'),traffic:icon('<path d="m4 10 2-6h12l2 6v9h-3v-3H7v3H4Zm0 0h16M7 13h2m6 0h2"/>'),road:icon('<path d="M6 2 3 22M18 2l3 20M12 3v4m0 3v4m0 3v4"/>'),path:icon('<path d="M4 21 12 3l8 18M9 15h6M7 20h10"/>'),data:icon('<path d="M4 4h16v16H4Zm5 0v16m6-16v16M4 9h16M4 15h16"/>'),repeat:icon('<path d="M4 7h13l-3-3m3 3-3 3M20 17H7l3 3m-3-3 3-3M4 7v7m16-7v10"/>'),effort:icon('<path d="M5 20v-6m7 6V9m7 11V4"/>')};
  const formatted=(value,digits=0,unit='')=>Number.isFinite(value)?Number(value).toFixed(digits)+unit:'Not available';
  function showWalkOnMap(context,stats,label,options={}){
    clearMap(context);owner=options.owner||'planned';control=L.control({position:'topright'});
    const item=(name,value,symbol,title)=>'<div title="'+escape(title)+'"><dt>'+icons[symbol]+'<span>'+name+'</span></dt><dd>'+escape(value)+'</dd></div>';
    control.onAdd=()=>{
      const element=L.DomUtil.create('section','route-summary-card');element.setAttribute('role','region');element.setAttribute('aria-label','Selected walking route summary');
      const comparison=options.comparison;
      element.innerHTML='<header class="route-summary-header"><div><p>Selected route</p><h3>Walking summary</h3></div><button type="button" aria-label="Close route summary">×</button></header><div class="route-summary-body"><dl class="route-summary-primary"><div><dt>Walking time</dt><dd>'+formatted(stats.minutes,1,' min')+'</dd></div><div><dt>Distance</dt><dd>'+formatted(stats.length/1609.344,2,' mi')+'</dd></div></dl>'+(comparison?'<div class="route-summary-comparison"><strong>'+escape(benefits.headline(comparison))+'</strong><span>'+(comparison.same?'Both methods choose this route.':formatted(Math.abs(comparison.extraMinutes),1)+(comparison.extraMinutes>=0?' extra':' fewer')+' walking minutes than the shortest walk.')+'</span></div>':'')+'<dl class="route-summary-metrics">'+item('Tree cover',formatted(stats.tree,1,'%'),'tree','Length-weighted predicted tree cover beside the walking path.')+item('Heat exposure',formatted(stats.heat,1,' / 100'),'heat','Surface-heat context index, not current weather or air temperature.')+item('Traffic exposure',formatted(stats.traffic,1,' / 100'),'traffic','Length-weighted traffic context index, not a safety rating.')+item('Near busy roads',formatted(stats.busy,1,'%'),'road','Share within 30 meters of roads with mapped daily traffic of at least 25,000 vehicles.')+item('Mapped paths',formatted(stats.pathPercent,1,'%'),'path','Share tagged as mapped paths or footways; continuous pedestrian access is not verified.')+item('Tree data coverage',formatted(stats.treeSampleCoverage,1,'%'),'data','Tree-raster sampling coverage; other tree estimates may use block context.')+item('Repeated paths',formatted(stats.retracePercent,1,'%'),'repeat','Distance walked again as a share of the whole route.')+item('Effort multiplier',formatted(stats.effortMultiplier,2,'×'),'effort','Modeled effort divided by ordinary walking time.')+'</dl><p class="route-summary-note">Nearby trees are a shade proxy. Heat and traffic use context indices, not live conditions. Environmental averages are weighted by route length.</p></div>';
      element.querySelector('button').onclick=()=>{clearMap(context);options.onClose?.();};
      const resize=()=>element.style.setProperty('--route-summary-max-height',Math.max(160,context.map.getSize().y-28)+'px');resize();context.map.on('resize',resize);control.onRemove=()=>context.map.off('resize',resize);
      L.DomEvent.disableClickPropagation(element);L.DomEvent.disableScrollPropagation(element);return element;
    };
    control.addTo(context.map);
  }
  benefits.showWalkOnMap=showWalkOnMap;
  // Planned A→B walks keep the compact comparison card; wandering walks use the full summary above.
  benefits.showOnMap=(context,comparison,label)=>{clearMap(context);originalShow(context,comparison,label);owner='planned';};
  benefits.clearMap=clearMap;
  benefits.summaryOwner=()=>owner;
})();
