import {readFile,writeFile,mkdir,readdir,rm} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const src=path.join(root,'netlify_site/src'),dest=path.join(root,'netlify_site/dist');
await rm(dest,{recursive:true,force:true});await mkdir(dest,{recursive:true});
const tileURL='/.netlify/functions/basemap?z={z}&x={x}&y={y}';
const placeholder=/https:\/\/basemaps\.cartocdn\.com\/rastertiles\/light_all\/\{z\}\/\{x\}\/\{y\}\.png\?key=__EMPATH_CARTO_PUBLIC_KEY__/g;
let count=0;
async function copy(folder,target){
 await mkdir(target,{recursive:true});
 for(const entry of await readdir(folder,{withFileTypes:true})){
  const input=path.join(folder,entry.name),output=path.join(target,entry.name);
  if(entry.isDirectory())await copy(input,output);
  else{
   let data=await readFile(input);
   if(entry.name.endsWith('.html')){
    const text=data.toString('utf8').replace(placeholder,tileURL).replaceAll('https://empathmaps.netlify.app/.netlify/functions/basemap','/.netlify/functions/basemap').replace(/L\.map\(([^,]+),\s*\{/g,'L.map($1,{scrollWheelZoom:false,').replace("L.map('map')","L.map('map',{scrollWheelZoom:false})").replace(/"scrollWheelZoom"\s*:\s*true/g,'"scrollWheelZoom":false');
    if(text.includes('__EMPATH_CARTO_PUBLIC_KEY__'))throw new Error('Unresolved basemap placeholder in '+entry.name);
    data=Buffer.from(text);
   }
   await writeFile(output,data);count++;
  }
 }
}
await copy(src,dest);
// Keep existing methodology links on the same maintained page.
await writeFile(path.join(dest,'behind.html'), await readFile(path.join(dest,'method.html')));
console.log(`Built ${count} files. Basemap requests use a server function; no key is embedded in HTML.`);
