import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const s=await NativeScene.create(wasm);let kinds=0;
try{
 s.command({op:'resize',width:512,height:160});s.command({op:'prompt',active:false});
 for(const kind of ['text','box','rule','button','item','cursor','progress','bars','pie','donut','scatter','line','digits','edge','checkbox','radio','select','scrollbar']){
  s.command({op:'widget',id:1,kind,x:300,y:110,width:300,height:120,value:.5,data:[.2,.4,.6,.8],text:'Large retained layout',alpha:.7});
  const saved=s.snapshot();s.render();assert.deepEqual(s.snapshot(),saved);s.restore(saved);assert.deepEqual(s.snapshot(),saved);kinds++;
 }
 s.command({op:'widget',id:1,kind:'box',x:-1000000000,y:-1000000000,width:2000000000,height:2000000000});
 let saved=s.snapshot();s.render();assert.deepEqual(s.snapshot(),saved);s.restore(saved);
 s.command({op:'define',path:'/width',value:2000000000,binding:{family:'widget',id:1,field:'width'}});s.command({op:'set',path:'/width',expression:{add:[1900000000,100000000]}});
 assert.equal(s.info().values['/width'],2000000000);saved=s.snapshot();assert.throws(()=>s.command({op:'set',path:'/width',value:2147483648}));assert.deepEqual(s.snapshot(),saved);
 s.command({op:'area',id:1,x:300,y:110,width:500,height:200});s.command({op:'status',id:1,area:1,text:'Large notification layout',durationMs:0});
 s.command({op:'text',id:1,x:350,y:120,width:1024,text:'Large retained text',durationMs:0});s.command({op:'indicator',id:1,x:400,y:130,sequence:'◐◓◑◒'});
 s.command({op:'window',id:1,width:1000,height:1000,minColumns:300,maxColumns:1024,title:'Large panel',text:'Source survives replay'});
 saved=s.snapshot();s.render();assert.deepEqual(s.snapshot(),saved);s.restore(saved);assert.deepEqual(s.snapshot(),saved);
 s.command({op:'prompt',active:true,mode:'grow',minRows:120,maxRows:1000});s.command({op:'draft',text:'Large prompt source',emitWeather:false});
 saved=s.snapshot();s.render();s.restore(saved);assert.deepEqual(s.snapshot(),saved);
 s.command({op:'prompt',active:false});s.command({op:'resize',width:1600,height:20});s.command({op:'pointer',phase:'down',x:1500,y:10});saved=s.snapshot();s.restore(saved);assert.deepEqual(s.snapshot(),saved);
 console.log(JSON.stringify({runtime:'actual WASM',widgetKinds:kinds,largePanelFamilies:true,billionCellRectangle:true,largeNumericBinding:true,renderPure:true,snapshotReplay:true,atomicRejection:true,wasmSha256:createHash('sha256').update(wasm).digest('hex')}));
}finally{s.close();}
