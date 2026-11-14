/* Resource-constrained return-walk candidates, ranked by summed environmental friction. */
(function(root){
  'use strict';
  const prepared=new WeakMap(),MILE=1609.344,SPEED=1.2,LABEL_LIMIT=8,CANDIDATE_LIMIT=512;
  function push(heap,item){heap.push(item);let i=heap.length-1;while(i){const p=(i-1)>>1;if(heap[p][0]<=item[0])break;heap[i]=heap[p];i=p;}heap[i]=item;}
  function pop(heap){const first=heap[0],last=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let j=i*2+1;if(j+1<heap.length&&heap[j+1][0]<heap[j][0])j++;if(heap[j][0]>=last[0])break;heap[i]=heap[j];i=j;}heap[i]=last;}return first;}
  const pause=()=>new Promise(resolve=>setTimeout(resolve,0));
  function check(options){if(options.cancelled?.()){const error=new Error('Search cancelled.');error.name='AbortError';throw error;}}
  function index(graph){
    if(prepared.has(graph))return prepared.get(graph);
    const forward=graph.adj||new Map(),reverse=new Map();
    graph.edges.forEach((edge,i)=>{if(!graph.adj){if(!forward.has(edge[0]))forward.set(edge[0],[]);forward.get(edge[0]).push(i);}if(!reverse.has(edge[1]))reverse.set(edge[1],[]);reverse.get(edge[1]).push(i);});
    const value={forward,reverse};prepared.set(graph,value);return value;
  }
  async function labelsFrom(graph,start,limit,reverse,options){
    const adjacency=index(graph)[reverse?'reverse':'forward'],origin={node:start,distance:0,cost:0,previous:null,edge:null,active:true};
    const labels=new Map([[start,[origin]]]),queue=[[0,origin]];let visits=0;
    while(queue.length){
      const[,current]=pop(queue);if(!current.active)continue;
      for(const i of adjacency.get(current.node)||[]){
        const edge=graph.edges[i],distance=current.distance+edge[4],cost=current.cost+edge[3],node=edge[reverse?0:1];
        if(!(edge[4]>0)||!Number.isFinite(distance)||!Number.isFinite(cost)||edge[3]<0||distance>limit+1e-6)continue;
        let list=labels.get(node)||[];
        if(list.some(other=>other.distance<=distance+1e-7&&other.cost<=cost+1e-7))continue;
        const candidate={node,distance,cost,previous:current,edge:i,active:true};
        list=list.filter(other=>{if(distance<=other.distance+1e-7&&cost<=other.cost+1e-7){other.active=false;return false;}return true;});
        list.push(candidate);list.sort((a,b)=>a.cost-b.cost||a.distance-b.distance);
        if(list.length>LABEL_LIMIT){
          const shortest=list.reduce((best,item)=>item.distance<best.distance?item:best,list[0]);
          const retained=list.slice(0,LABEL_LIMIT);if(!retained.includes(shortest))retained[LABEL_LIMIT-1]=shortest;
          for(const item of list)if(!retained.includes(item))item.active=false;list=retained;
        }
        labels.set(node,list);if(candidate.active)push(queue,[cost,candidate]);
      }
      if(++visits%1000===0){check(options);await pause();}
    }check(options);return labels;
  }
  function trace(label,reverse=false){const result=[];while(label.previous){result.push(label.edge);label=label.previous;}return reverse?result:result.reverse();}
  function physical(edge){return edge[0]<edge[1]?edge[0]+':'+edge[1]:edge[1]+':'+edge[0];}
  async function find(graph,options){
    const{start,minutes,miles}=options;
    if(!graph.nodes.has(start))throw Error('Choose a starting point on the mapped walking network.');
    if(!Number.isFinite(minutes)||minutes<5||minutes>180)throw Error('Enter a walking time from 5 to 180 minutes.');
    if(!Number.isFinite(miles)||miles<.1||miles>20)throw Error('Enter a distance limit from 0.1 to 20 miles.');
    if(options.destination&&options.destination!=='return')throw Error('Enthusiast walks return to their starting point.');
    const lowerMinutes=Math.max(0,minutes-5),upperMinutes=minutes+5,minDistance=Math.max(1,lowerMinutes*60*SPEED),maxDistance=Math.min(upperMinutes*60*SPEED,miles*MILE);
    const bounds={lowerMinutes,upperMinutes,maxMiles:miles,minDistance,maxDistance};
    if(maxDistance+1e-6<minDistance)return{routes:[],bounds,reason:'distance-time-conflict',minimumMiles:minDistance/MILE};
    const outward=await labelsFrom(graph,start,maxDistance,false,options),back=await labelsFrom(graph,start,maxDistance,true,options),pool=[];
    const retain=candidate=>{if(pool.length===CANDIDATE_LIMIT&&candidate.cost>pool.at(-1).cost+1e-7)return;let lo=0,hi=pool.length;while(lo<hi){const mid=(lo+hi)>>1;if(pool[mid].cost<=candidate.cost)lo=mid+1;else hi=mid;}pool.splice(lo,0,candidate);if(pool.length>CANDIDATE_LIMIT)pool.pop();};
    for(let i=0;i<graph.edges.length;i++){
      if(i%3000===0){check(options);await pause();}
      const edge=graph.edges[i],a=outward.get(edge[0]),b=back.get(edge[1]);if(!a||!b||!(edge[4]>0)||!Number.isFinite(edge[3])||edge[3]<0)continue;
      for(const left of a)for(const right of b){const distance=left.distance+edge[4]+right.distance;if(distance<minDistance-1e-6||distance>maxDistance+1e-6)continue;retain({left,right,edge:i,distance,cost:left.cost+edge[3]+right.cost});}
    }
    const candidates=[],seen=new Set();
    for(const candidate of pool){
      check(options);const indices=[...trace(candidate.left),candidate.edge,...trace(candidate.right,true)],signature=indices.join(',');if(seen.has(signature))continue;seen.add(signature);
      let node=start,distance=0,frictionSeconds=0,repeated=0,valid=true;const edges=new Set();
      for(const i of indices){const edge=graph.edges[i];if(edge[0]!==node){valid=false;break;}node=edge[1];distance+=edge[4];frictionSeconds+=edge[3];const key=physical(edge);if(edges.has(key))repeated+=edge[4];edges.add(key);}
      if(!valid||node!==start||distance<minDistance-1e-5||distance>maxDistance+1e-5)continue;
      const retracedFraction=repeated/distance;
      candidates.push({indices,start,end:start,distance,miles:distance/MILE,walkSeconds:distance/SPEED,frictionSeconds,retracedFraction,kind:retracedFraction>.4?'out-and-back':retracedFraction>.05?'return-with-retracing':'loop',edges});
    }
    candidates.sort((a,b)=>a.frictionSeconds-b.frictionSeconds||Math.abs(a.walkSeconds/60-minutes)-Math.abs(b.walkSeconds/60-minutes)||a.retracedFraction-b.retracedFraction);
    const routes=[],geometries=new Set();
    for(const route of candidates){const geometry=[...route.edges].sort().join('|');if(geometries.has(geometry))continue;geometries.add(geometry);routes.push(route);if(routes.length===3)break;}
    return{routes:routes.map(({edges,...route})=>route),bounds,reason:routes.length?null:'no-connected-match',ranking:{objective:'summed_friction_seconds',labelsPerNode:LABEL_LIMIT,candidateLimit:CANDIDATE_LIMIT,globalOptimumGuaranteed:false}};
  }
  const api={find};root.EmPathWanderingCore=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
