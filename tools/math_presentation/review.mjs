// Verify the complete relocatable review package over a temporary loopback server.
// node tools/math_presentation/review.mjs /absolute/node_modules
import {createServer} from 'node:http';
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
import {pathToFileURL} from 'node:url';
const root=resolve('docs/evidence/math-presentation/bundle');
const {chromium}=await import(pathToFileURL(resolve(process.argv[2])+'/playwright/index.mjs').href);
const server=createServer(async(req,res)=>{try{const path=resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!path.startsWith(root+'/'))throw Error('outside');res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.md':'text/plain;charset=utf-8','.svg':'image/svg+xml','.gif':'image/gif','.png':'image/png','.json':'application/json'})[extname(path)]||'text/plain');res.end(await readFile(path));}catch{res.writeHead(404);res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
const results=[];
for(const [name,width,reducedMotion,colorScheme] of [['desktop',1280,'no-preference','light'],['mobile',390,'no-preference','light'],['reduced-mobile',390,'reduce','light'],['dark',1280,'reduce','dark']]){
 const context=await browser.newContext({viewport:{width,height:1000},reducedMotion,colorScheme});
 const page=await context.newPage(),errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',route=>{if(new URL(route.request().url()).origin!==origin){external.push(route.request().url());route.abort();}else route.continue();});
 await page.goto(origin+'/review.html');
 await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
 const before=await page.evaluate(()=>({pageWidth:document.documentElement.scrollWidth,viewport:innerWidth,images:[...document.images].map(i=>({src:i.currentSrc,loaded:i.complete&&i.naturalWidth>0})),mathOverflow:[...document.querySelectorAll('.math-display')].filter(e=>e.scrollWidth>e.clientWidth+1).map(e=>e.textContent)}));
 if(before.pageWidth>before.viewport||before.mathOverflow.length)throw Error('README layout failure '+name);
 if(reducedMotion==='reduce'){if(!before.images[0].src.endsWith('.png'))throw Error('Reduced motion fallback failed');}
 else{
  await page.getByRole('button',{name:'Pause preview',exact:true}).click();
  if(!await page.locator('canvas').isVisible())throw Error('Pause preview failed');
  await page.getByRole('button',{name:'Replay preview',exact:true}).click();
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
 }
 await page.screenshot({path:`docs/evidence/math-presentation/review-${name}-readme.png`});
 if(name==='desktop'){
  for(const href of await page.locator('#readme-panel main a').evaluateAll(as=>as.map(a=>a.getAttribute('href')))){
   const target=new URL(href,origin+'/review.html');if(target.origin!==origin)continue;
   const response=await page.request.get(target.href);if(!response.ok())throw Error('Broken package link '+href);
   if(target.hash){const other=await context.newPage();await other.goto(target.href);if(!await other.evaluate(id=>!!document.getElementById(id),decodeURIComponent(target.hash.slice(1))))throw Error('Missing package anchor '+href);await other.close();}
  }
 }
 await page.getByRole('tab',{name:'Interactive explanation',exact:true}).click();
 const frame=await(await page.locator('#interactive-panel iframe').elementHandle()).contentFrame();
 await frame.waitForFunction(()=>!!window.latinPresentation);
 await frame.evaluate(()=>window.latinPresentation.seek(35));
 await frame.locator('#play').click();await page.waitForTimeout(250);
 if(!(await frame.evaluate(()=>window.latinPresentation.getState())).playing)throw Error('Embedded playback failed');
 await frame.locator('#play').click();
 await page.screenshot({path:`docs/evidence/math-presentation/review-${name}-interactive.png`});
 await page.getByRole('tab',{name:'README presentation',exact:true}).click();
 await frame.waitForFunction(()=>!window.latinPresentation.getState().playing);
 if(errors.length||external.length)throw Error('Review runtime failure '+JSON.stringify({errors,external}));
 results.push({name,...before,errors,external,previewPauseReplay:reducedMotion!=='reduce',embeddedPlaybackVerified:true});
 await context.close();
}
await browser.close();server.close();
await writeFile('docs/evidence/math-presentation/review-checks.json',JSON.stringify(results,null,2)+'\n');
console.log(JSON.stringify(results.map(r=>({name:r.name,width:r.viewport,mathOverflow:r.mathOverflow.length,errors:r.errors,externalRequests:r.external.length,embeddedPlaybackVerified:r.embeddedPlaybackVerified}))));
