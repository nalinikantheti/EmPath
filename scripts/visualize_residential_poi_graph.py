"""Visible activity-graph diagram and a standalone interactive weighted graph."""
from pathlib import Path
import json
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/residential_poi_graph'


def run():
    graphs = {name: nx.read_graphml(OUT / f'{name}_activity_graph.graphml') for name in ['shortest_time', 'lowest_friction']}
    nodes = [{**attrs, 'id': node} for node, attrs in graphs['shortest_time'].nodes(data=True)]
    payload = {'nodes': nodes, 'edges': {name: [{'source': u, 'target': v, **attrs} for u,v,attrs in g.edges(data=True)] for name,g in graphs.items()}}
    origins = [n['id'] for n in nodes if n['role']=='origin']
    # A reproducible readable subset; preserve all four origins, including isolated ones.
    sample = set()
    baseline = graphs['shortest_time']
    for origin in origins:
        sample.update(v for _,v,_ in sorted(baseline.out_edges(origin,data=True),key=lambda e:e[2]['weight'])[:3])
    destinations = sorted(sample, key=lambda n: baseline.nodes[n]['label'])
    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    origin_pos = {n: (0, y) for n,y in zip(origins,np.linspace(.85,.15,len(origins)))}
    dest_pos = {n: (1, y) for n,y in zip(destinations,np.linspace(.95,.05,len(destinations)))}
    for ax,(name,g) in zip(axes,graphs.items()):
        for u,v,d in g.edges(data=True):
            if v in dest_pos:
                x1,y1=origin_pos[u]; x2,y2=dest_pos[v]
                ax.plot([x1,x2],[y1,y2],color='#2474ad',alpha=.25,lw=1,zorder=1)
        for i,n in enumerate(origins,1):
            x,y=origin_pos[n]; ax.scatter(x,y,s=160,color='#ef8a24',edgecolor='white',zorder=3)
            ax.text(x-.04,y,f'R{i}',ha='right',va='center',weight='bold',fontsize=11)
            if g.out_degree(n)==0:ax.text(x+.03,y+.035,'No supported routes',fontsize=8,color='#a33')
        for i,n in enumerate(destinations,1):
            x,y=dest_pos[n];ax.scatter(x,y,s=55,color='#2474ad',zorder=3)
            label=g.nodes[n]['label']
            ax.text(x+.03,y,f'P{i}: {label[:34]}',va='center',fontsize=8)
        ax.set_xlim(-.15,1.85);ax.set_ylim(0,1);ax.axis('off')
        ax.set_title(('Shortest-distance routes' if name=='shortest_time' else 'Lowest-friction routes')+f'\n{g.number_of_edges()} connections in full graph',fontsize=14,pad=12)
    fig.suptitle('Residential origins → places of interest',fontsize=20,y=.98)
    fig.legend(handles=[Line2D([0],[0],marker='o',color='w',markerfacecolor='#ef8a24',markersize=10,label='Provisional residential origin'),Line2D([0],[0],marker='o',color='w',markerfacecolor='#2474ad',markersize=8,label='POI'),Line2D([0],[0],color='#2474ad',label='One retained minimum-cost walking route')],loc='lower center',bbox_to_anchor=(.5,.065),ncol=3,frameon=False)
    origin_labels='\n'.join(f'R{i}: {baseline.nodes[n]["label"]}' for i,n in enumerate(origins,1))
    fig.text(.05,.018,'Readable subset: three nearest POIs per origin, combined across origins. Full graph is in the interactive HTML.\nFriction gaps leave three origins isolated; missing inputs are not zero cost. Positions are schematic, not geographic.',fontsize=9)
    fig.tight_layout(rect=[0,.11,1,.94]);fig.savefig(OUT/'weighted_graph_overview.png',dpi=170);plt.close(fig)
    (OUT/'graph_node_key.txt').write_text(origin_labels)
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EmPath weighted graph</title>
<style>body{margin:0;padding:24px;font:15px system-ui;color:#182e3c;background:#f4f7fa}h1{margin:0 0 8px}.controls{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0}select{padding:8px;max-width:350px}#summary,#notice{padding:12px;background:white;border-radius:8px;margin:10px 0}#notice{border-left:4px solid #ef8a24}svg{background:white;border-radius:12px;width:100%;min-width:760px}.canvas{overflow:auto}#details{white-space:pre-line;background:white;padding:16px;border-radius:8px;min-height:65px}.edge:hover{stroke:#e36b11;stroke-width:4;opacity:1!important}.small{font-size:13px;color:#526979}</style>
<h1>Residential origins → places of interest</h1><div>Orange nodes are provisional residential origins; blue nodes are POIs. Each line represents one actual minimum-cost walking route, not a straight walking connection.</div>
<div class="controls"><label>Route objective<br><select id="objective"><option value="shortest_time">Shortest distance / time</option><option value="lowest_friction">Lowest assumed friction</option></select></label><label>Residential origin<br><select id="origin"></select></label><label>POIs shown<br><select id="limit"><option>12</option><option>25</option><option value="all">All 85</option></select></label></div>
<div id="summary"></div><div id="notice"></div><div class="canvas"><svg id="graph" role="img" aria-label="Residential to destination weighted graph"></svg></div><p class="small">Hover or click a line for its exact route weight and physical distance. Arrowheads point toward destinations. Schematic positions are not geographic. Gray POIs have no displayed connection.</p><div id="details">Select a line to inspect its weight.</div>
<script>const DATA=__DATA__;
const byId=Object.fromEntries(DATA.nodes.map(n=>[n.id,n]));const origins=DATA.nodes.filter(n=>n.role==='origin');const el=id=>document.getElementById(id);const svg=el('graph');const ns='http://www.w3.org/2000/svg';
function shape(tag,attrs,parent=svg){const node=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))node.setAttribute(k,v);parent.appendChild(node);return node}
function txt(x,y,value,attrs={}){const t=shape('text',{x,y,'font-size':13,fill:'#182e3c',...attrs});t.textContent=value;return t}
const all=document.createElement('option');all.value='all';all.textContent='All four origins';el('origin').appendChild(all);origins.forEach((n,i)=>{const o=document.createElement('option');o.value=n.id;o.textContent=`R${i+1}: ${n.label}`;el('origin').appendChild(o)});
function draw(){svg.replaceChildren();const objective=el('objective').value, selected=el('origin').value;const allEdges=DATA.edges[objective];const edges=allEdges.filter(e=>selected==='all'||e.source===selected);const score={};edges.forEach(e=>score[e.target]=Math.min(score[e.target]??Infinity,e.weight));const pois=DATA.nodes.filter(n=>n.role==='destination').sort((a,b)=>(score[a.id]??Infinity)-(score[b.id]??Infinity)||a.label.localeCompare(b.label));const shown=el('limit').value==='all'?pois:pois.slice(0,Number(el('limit').value));const activeOrigins=origins.filter(n=>selected==='all'||n.id===selected);const h=Math.max(530,shown.length*34+90),w=1150;svg.setAttribute('viewBox',`0 0 ${w} ${h}`);svg.setAttribute('height',h);const defs=shape('defs',{});const marker=shape('marker',{id:'arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:5,markerHeight:5,orient:'auto'},defs);shape('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#2474ad'},marker);const op={},dp={};activeOrigins.forEach((n,i)=>op[n.id]=[310,70+(h-140)*(i+1)/(activeOrigins.length+1)]);shown.forEach((n,i)=>dp[n.id]=[760,60+i*(h-120)/Math.max(1,shown.length-1)]);let count=0;
for(const e of edges){if(!dp[e.target])continue;count++;const [x1,y1]=op[e.source],[x2,y2]=dp[e.target];const line=shape('line',{x1:x1+10,y1,x2:x2-10,y2,stroke:'#2474ad','stroke-width':1.5,opacity:.35,'marker-end':'url(#arrow)',class:'edge',tabindex:0});const details=()=>{el('details').textContent=`${byId[e.source].label} → ${byId[e.target].label}\nDistance: ${e.distance_m.toFixed(0)} m · Network walking time: ${e.network_walk_minutes.toFixed(1)} min\nWeight: ${e.weight.toFixed(1)} ${objective==='lowest_friction'?'equivalent seconds (assumed environmental friction)':'seconds'}\nAccess, entrances and crossings are not verified; connector travel is excluded.`};line.addEventListener('mouseenter',details);line.addEventListener('click',details);line.addEventListener('focus',details);const t=shape('title',{},line);t.textContent=`${e.distance_m.toFixed(0)} m; weight ${e.weight.toFixed(1)} s`;}
for(const n of activeOrigins){const[x,y]=op[n.id];shape('circle',{cx:x,cy:y,r:11,fill:'#ef8a24'});txt(x-20,y-7,`R${origins.findIndex(o=>o.id===n.id)+1}` ,{'text-anchor':'end','font-weight':'bold'});txt(x-20,y+13,n.label.slice(0,36),{'text-anchor':'end','font-size':11});if(!edges.some(e=>e.source===n.id))txt(x+18,y+4,'No supported route',{'font-size':11,fill:'#a33'});}
for(const n of shown){const[x,y]=dp[n.id];shape('circle',{cx:x,cy:y,r:6,fill:score[n.id]===undefined?'#b2bac1':'#2474ad'});txt(x+16,y+4,n.label.slice(0,47),{'font-size':12});}
el('summary').textContent=`Full ${objective==='lowest_friction'?'friction':'distance'} graph: ${origins.length} origins · 85 POIs · ${allEdges.length} connections. Displaying ${count} connections to ${shown.length} POIs. No residential–residential or POI–POI edges.`;
el('notice').textContent=objective==='lowest_friction'?'Important: missing environmental inputs fragment this graph. Only one of the four origins currently has supported friction routes. This does not mean the other origins are physically inaccessible.':'Provisional prototype: four block-origin examples, not all residential blocks. Twelve of 340 potential pairs are unreachable in the distance network.';}
['objective','origin','limit'].forEach(id=>el(id).addEventListener('change',draw));draw();</script></html>'''
    (OUT/'weighted_graph.html').write_text(html.replace('__DATA__',json.dumps(payload,allow_nan=False).replace('<','\\u003c')))
    return OUT/'weighted_graph.html', OUT/'weighted_graph_overview.png'

if __name__=='__main__':
    print(*run(),sep='\n')
