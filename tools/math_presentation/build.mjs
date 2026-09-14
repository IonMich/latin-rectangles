// node tools/math_presentation/build.mjs /absolute/katex.mjs
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
const {default:katex}=await import(pathToFileURL(resolve(process.argv[2])).href);
const formulas={
 event:String.raw`A_{i,s}=\{\sigma:\sigma(i)=s\}`,
 selected:String.raw`A=A_{1,1},\qquad B=A_{3,4}`,
 conflict:String.raw`|A\cap B|=0`,
 choosePairs:String.raw`\binom{16}{2}=120`,
 minusColumns:String.raw`120-8=112`,
 minusSymbols:String.raw`120-8-8=104`,
 rookTwo:String.raw`r_2=\binom{16}{2}-8-8=104`,
 sixFactorial:String.raw`(8-2)!=6!=720`,
 pairsCompletions:String.raw`r_2\,6!=104\cdot720`,
 cancellation:String.raw`1-2+1=0`,
 cancelZero:String.raw`1`,
 cancelOne:String.raw`1-1=0`,
 cancelTwo:String.raw`1-1-1=-1`,
 generalIE:String.raw`E=\sum_{j=0}^{8}(-1)^j r_j(8-j)!`,
 componentProduct:String.raw`R_B(x)=R_2(x)^2R_4(x)`,
 componentCoefficient:String.raw`\begin{aligned}r_2&=2+2+20\\&\quad+16+32+32=104\end{aligned}`,
 componentPolys:String.raw`\begin{aligned}R_2(x)&=1+4x+2x^2,\\R_4(x)&=1+8x+20x^2\\&\quad+16x^3+2x^4.\end{aligned}`,
 generalMatching:String.raw`\begin{aligned}R_F(x)&=R_{F-c}(x)\\&\quad+x\sum_{s\in N_F(c)}R_{F-\{c,s\}}(x).\end{aligned}`,
 touchard:String.raw`q_a(t)q_b(t)=q_{a+b}(t)+q_{|a-b|}(t).`,
};
const math=Object.fromEntries(Object.entries(formulas).map(([key,value])=>[key,katex.renderToString(value,{displayMode:true,output:'mathml',throwOnError:true})]));
const scene=JSON.parse(await readFile('docs/evidence/math-presentation/scene.json','utf8'));
const template=await readFile('tools/math_presentation/interactive.template.html','utf8');
const html=template.replace('__SCENE_DATA__',JSON.stringify(scene)).replace('__MATH_DATA__',JSON.stringify(math));
if(html.includes('__SCENE_DATA__')||html.includes('__MATH_DATA__'))throw Error('Unresolved template');
await mkdir('docs/assets/math-motion',{recursive:true});
await writeFile('docs/assets/math-motion/latin-counting.html',html);
await writeFile('docs/evidence/math-presentation/equations.json',JSON.stringify(formulas,null,2)+'\n');
console.log(`Built self-contained interactive presentation with ${Object.keys(math).length} compiled equations.`);
