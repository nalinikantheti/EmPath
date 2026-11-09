const path='/Users/nalinikantheti/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/';
const sharp=require(path+'sharp');
const {mathjax}=require(path+'mathjax-full/js/mathjax.js');
const {TeX}=require(path+'mathjax-full/js/input/tex.js');
const {SVG}=require(path+'mathjax-full/js/output/svg.js');
const {liteAdaptor}=require(path+'mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler}=require(path+'mathjax-full/js/handlers/html.js');
const adaptor=liteAdaptor();RegisterHTMLHandler(adaptor);
const doc=mathjax.document('',{InputJax:new TeX(),OutputJax:new SVG({fontCache:'none'})});
const equations=[String.raw`w_{\theta}(e,t)=T(e)\left[1+f_{\theta}(\mathbf{x}_e,\mathbf{h}_t)\right],\qquad f_{\theta}\geq0.`,String.raw`C_{\theta}(P,t)=\sum_{e\in P} w_{\theta}(e,t).`,String.raw`F_{\theta}(r)=\sum_{d\in D}d_{w_{\theta}}(r,d).`,String.raw`r^{*}=\mathop{\mathrm{arg\,min}}_{r\in R}\left[\sum_{d\in D_{\mathrm{selected}}}d_{w_{\theta}}(r,d)\right].`];
(async()=>{for(let i=0;i<equations.length;i++){
 let html=adaptor.outerHTML(doc.convert(equations[i],{display:true}));let svg=html.slice(html.indexOf('<svg'),html.indexOf('</svg>')+6).replace(/currentColor/g,'#000000').replace(/(width|height)="([0-9.]+)ex"/g,(_,a,n)=>`${a}="${Number(n)*10}px"`);
 await sharp(Buffer.from(svg),{density:400}).flatten({background:'#ffffff'}).extend({top:20,bottom:20,left:25,right:25,background:'#ffffff'}).png().toFile(`output/proposal_google_docs/equations/equation_${i+1}.png`);
 }})();
