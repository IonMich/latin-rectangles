// node tools/math_presentation/inspect.mjs /absolute/node_modules
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
const modules=resolve(process.argv[2]);
const {chromium}=await import(pathToFileURL(modules+'/playwright/index.mjs').href);
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
const artifact=pathToFileURL(resolve('docs/assets/math-motion/latin-counting.html')).href;
const evidence='docs/evidence/math-presentation';
await mkdir(evidence,{recursive:true});
const checks=[];
for(const [name,width,colorScheme,reducedMotion] of [['desktop',1080,'light','no-preference'],['mobile',390,'light','no-preference'],['narrow',320,'light','reduce'],['dark',1080,'dark','reduce']]){
 const page=await browser.newPage({viewport:{width,height:1000},colorScheme,reducedMotion});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(artifact);
 if((await page.evaluate(()=>window.latinPresentation.getState())).playing)throw Error('Player should start paused');
 const scenes=[];
 for(const [label,time] of [['select',0],['conflict',4],['pairs',20.5],['complete',35],['cancel',49],['total',62]]){
  await page.evaluate(t=>window.latinPresentation.seek(t),time);
  const dimensions=await page.evaluate(()=>({pageWidth:document.documentElement.scrollWidth,viewport:document.documentElement.clientWidth,overflowingMath:[...document.querySelectorAll('.equation')].filter(e=>e.clientWidth&&e.scrollWidth>e.clientWidth+1).map(e=>e.textContent),undefinedText:document.querySelector('main').innerText.includes('undefined'),invalidArity:[...document.querySelectorAll('mfrac,msub,msup,msubsup,munder,mover,munderover')].filter(e=>e.children.length!==(['msubsup','munderover'].includes(e.localName)?3:2)).length,marks:document.querySelectorAll('#board>g>g').length}));
  if(dimensions.pageWidth>dimensions.viewport||dimensions.overflowingMath.length||dimensions.invalidArity||dimensions.undefinedText)throw Error('Invalid scene '+name+' '+label+' '+JSON.stringify(dimensions));
  scenes.push({label,time,...dimensions});
  if(name==='desktop'||name==='mobile')await page.screenshot({path:`${evidence}/${name}-${label}.png`,fullPage:true});
 }
 await page.getByRole('button',{name:'Why components multiply'}).click();
 for(let i=0;i<6;i++)await page.evaluate(j=>window.latinPresentation.showComponents(j),i);
 if(name==='desktop'||name==='mobile')await page.screenshot({path:`${evidence}/${name}-components.png`,fullPage:true});
 await page.locator('[data-chapter="0"]').click();
 await page.getByRole('button',{name:'Play',exact:true}).click();
 await page.waitForTimeout(350);
 const playing=await page.evaluate(()=>window.latinPresentation.getState());
 await page.getByRole('button',{name:'Pause',exact:true}).click();
 const paused=await page.evaluate(()=>window.latinPresentation.getState());
 await page.waitForTimeout(200);
 const stable=await page.evaluate(()=>window.latinPresentation.getState());
 if(!playing.playing||playing.time<=0||paused.playing||stable.time!==paused.time)throw Error('Playback/pause failure '+name);
 await page.locator('#play').focus();await page.keyboard.press('Space');
 if(!(await page.evaluate(()=>window.latinPresentation.getState())).playing)throw Error('Keyboard play failed');
 await page.keyboard.press('Space');
 if((await page.evaluate(()=>window.latinPresentation.getState())).playing)throw Error('Keyboard pause failed');
 await page.evaluate(()=>{const range=document.getElementById('seek');range.value=45;range.dispatchEvent(new Event('input',{bubbles:true}));});
 if((await page.evaluate(()=>window.latinPresentation.getState())).time!==45)throw Error('Seek control failed');
 await page.evaluate(()=>window.latinPresentation.seek(62));
 if(await page.locator('.sum-result strong').innerText()!=='4,744')throw Error('Final displayed count differs');
 await page.locator('summary').click();
 const expanded=await page.evaluate(()=>[...document.querySelectorAll('.equation')].filter(e=>e.clientWidth&&e.scrollWidth>e.clientWidth+1).map(e=>e.textContent));
 if(expanded.length)throw Error('Expanded math overflow '+name);
 if(errors.length)throw Error('Browser errors '+name+': '+errors.join(';'));
 checks.push({name,scenes,errors,playbackAndPauseVerified:true,startsPaused:true});
 await page.close();
}
await browser.close();
await writeFile(`${evidence}/browser-checks.json`,JSON.stringify(checks,null,2)+'\n');
console.log(JSON.stringify(checks.map(c=>({name:c.name,errors:c.errors,overflow:c.scenes.filter(s=>s.pageWidth>s.viewport||s.overflowingMath.length),invalid:c.scenes.filter(s=>s.invalidArity||s.undefinedText)}))));
