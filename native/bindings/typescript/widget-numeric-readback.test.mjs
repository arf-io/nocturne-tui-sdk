// Real WASM widget numeric metadata regression, authored before native repair.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 const controls={value:1e-7,min:-1e-7,max:.987654321,alpha:.123456789,data:[.1,.3,1e-7],cellAspect:2.123456789,innerRadius:.234567891,startAngle:.987654321,sweepAngle:270.123456789};
 scene.command({op:'widget',id:1,kind:'donut',...controls});const pure=scene.snapshot();
 const widget=()=>scene.infoComplete().widgets.find(w=>w.id===1);
 for(const key of ['value','min','max','alpha','data'])assert.deepEqual(widget()[key],controls[key]);
 for(const key of ['cellAspect','innerRadius','startAngle','sweepAngle'])assert.equal(widget().plot[key],controls[key]);
 scene.render();assert.deepEqual(scene.snapshot(),pure);
 scene.command({op:'define',path:'/v',value:1e-7,binding:{family:'widget',id:1,field:'value'}});
 assert.equal(widget().value,1e-7);
 scene.command({op:'set',path:'/v',expression:{multiply:[0,-1]}});assert.ok(Object.is(widget().value,-0));
 const initial=scene.snapshot();scene.command({op:'set',path:'/v',value:.123456789});const final=scene.snapshot(),frame=scene.render().bytes;
 assert.equal(widget().value,.123456789);assert.throws(()=>scene.command({op:'set',path:'/v',value:1000001}));assert.deepEqual(scene.snapshot(),final);
 scene.restore(initial);scene.command({op:'set',path:'/v',value:.123456789});assert.deepEqual(scene.snapshot(),final);assert.deepEqual(scene.render().bytes,frame);
 console.log('PASS real WASM exact widget numeric readback');
}finally{scene.close();}
