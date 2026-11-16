import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));const s=await NativeScene.create(wasm);
try{
 const studies=[['hsl',{h:0,s:1,l:.5},'lightness',.25,0x800000],['rgb',{r:.2,g:.4,b:.6},'channels.r',1,0xff6699],['hsb',{h:0,s:1,v:1},'brightness',.5,0x800000],['indexed',{i:0},'channels.i',1,0x00ff00]];
 for(const [space,channels,field,value,color] of studies){s.command({op:'reset'});s.command({op:'material',id:2,space,channels,alpha:1,...(space==='indexed'?{colors:[0xff0000,0x00ff00]}:{})});s.command({op:'widget',id:1,kind:'text',x:2,y:2,height:1,text:'A',alpha:0,material:2});s.command({op:'define',path:'/color',value,binding:{family:'material',id:2,field}});const saved=s.snapshot(),frame=s.render();assert.equal(frame.cells[(2*frame.width+2)*4+1],color);assert.deepEqual(s.snapshot(),saved);s.restore(saved);assert.deepEqual(s.snapshot(),saved);}
 s.command({op:'reset'});s.command({op:'material',id:2,space:'rgb'});const saved=s.snapshot();assert.throws(()=>s.command({op:'define',path:'/bad',value:.5,binding:{family:'material',id:2,field:'hue'}}));assert.deepEqual(s.snapshot(),saved);
 console.log(JSON.stringify({runtime:'actual WASM',independentColorChecks:studies.length,incompatibleAliasRejection:true,renderPure:true,snapshotReplay:true,wasmSha256:createHash('sha256').update(wasm).digest('hex')}));
}finally{s.close();}
