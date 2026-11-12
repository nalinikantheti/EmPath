// Approximate public Census address lookup. No address storage or API key.
export default async function address(request){
 if(request.method!=='POST')return new Response('Method not allowed',{status:405});
 let body;try{body=await request.json()}catch{return Response.json({error:'Enter a street address.'},{status:400})}
 const q=String(body.address||'').trim();if(q.length<5||q.length>200)return Response.json({error:'Enter a street address in Plano.'},{status:400});
 const url=new URL('https://geocoding.geo.census.gov/geocoder/locations/onelineaddress');url.searchParams.set('address',/plano/i.test(q)?q:q+', Plano, TX');url.searchParams.set('benchmark','Public_AR_Current');url.searchParams.set('format','json');
 try{const r=await fetch(url,{signal:AbortSignal.timeout(18000)});if(!r.ok)throw Error();const d=await r.json();const matches=(d.result?.addressMatches||[]).slice(0,5).map(m=>({address:m.matchedAddress,lon:m.coordinates.x,lat:m.coordinates.y}));return Response.json({matches,source:'U.S. Census Bureau approximate address geocoding'},{headers:{'Cache-Control':'no-store'}})}catch{return Response.json({error:'Address lookup is temporarily unavailable. You can still select an area on the map.'},{status:502})}
}
