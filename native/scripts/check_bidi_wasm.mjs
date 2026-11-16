import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from '../bindings/typescript/native_scene.mjs';
const digest=data=>createHash('sha256').update(data).digest('hex');
const folder=new URL('../unicode/17.0.0/',import.meta.url),manifest=JSON.parse(readFileSync(new URL('SOURCES.json',folder)));
const wasm=readFileSync(new URL('../dist/nocturne_native.wasm',import.meta.url));
const s=await NativeScene.create(wasm,2030),results={};
const classes='L R AL EN AN ES ET CS NSM BN B S WS ON LRE LRO RLE RLO PDF LRI RLI FSI PDI'.split(' ');
const scalars=[65,0x5d0,0x627,49,0x661,43,36,44,0x300,0xad,10,9,32,33,0x202a,0x202d,0x202b,0x202e,0x202c,0x2066,0x2067,0x2068,0x2069];
try {
 for(const name of ['BidiCharacterTest.txt','BidiTest.txt']){
  const raw=readFileSync(new URL(name,folder)),sha256=digest(raw);if(sha256!==manifest.sources.find(r=>r.name===name).sha256)throw Error('Fixture hash mismatch');
  let total=0,mismatches=0,expectedLevels,expectedOrder;const failures=[];
  const execute=(text,direction,levels,order,line)=>{
   const rows=s.bidiVisual(text,direction),actualLevels=Array.from(text,()=>null),actualOrder=rows.map(r=>r[0]);for(const row of rows)actualLevels[row[0]]=row[2];total++;
   if(JSON.stringify(actualLevels)!==JSON.stringify(levels)||JSON.stringify(actualOrder)!==JSON.stringify(order)){mismatches++;if(failures.length<5)failures.push({line,direction,expectedLevels:levels,actualLevels,expectedOrder:order,actualOrder});}
  };
  let lineNumber=0;
  for(let line of raw.toString('utf8').split('\n')){
   lineNumber++;line=line.split('#')[0].trim();if(!line)continue;
   if(name==='BidiCharacterTest.txt'){
    const fields=line.split(';').map(x=>x.trim());if(fields.length!==5)throw Error('Invalid fixture');
    const text=String.fromCodePoint(...fields[0].split(/\s+/).map(x=>parseInt(x,16)));
    execute(text,Number(fields[1]),fields[3].split(/\s+/).map(x=>x==='x'?null:Number(x)),fields[4]?fields[4].split(/\s+/).map(Number):[],lineNumber);
   }else{
    if(line.startsWith('@Levels:')){const value=line.split(':')[1].trim();expectedLevels=value?value.split(/\s+/).map(x=>x==='x'?null:Number(x)):[];continue;}
    if(line.startsWith('@Reorder:')){const value=line.split(':')[1].trim();expectedOrder=value?value.split(/\s+/).map(Number):[];continue;}
    if(line.startsWith('@'))continue;
    const [input,mask]=line.split(';'),text=String.fromCodePoint(...input.trim().split(/\s+/).map(c=>scalars[classes.indexOf(c)])),bits=parseInt(mask,16);
    for(const [bit,direction] of [[1,2],[2,0],[4,1]])if(bits&bit)execute(text,direction,expectedLevels,expectedOrder,lineNumber);
   }
  }
  results[name]={sha256,total,mismatches,passed:total>0&&!mismatches,failures};
 }
 const report={schema:'nr-bidi-wasm-conformance-v1',unicodeVersion:'17.0.0',wasmSha256:digest(wasm),bindingSha256:digest(readFileSync(new URL('../bindings/typescript/native_scene.mjs',import.meta.url))),passed:Object.values(results).every(r=>r.passed),results};
 const output=process.argv[2];if(output)writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));if(!report.passed)process.exitCode=1;
}finally{s.close();}
