import {createHash,createHmac,randomBytes,timingSafeEqual} from 'node:crypto';
import seed from '../../src/data/public-feedback.json' with {type:'json'};
const cookieName='empath_voter';
export const feedbackId=message=>createHash('sha256').update(message.trim()).digest('hex');
export function sortFeedback(items){return items.sort((a,b)=>b.votes-a.votes||Date.parse(b.createdAt)-Date.parse(a.createdAt)||a.id.localeCompare(b.id));}
export async function publicItems(store){
 const {blobs}=await store.list({prefix:'ideas/'});
 const saved=await Promise.all(blobs.map(b=>store.get(b.key,{type:'json'})));
 const byMessage=new Map(seed.map(item=>[feedbackId(item.message),item]));
 for(const item of saved)if(item?.message)byMessage.set(feedbackId(item.message),item);
 return [...byMessage.values()].map(({id,message,createdAt})=>({id,message,createdAt}));
}
async function secret(store){let value=await store.get('private/signing-key');if(!value){await store.set('private/signing-key',randomBytes(32).toString('hex'),{onlyIfNew:true});value=await store.get('private/signing-key');}return value;}
const sign=(id,key)=>createHmac('sha256',key).update(id).digest('hex');
export async function voter(request,store){
 const key=await secret(store),value=(request.headers.get('cookie')||'').split(';').map(s=>s.trim()).find(s=>s.startsWith(cookieName+'='))?.slice(cookieName.length+1)||'';
 const [id='',signature='']=value.split('.');const expected=sign(id,key);
 if(/^[a-f0-9]{48}$/.test(id)&&/^[a-f0-9]{64}$/.test(signature)&&timingSafeEqual(Buffer.from(signature),Buffer.from(expected)))return {id,cookie:null,existing:true};
 const next=randomBytes(24).toString('hex');return {id:next,existing:false,cookie:`${cookieName}=${next}.${sign(next,key)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=31536000`};
}
export async function handleFeedback(request,store){
 const json=(data,status=200,cookie)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store',...(cookie?{'Set-Cookie':cookie}:{})}});
 if(!['GET','POST'].includes(request.method))return json({error:'Method not allowed.'},405);
 const person=await voter(request,store),items=await publicItems(store);
 if(request.method==='POST'){
   if(request.headers.get('origin')!==new URL(request.url).origin)return json({error:'Please vote from the EmPath page.'},403);
   if(!person.existing)return json({error:'Please allow cookies and reload before voting.'},403,person.cookie);
   if(!request.headers.get('content-type')?.startsWith('application/json'))return json({error:'Expected JSON.'},415);
   const raw=await request.text();if(raw.length>2048)return json({error:'Request too large.'},413);
   let body;try{body=JSON.parse(raw)}catch{return json({error:'Invalid request.'},400)}
   if(!items.some(item=>item.id===body.id))return json({error:'That idea is not available.'},404);
   // One immutable vote record per idea and browser prevents lost increments and repeat clicks.
   await store.set(`votes/${body.id}/${person.id}`,'1',{onlyIfNew:true});
 }
 const result=await Promise.all(items.map(async item=>{const [{blobs},own]=await Promise.all([store.list({prefix:`votes/${item.id}/`}),store.get(`votes/${item.id}/${person.id}`)]);return {...item,votes:blobs.length,voted:!!own};}));
 return json({items:sortFeedback(result)},200,person.cookie);
}
export async function saveSubmission(payload,store){
 const data=payload?.data||{},form=payload?.form_name||payload?.form?.name||data['form-name'];
 if(form!=='empath-feedback'||!['yes','on','true'].includes(String(data['share-publicly'])))return false;
 const message=String(data.message||'').trim();if(!message||message.length>4000||data['bot-field'])return false;
 // Existing imported messages retain their IDs and votes if an event is replayed.
 if(seed.some(item=>feedbackId(item.message)===feedbackId(message)))return false;
 const id=feedbackId(message),createdAt=payload.created_at||new Date().toISOString();
 await store.setJSON(`ideas/${id}`,{id,message,createdAt},{onlyIfNew:true});return true;
}
