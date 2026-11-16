import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try{
 const cmd={op:'field',x:10,y:5,width:3,speed:2,strength:.7,seed:71,continuous:true,falloff:4,frequency:237,phase:-71,interference:.8,velocity:[3,-2],surface:{x:8,y:3,width:40,height:20}};s.command(cmd);
 for(const t of [0,500000,1500000,5000000]){s.advanceTo(t);const before=s.snapshot(),age=t/1e6,cx=18+3*age,cy=8-2*age;for(const [x,y] of [[18,8],[22,10],[7,8]]){const q=s.fieldSample(1,x,y),dist=Math.hypot(2*(x-cx),4*(y-cy)),angle=((dist-4*age)/6.01*237-age*90-71)*Math.PI/180,wave=.2*(.5+.5*Math.cos(angle))+.8*(.5+.5*Math.cos(2*angle+71*Math.PI/180)),expected=x>=8&&x<48&&y>=3&&y<23&&dist<=30?(.2+.8*wave)*.7/(1+(dist/6)**4):0;assert.ok(Math.abs(q[0]-expected)<2e-6,`${q[0]} != ${expected}`);assert.deepEqual(q.slice(2),[cx,cy]);q[0]=-999;assert.notEqual(s.fieldSample(1,x,y)[0],-999);}s.render();assert.deepEqual(s.snapshot(),before);}
 for(const extra of [{falloff:9},{continuous:1},{velocity:[1]},{surface:{x:0,y:0,width:0,height:1}}]){const before=s.snapshot();assert.throws(()=>s.command({...cmd,...extra}));assert.deepEqual(s.snapshot(),before);}
 for(const [id,x,y] of [[0,0,0],[1,NaN,0],[1,0,Infinity]])assert.throws(()=>s.fieldSample(id,x,y));
 assert.equal(s.fieldSample(123,0,0),null);s.command({op:'remove-field',id:1});assert.equal(s.fieldSample(1,18,8),null);
 console.log('PASS actual WASM independent continuous field controls, motion/clip, owned output, purity and atomic rejection');
}finally{s.close();}
