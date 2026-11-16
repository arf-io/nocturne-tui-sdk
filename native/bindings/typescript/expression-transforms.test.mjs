import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const scene=await NativeScene.create(wasm);
const cases=[
 [{floor:-1.2},-2],[{ceil:-1.2},-1],[{round:-1.5},-1],
 [{lerp:{from:2,to:10,amount:.25}},4],
 [{remap:{value:15,inMin:10,inMax:20,outMin:0,outMax:1}},.5],
 [{convert:{value:2,from:'seconds',to:'milliseconds'}},2000],
 [{convert:{value:250,from:'centimeters',to:'meters'}},2.5],
 [{convert:{value:180,from:'degrees',to:'radians'}},Math.PI],
 [{convert:{value:32,from:'fahrenheit',to:'celsius'}},0],
 [{convert:{value:100,from:'celsius',to:'fahrenheit'}},212],
];
try {
 for(const [path,value] of [['/go',0],['/out',0],['/input',15]])scene.command({op:'define',path,value});
 for(const [expression,expected] of cases){
  scene.command({op:'set',path:'/out',expression});assert.ok(Math.abs(scene.info().values['/out']-expected)<1e-10);
  scene.command({op:'set',path:'/go',value:0});
  scene.command({op:'trigger',id:1,source:'/go',threshold:0,target:'/out',expression});
  scene.command({op:'set',path:'/go',value:1});assert.ok(Math.abs(scene.info().values['/out']-expected)<1e-10);
 }
 const before=scene.snapshot();
 assert.throws(()=>scene.command({op:'set',path:'/out',expression:{convert:{value:1,from:'meters',to:'seconds'}}}));
 assert.deepEqual(scene.snapshot(),before);
 scene.command({op:'set',path:'/go',value:0});
 scene.command({op:'trigger',id:1,source:'/go',target:'/out',debounceMs:500,expression:{remap:{value:{path:'/input'},inMin:10,inMax:20,outMin:0,outMax:1}}});
 const owned=scene.snapshot();assert.throws(()=>scene.command({op:'remove-value',path:'/input'}));assert.deepEqual(scene.snapshot(),owned);
 scene.command({op:'set',path:'/go',value:1});scene.command({op:'set',path:'/input',value:18});
 const start=scene.snapshot();scene.advanceTo(500000);assert.equal(scene.info().values['/out'],.8);
 const finish=scene.snapshot();scene.render();assert.deepEqual(scene.snapshot(),finish);
 scene.restore(start);scene.advanceTo(500000);assert.deepEqual(scene.snapshot(),finish);
 console.log(JSON.stringify({runtime:'actual WASM',directAndRetainedCases:cases.length,dimensionalRejection:true,nestedSourceOwnership:true,executionTimeRead:true,replay:true,renderPure:true,wasmSha256:createHash('sha256').update(wasm).digest('hex')}));
}finally{scene.close();}
