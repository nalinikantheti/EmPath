// Key remains in the function environment; never send it to the browser or logs.
export default async function basemap(request) {
  if(request.method!=='GET')return new Response('Method not allowed',{status:405});
  const query=new URL(request.url).searchParams;
  const values=['z','x','y'].map(name=>query.get(name));
  if(values.some(v=>v===null||!/^\d+$/.test(v)))return new Response('Invalid tile',{status:400});
  const [z,x,y]=values.map(Number);
  if(z>19||x>=2**z||y>=2**z)return new Response('Invalid tile',{status:400});
  const key=process.env.CARTO_BASEMAP_API_KEY;
  if(!key)return new Response('Basemap is not configured',{status:503});
  const upstream=new URL(`https://basemaps.cartocdn.com/rastertiles/light_all/${z}/${x}/${y}.png`);
  upstream.searchParams.set('key',key);
  try {
    const response=await fetch(upstream,{signal:AbortSignal.timeout(15000)});
    if(!response.ok)return new Response('Basemap tile unavailable',{status:502});
    const type=response.headers.get('content-type')||'';
    if(!type.startsWith('image/'))return new Response('Unexpected basemap response',{status:502});
    return new Response(await response.arrayBuffer(),{headers:{
      'Content-Type':type,'Cache-Control':'public, max-age=86400',
      'Netlify-CDN-Cache-Control':'public, max-age=86400','X-Content-Type-Options':'nosniff'
    }});
  }catch{return new Response('Basemap temporarily unavailable',{status:502});}
}
