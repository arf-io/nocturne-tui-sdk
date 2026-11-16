import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
import {equalBytes} from '../../scripts/resource_ownership_checks.mjs';
import {runAtelier} from '../../scripts/atelier_checks.mjs';
const cases=JSON.parse(readFileSync(new URL('../../examples/atelier-scenes.json',import.meta.url)));
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const report={runtime:'actual WASM',expectedCaseIds:cases.map(c=>c.id),cases:[],complete:false,passed:false};
const persist=()=>{if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n');};persist();
for(const recipe of cases){
 const scene=await NativeScene.create(wasm);
 try{
  for(const command of recipe.commands)scene.command(command);const initial=scene.snapshot();
  const {frames}=runAtelier(scene,recipe,equalBytes),final=scene.snapshot();
  for(const command of recipe.rejectedCommands){assert.throws(()=>scene.command(command));assert.ok(equalBytes(final,scene.snapshot()),recipe.id+' atomic rejection');}
  scene.restore(initial);const replay=runAtelier(scene,recipe,equalBytes).frames;
  assert.ok(equalBytes(final,scene.snapshot()),recipe.id+' replay source');
  for(const [i,frame] of frames.entries())assert.ok(equalBytes(frame,replay[i]),recipe.id+' replay frame');
  report.cases.push({id:recipe.id,status:'PASS',samples:frames.length});persist();
 }catch(error){report.cases.push({id:recipe.id,status:'FAIL',error:String(error.stack||error)});persist();throw error;}
 finally{scene.close();}
}
report.complete=true;report.passed=true;persist();console.log('PASS actual WASM Atelier source '+cases.length);
