import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const fields={"window": {"position.x": [0, 8], "position.y": [4, 8], "position.z": [0, 3], "yaw": [0, 25], "pitch": [0, 15], "roll": [0, 10], "width": [30, 38], "height": [14, 18], "minColumns": [30, 36], "maxColumns": [78, 68], "padding": [1, 2], "chromeSize": [3, 4], "fadeStartRatio": [1, 1.2], "fadeEndRatio": [0.22, 0.1], "anchorX": [0.5, 0.2], "anchorY": [1.15, 0.8], "overshoot": [0.18, 0.4], "scatter": [32, 16], "bend": [9, 14], "folds": [6, 10], "meshColumns": [12, 16], "meshRows": [8, 12], "durationMs": [600, 1200]}, "area": {"x": [8, 12], "y": [26, 24], "width": [60, 72], "height": [7, 9], "padding": [1, 2], "margin": [0, 1], "speedX": [8, 16], "speedY": [1, 2], "hideEmpty": [0, 1], "fadeMs": [500, 800], "gapMs": [300, 600]}};
let checked=0;
for(const [family,entries] of Object.entries(fields))for(const [field,[initial,target]] of Object.entries(entries)){
 const s=await NativeScene.create(wasm), oracle=await NativeScene.create(wasm);
 try{
  const base=family==='window'?[{op:'window',id:1,title:'Panel',text:'Retained document',position:[0,4,0],width:30,height:14,effect:'window-transition/ribbon-genie'}]:[{op:'area',id:1,x:8,y:26,width:60,height:7},{op:'status',id:1,area:1,text:'Native layout',durationMs:0}];
  for(const scene of [s,oracle]){for(const command of base)scene.command(command);scene.advanceTo(250000);}
  s.command({op:'define',path:'/control',value:target,binding:{family,id:1,field}});
  const edit={op:family,id:1,[field]:field==='hideEmpty'?!!target:target};
  if(field.startsWith('position.')){delete edit[field];edit.position=[0,4,0];edit.position['xyz'.indexOf(field.at(-1))]=target;}
  oracle.command(edit);s.command({op:'remove-value',path:'/control'});assert.deepEqual(s.snapshot(),oracle.snapshot(),family+'.'+field);
  s.advanceTo(1000000);oracle.advanceTo(1000000);assert.deepEqual(s.render().bytes,oracle.render().bytes);checked++;
 }finally{s.close();oracle.close();}
}
const s=await NativeScene.create(wasm);try{s.command({op:'window',id:1});const saved=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/invalid',value:0,binding:{family:'window',id:1,field:'width'}}));assert.deepEqual(s.snapshot(),saved);}finally{s.close();}
console.log(JSON.stringify({runtime:'actual WASM',fields:checked,publicEditOracle:true,atomicRejection:true,wasmSha256:createHash('sha256').update(wasm).digest('hex')}));
