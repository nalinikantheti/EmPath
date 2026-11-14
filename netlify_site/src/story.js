/* A single scroll controller and animation clock keep the story from restarting at section boundaries. */
(()=>{
const steps=[...document.querySelectorAll('.story-step')],scene=document.querySelector('.scene'),walker=document.getElementById('walker');
if(!steps.length||!scene||!walker)return;
const motion=matchMedia('(prefers-reduced-motion: reduce)'),paths=[document.getElementById('direct-path'),document.getElementById('cool-path')];
const lengths=paths.map(p=>p.getTotalLength()),captions=['A walk to the bank should be simple.','Heat and traffic can turn it into a medical emergency.','Compare routes and homes for a safer journey.'];
paths.forEach((p,i)=>{p.style.strokeDasharray=String(lengths[i]);p.style.strokeDashoffset=String(i?lengths[i]:0)});
let active=-1,frame=0,scrollFrame=0,route=0,progress=0,locked=null,releaseTimer=0;
const ease=t=>t*t*(3-2*t);
function position(which,value){const p=paths[which].getPointAtLength(lengths[which]*value);walker.setAttribute('transform',`translate(${p.x} ${p.y})`);route=which;progress=value;if(which===1)paths[1].style.strokeDashoffset=String(lengths[1]*(1-value));}
function show(i){if(i===active)return;const initial=active===-1;active=i;steps.forEach((step,j)=>step.dataset.active=String(j===i));cancelAnimationFrame(frame);scene.dataset.stage=String(i);document.getElementById('story-counter').textContent=String(i+1).padStart(2,'0')+' / 03';
const nextRoute=i===2?1:0,target=i===0?0:i===1?.36:1,change=route!==nextRoute,from=change?0:progress,start=performance.now(),fade=change&&!motion.matches?150:0,duration=motion.matches||initial?0:i===2?2000:1100;
if(nextRoute===0)paths[1].style.strokeDashoffset=String(lengths[1]);
window.empathStoryState={step:i,reducedMotion:motion.matches,animating:duration>0};
function tick(now){const elapsed=now-start;if(elapsed<fade){walker.style.opacity=String(1-elapsed/fade);frame=requestAnimationFrame(tick);return}const t=duration?Math.min(1,(elapsed-fade)/duration):1;position(nextRoute,from+(target-from)*ease(t));walker.style.opacity=String(fade?Math.min(1,(elapsed-fade)/180):1);if(t<1)frame=requestAnimationFrame(tick);else{walker.style.opacity='1';window.empathStoryState.animating=false;}}
if(!duration){position(nextRoute,target);walker.style.opacity='1';window.empathStoryState.animating=false;}else frame=requestAnimationFrame(tick);
}
function selectFromScroll(){scrollFrame=0;if(locked!=null)return;const header=document.querySelector('.topbar').getBoundingClientRect().bottom,mobile=matchMedia('(max-width:760px)').matches,visual=document.querySelector('.story-visual').getBoundingClientRect(),top=mobile?Math.max(header,Math.min(innerHeight*.6,visual.bottom)):header,anchor=top+(innerHeight-top)*.45;const distances=steps.map(s=>{const r=s.getBoundingClientRect();return Math.abs((r.top+r.bottom)/2-anchor)});let next=distances.indexOf(Math.min(...distances));if(active>=0&&distances[next]+32>=distances[active])next=active;show(next);}
function schedule(){if(!scrollFrame)scrollFrame=requestAnimationFrame(selectFromScroll);if(locked!=null){clearTimeout(releaseTimer);releaseTimer=setTimeout(()=>{locked=null;schedule()},200)}}
function go(delta){const next=Math.max(0,Math.min(2,active+delta));locked=next;steps[next].scrollIntoView({behavior:'instant',block:'center'});show(next);clearTimeout(releaseTimer);releaseTimer=setTimeout(()=>{locked=null;schedule()},1000);}
document.getElementById('story-next').onclick=()=>go(1);document.getElementById('story-prev').onclick=()=>go(-1);
window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',schedule,{passive:true});motion.addEventListener('change',()=>{const i=active;active=-1;show(i)});
show(0);schedule();
})();
