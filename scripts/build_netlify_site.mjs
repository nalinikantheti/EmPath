import {readFile,writeFile,mkdir,readdir,rm} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const src=path.join(root,'netlify_site/src'),dest=path.join(root,'netlify_site/dist');
let key=process.env.CARTO_BASEMAP_API_KEY?.trim();
// Local preview convenience only. Netlify obtains the key from its environment UI.
if(!key){try{const env=await readFile(path.join(root,'.env'),'utf8');const match=env.match(/^\s*(?:export\s+)?CARTO_BASEMAP_API_KEY\s*=\s*(.+)\s*$/m);key=match?.[1]?.trim().replace(/^["']|["']$/g,'');}catch{}}
if(!key)throw new Error('Set CARTO_BASEMAP_API_KEY in Netlify environment variables, then redeploy.');
await rm(dest,{recursive:true,force:true});await mkdir(dest,{recursive:true});
let count=0;
async function copy(folder,target){
 await mkdir(target,{recursive:true});
 for(const entry of await readdir(folder,{withFileTypes:true})){
  const input=path.join(folder,entry.name),output=path.join(target,entry.name);
  if(entry.isDirectory())await copy(input,output);
  else{
   let data=await readFile(input);
   if(entry.name.endsWith('.html'))data=Buffer.from(data.toString('utf8').replaceAll('__EMPATH_CARTO_PUBLIC_KEY__',encodeURIComponent(key)));
   await writeFile(output,data);count++;
  }
 }
}
await copy(src,dest);
console.log(`Built ${count} static files in netlify_site/dist. Key value not logged.`);
