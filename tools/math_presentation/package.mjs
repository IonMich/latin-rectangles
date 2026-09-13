// node tools/math_presentation/package.mjs /absolute/node_modules /absolute/katex.mjs [README source]
import {readFile,writeFile,mkdir,copyFile,stat} from 'node:fs/promises';
import {resolve,dirname,relative,extname} from 'node:path';
import {pathToFileURL} from 'node:url';
const root=process.cwd(),out=resolve('docs/evidence/math-presentation/bundle');
const {marked}=await import(pathToFileURL(resolve(process.argv[2])+'/marked/lib/marked.esm.js').href);
const {default:katex}=await import(pathToFileURL(resolve(process.argv[3])).href);
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
marked.use({gfm:true,renderer:{
 code({text,lang}){return lang==='math'?`<div class="math-display">${katex.renderToString(text,{displayMode:true,output:'mathml',throwOnError:true})}</div>`:`<pre><code>${escape(text)}</code></pre>`;},
 heading({tokens,depth,text}){const id=text.replace(/<[^>]*>/g,'').toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu,'').replace(/\s/g,'-');return `<h${depth} id="${id}">${this.parser.parseInline(tokens)}</h${depth}>`;}
}});
const css=await readFile('tools/math_presentation/readme.css','utf8');
const shell=(title,content)=>`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><style>${css}</style></head><body><main>${content}</main></body></html>`;
await mkdir(out,{recursive:true});
const markdown=await readFile(process.argv[4]||'README.md','utf8');
await writeFile(out+'/README.md',markdown);
const queue=[{text:markdown,base:root}],seen=new Set();
while(queue.length){
 const {text,base}=queue.shift();
 const links=[...text.matchAll(/\[[^\]]*\]\(([^\s)]+)\)/g)].map(m=>m[1]);
 links.push(...[...text.matchAll(/(?:src|srcset)="([^"]+)"/g)].map(m=>m[1]));
 for(const href of links){
  if(/^(?:https?:|#|mailto:)/.test(href))continue;
  const source=resolve(base,decodeURIComponent(href.split('#')[0]));
  if(!source.startsWith(root+'/'))throw Error('Link escapes project '+href);
  if(seen.has(source))continue;seen.add(source);
  const dest=resolve(out,relative(root,source));await mkdir(dirname(dest),{recursive:true});
  await copyFile(source,dest);
  if(extname(source)==='.md'){
   const child=await readFile(source,'utf8');queue.push({text:child,base:dirname(source)});
   await writeFile(dest.replace(/\.md$/,'.html'),shell(relative(root,source),marked.parse(child).replace(/href="([^"#]+)\.md(?=["#])/g,'href="$1.html')));
  }
 }
}
await mkdir(out+'/docs/assets/math-motion',{recursive:true});
await copyFile('docs/assets/math-motion/latin-counting.html',out+'/docs/assets/math-motion/latin-counting.html');
const content=marked.parse(markdown).replace(/href="([^"#]+)\.md(?=["#])/g,'href="$1.html');
await writeFile(out+'/readme.html',shell('Latin Rectangles — README presentation',content));
const extra=`
.review-nav{max-width:1012px;margin:0 auto;padding:15px 20px;display:flex;flex-wrap:wrap;align-items:center;gap:14px;border-bottom:1px solid #d1d9e0;font:14px/1.4 -apple-system,BlinkMacSystemFont,sans-serif}.review-nav strong{margin-right:auto;font-weight:600}.review-nav button{font:inherit;color:inherit;background:none;border:0;padding:9px 5px;cursor:pointer;border-bottom:2px solid transparent}.review-nav button[aria-selected=true]{border-color:currentColor}.review-nav button:focus-visible{outline:2px solid #0969da}.review-nav a{font-size:12px}#interactive-panel{max-width:1120px;margin:0 auto}#interactive-panel iframe{display:block;border:0;width:100%;height:calc(100dvh - 72px);min-height:600px}.review-caption{max-width:1012px;margin:12px auto 0;padding:0 32px;color:#526174;font-size:12px}main{margin-top:18px}.media-controls{max-width:1012px;margin:12px auto 0;padding:0 32px}.media-controls button{font:13px -apple-system,BlinkMacSystemFont,sans-serif;background:none;color:inherit;border:1px solid #d1d9e0;border-radius:4px;padding:7px 10px;cursor:pointer}@media(max-width:600px){.review-nav{gap:9px;padding:10px 16px}.review-nav strong{width:100%}.review-caption,.media-controls{padding:0 16px}#interactive-panel iframe{height:calc(100dvh - 110px)}}@media(prefers-color-scheme:dark){.review-caption{color:#a4b0bf}.review-nav,.media-controls button{border-color:#3d444d}}
`;
const review=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Latin Rectangles — presentation</title><style>${css}${extra}</style></head><body>
<nav class="review-nav" aria-label="Presentation views"><strong>Latin Rectangles</strong><button id="readme-tab" role="tab" aria-selected="true" aria-controls="readme-panel">README presentation</button><button id="interactive-tab" role="tab" aria-selected="false" aria-controls="interactive-panel">Interactive explanation</button><a href="docs/assets/math-motion/latin-counting.html" target="_blank" rel="noopener">Open player ↗</a></nav>
<section id="readme-panel" role="tabpanel" aria-labelledby="readme-tab"><p class="review-caption">The README keeps the full library scope and runnable example. The interactive explanation is available in the second view.</p><div class="media-controls"><button id="pause-preview" type="button">Pause preview</button></div><main>${content}</main></section>
<section id="interactive-panel" role="tabpanel" aria-labelledby="interactive-tab" hidden><iframe title="Interactive explanation of the Latin-rectangle count" src="docs/assets/math-motion/latin-counting.html?embed=1" loading="lazy"></iframe></section>
<script>
const readme=document.getElementById('readme-panel'),interactive=document.getElementById('interactive-panel'),tabs=[document.getElementById('readme-tab'),document.getElementById('interactive-tab')];
function view(index){readme.hidden=index!==0;interactive.hidden=index!==1;tabs.forEach((b,i)=>b.setAttribute('aria-selected',i===index));if(index===0)interactive.querySelector('iframe').contentWindow.postMessage({type:'latin-presentation-pause'},'*');history.replaceState(null,'',index?'#interactive':'#readme');}
tabs.forEach((b,i)=>b.onclick=()=>view(i));if(location.hash==='#interactive')view(1);
const button=document.getElementById('pause-preview'),picture=readme.querySelector('picture'),img=picture.querySelector('img');let frozen=null;
if(matchMedia('(prefers-reduced-motion: reduce)').matches){button.textContent='Static preview · reduced motion';button.disabled=true;}
button.onclick=()=>{if(!frozen){frozen=document.createElement('canvas');frozen.width=img.naturalWidth;frozen.height=img.naturalHeight;frozen.getContext('2d').drawImage(img,0,0);frozen.style.cssText='display:block;max-width:100%;height:auto;margin:auto';frozen.setAttribute('role','img');frozen.setAttribute('aria-label','Paused mathematical preview');picture.after(frozen);picture.style.display='none';button.textContent='Replay preview';}else{frozen.remove();frozen=null;for(const el of picture.querySelectorAll('source,img')){const attr=el.tagName==='SOURCE'?'srcset':'src';el.setAttribute(attr,el.getAttribute(attr).split('?')[0]+'?replay='+Date.now());}picture.style.display='';button.textContent='Pause preview';}};
</script></body></html>`;
await writeFile(out+'/review.html',review);
await writeFile(out+'/REVIEW.md',`# Latin Rectangles — finished mathematical presentation\n\nThe library combines specialized two-row counting with general forbidden-graph k-row methods. The revised visual follows selected violations through rook counts, unrestricted completions, and inclusion–exclusion cancellation.\n\n![The counting explanation](docs/assets/math-motion/counting-desktop.gif)\n\n[Play and explore the explanation](docs/assets/math-motion/latin-counting.html) · [Review the full README in context](review.html)\n\n![The final count and its inclusion–exclusion terms](docs/assets/math-motion/counting-still-desktop.png)\n\nThe interactive player supports pause, seeking, chapter selection, reduced motion, and inspection of component counts. This is a local review of the project presentation; it does not publish the repository.\n`);
await writeFile('docs/evidence/math-presentation/package-manifest.json',JSON.stringify({entry:'bundle/review.html',interactive:'bundle/docs/assets/math-motion/latin-counting.html',markdown:'bundle/README.md',boardSummary:'bundle/REVIEW.md',relativeAssets:true,externalRequestsRequired:false,copiedReferences:seen.size},null,2)+'\n');
console.log('Created relocatable review bundle: '+out+'/review.html');
