// Offline test-only transpilation of the preserved original source; no SDK dispatch.
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const ts=require(process.env.NOCTURNE_TYPESCRIPT_MODULE||'typescript');
export function atelierOracleSource(){
 const input=readFileSync(new URL('../../legacy/atelier-v0.5/bindings/typescript/particles.ts',import.meta.url),'utf8');
 const code=ts.transpileModule(input,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText
  .replace(/import[^;]+;/,'').replace(/export /g,'');
 const prefix="const TAU=Math.PI*2,clamp=(v,a,b)=>Math.max(a,Math.min(b,v));function finite(v,a,b,label){if(typeof v!=='number'||!Number.isFinite(v)||v<a||v>b)throw Error(label);return v;}function randomAt(seed,index){let v=(seed^Math.imul(index+1,0x9e3779b9))>>>0;v=Math.imul(v^(v>>>16),0x7feb352d)>>>0;v=Math.imul(v^(v>>>15),0x846ca68b)>>>0;return ((v^(v>>>16))>>>0)/4294967296;}";
 return prefix+code;
}
export const sampleBurst=Function(atelierOracleSource()+';return sampleBurst;')();
if(process.argv.includes('--source'))process.stdout.write(atelierOracleSource());
