// node tools/math_presentation/export.mjs /absolute/node_modules
import {mkdir,writeFile,stat} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
const modules=resolve(process.argv[2]);
const {chromium}=await import(pathToFileURL(modules+'/playwright/index.mjs').href);
const {default:sharp}=await import(pathToFileURL(modules+'/sharp/dist/index.mjs').href);
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
const metadata=[];
for(const [size,width,height] of [['desktop',900,580],['mobile',390,870]]){
 const page=await browser.newPage({viewport:{width,height},colorScheme:'light',reducedMotion:'reduce',deviceScaleFactor:1});
 await page.goto(pathToFileURL(resolve('docs/assets/math-motion/latin-counting.html')).href+'?capture='+size);
 const frames=`benchmark_results/math-presentation/${size}`;
 await mkdir(frames,{recursive:true});
 for(let i=0;i<=372;i++){
  await page.evaluate(t=>window.latinPresentation.seek(t),i/6);
  const bounds=await page.evaluate(()=>({bottom:document.querySelector('.scene').getBoundingClientRect().bottom,scrollWidth:document.documentElement.scrollWidth,width:innerWidth}));
  if(bounds.bottom>height||bounds.scrollWidth>width)throw Error('Capture would clip '+size+' frame '+i+' '+JSON.stringify(bounds));
  await page.screenshot({path:`${frames}/frame-${String(i).padStart(4,'0')}.png`});
  if(i%120===0)console.log(size+': captured '+i+'/372');
 }
 await page.screenshot({path:`docs/assets/math-motion/counting-still-${size}.png`});
 await page.evaluate(()=>window.latinPresentation.seek(20.5));
 await page.screenshot({path:`docs/assets/math-motion/rook-count-${size}.png`});
 await page.close();
 const output=`docs/assets/math-motion/counting-${size}.gif`;
 execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate','6','-i',`${frames}/frame-%04d.png`,'-filter_complex','split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=none','-loop','-1','-final_delay','200',output],{stdio:'inherit'});
 const meta=await sharp(output,{animated:true}).metadata();
 metadata.push({path:output,bytes:(await stat(output)).size,width:meta.width,height:meta.pageHeight,frames:meta.pages,durationMs:meta.delay.reduce((a,b)=>a+b,0),plays:meta.loop});
 console.log('Exported '+output+' '+metadata.at(-1).bytes+' bytes');
}
await browser.close();
await writeFile('docs/evidence/math-presentation/asset-checks.json',JSON.stringify(metadata,null,2)+'\n');
