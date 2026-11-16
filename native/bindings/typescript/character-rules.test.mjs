import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const wasm=readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url));
const unicodeOrder=await NativeScene.create(wasm);
try{
 unicodeOrder.command({op:'resize',width:4,height:2});
 unicodeOrder.command({op:'material',id:7,space:'rgb',channels:{r:1,g:0,b:0},alpha:1});
 unicodeOrder.command({op:'character-rule',rule:{id:'\ue000',foregroundEffects:[{type:'invert'}]}});
 unicodeOrder.command({op:'character-rule',rule:{id:'\u{10000}',foreground:7,compositeSpace:'srgb',protectLocalInk:false}});
 const saved=unicodeOrder.snapshot();
 for(let replay=0;replay<2;replay++){
  const frame=unicodeOrder.render();for(let at=1;at<frame.cells.length;at+=4)assert.equal(frame.cells[at],0x00ffff);
  assert.deepEqual(unicodeOrder.snapshot(),saved);unicodeOrder.restore(saved);
 }
}finally{unicodeOrder.close();}
const late=await NativeScene.create(wasm);
try{
 late.command({op:'resize',width:4,height:2});const baseline=late.render().bytes;
 const rule={id:'late-material',foreground:7,protectLocalInk:false,compositeSpace:'srgb'};
 late.command({op:'character-rule',rule});const dormant=late.snapshot();
 assert.deepEqual(late.render().bytes,baseline);late.restore(dormant);
 assert.deepEqual(late.snapshot(),dormant);assert.deepEqual(late.info().characterRules,[rule]);
 assert.deepEqual(late.render().bytes,baseline);
 late.command({op:'material',id:7,space:'rgb',channels:{r:1,g:0,b:0},alpha:1});
 const live=late.snapshot(),frame=late.render();
 for(let at=1;at<frame.cells.length;at+=4)assert.equal(frame.cells[at],0xff0000);
 assert.deepEqual(late.snapshot(),live);
 late.restore(dormant);assert.deepEqual(late.render().bytes,baseline);
 assert.deepEqual(late.info().characterRules,[rule]);
}finally{late.close();}
const patches=await NativeScene.create(wasm);
try{
 patches.command({op:'resize',width:4,height:2});
 patches.command({op:'character-region',region:{id:'selected',path:'/selected',state:'selected',cells:[0]}});
 const baseline=patches.render().cells;
 patches.command({op:'character-rule',rule:{id:'deferred',foreground:7,background:8,foregroundEffects:[{type:'invert'}],compositeSpace:'srgb',protectLocalInk:false,states:{selected:{enabled:false}}}});
 patches.command({op:'material',id:7,space:'rgb',channels:{r:1,g:0,b:0}});
 const dormant=patches.snapshot();assert.deepEqual(patches.render().cells,baseline);
 const material={op:'material',id:8,space:'rgb',channels:{r:0,g:0,b:1}};
 assert.throws(()=>patches.command({op:'batch',commands:[material,{op:'character-rule',rule:{id:''}}]}));
 assert.deepEqual(patches.snapshot(),dormant);assert.deepEqual(patches.render().cells,baseline);
 patches.command(material);const live=patches.snapshot(),frame=patches.render().cells;
 assert.deepEqual(frame.slice(0,4),baseline.slice(0,4));
 for(let at=4;at<frame.length;at+=4){assert.equal(frame[at+1],0x00ffff);assert.equal(frame[at+2],0x0000ff);assert.equal(frame[at],baseline[at]);assert.equal(frame[at+3],baseline[at+3]);}
 assert.deepEqual(patches.snapshot(),live);patches.restore(dormant);assert.deepEqual(patches.render().cells,baseline);
}finally{patches.close();}
const s=await NativeScene.create(wasm);
try{
 assert.throws(()=>s.inspectCharacterCell(0,0),/Render required/);
 const pureStart=s.snapshot();
 for(const [space,expected] of [0x808080,0xbcbcbc,0x636363,0x636363].entries()){
  assert.deepEqual(s.compositeInSpace(0,0xffffff,space,65535,32768),{rgb:expected,alpha:65535});
  assert.deepEqual(s.compositeInSpace(0x123456,0xabcdef,space,65535,0),{rgb:0x123456,alpha:65535});
 }
 assert.throws(()=>s.compositeInSpace(0,0xffffff,4));assert.deepEqual(s.snapshot(),pureStart);
 const baseline=s.render(),expected=new Uint32Array(baseline.cells);
 for(let x=2;x<6;x++)expected[(2*baseline.width+x)*4+1]^=0xffffff;
 const rule={id:'invert',selector:{rect:{x:2,y:2,width:4,height:1}},compositeSpace:'srgb',foregroundEffects:[{type:'invert'}]};
 s.command({op:'character-rule',rule});const saved=s.snapshot();
 assert.deepEqual(s.info().characterRules,[rule]);assert.deepEqual(s.render().cells,expected);assert.deepEqual(s.snapshot(),saved);
 s.command({op:'character-rule',rule:{id:'invert',enabled:false}});assert.deepEqual(s.render().cells,baseline.cells);
 s.restore(saved);assert.deepEqual(s.render().cells,expected);assert.deepEqual(s.snapshot(),saved);
 for(const invalid of [{id:''},{id:'bad',foreground:9999},{id:'bad',foregroundEffects:[{type:'gamma',value:0}]},{id:'bad',states:{active:{priority:1}}}]){
  assert.throws(()=>s.command({op:'character-rule',rule:invalid}));assert.deepEqual(s.snapshot(),saved);
 }
 assert.throws(()=>s.command({op:'batch',commands:[{op:'remove-character-rule',id:'invert'},{op:'character-rule',rule:{id:''}}]}));
 assert.deepEqual(s.snapshot(),saved);
 s.command({op:'remove-character-rule',id:'invert'});s.command({op:'remove-character-rule',id:'invert'});
 assert.deepEqual(s.info().characterRules,[]);assert.deepEqual(s.render().cells,baseline.cells);
 const positions=[2*baseline.width+2,2*baseline.width+3];
 const region={id:'fragment',path:'/app/fragment',role:'user-text',state:'selected',cells:positions,indices:[7,9]};
 s.command({op:'character-region',region});
 s.command({op:'character-rule',rule:{id:'fragment-paint',selector:{path:'/app/fragment',indices:[9]},states:{selected:{foregroundEffects:[{type:'invert'}]}}}});
 const regional=new Uint32Array(baseline.cells);regional[positions[1]*4+1]^=0xffffff;
 const regionalSnapshot=s.snapshot();assert.deepEqual(s.render().cells,regional);assert.deepEqual(s.info().characterRegions,[region]);
 const inspected=s.inspectCharacterCell(3,2);assert.equal(inspected.path,'/app/fragment');assert.equal(inspected.index,9);assert.equal(inspected.state,'selected');
 assert.equal(inspected.glyph,regional[positions[1]*4]);assert.equal(inspected.id,regional[positions[1]*4+3]);
 assert.deepEqual(s.snapshot(),regionalSnapshot);
 s.command({op:'remove-character-region',id:'fragment'});assert.deepEqual(s.render().cells,baseline.cells);
 s.restore(regionalSnapshot);assert.throws(()=>s.inspectCharacterCell(3,2),/Render required/);assert.deepEqual(s.render().cells,regional);
 assert.deepEqual(s.inspectCharacterCell(3,2),inspected);
 assert.throws(()=>s.command({op:'character-region',region:{...region,indices:[7]}}));assert.deepEqual(s.snapshot(),regionalSnapshot);
 s.command({op:'remove-character-rule',id:'fragment-paint'});s.command({op:'remove-character-region',id:'fragment'});
 for(let start=0;start<128;start+=64)s.command({op:'batch',commands:Array.from({length:64},(_,offset)=>({op:'character-rule',rule:{id:`capacity-${start+offset}`,enabled:false}}))});
 const full=s.snapshot();assert.equal(s.info().characterRules.length,128);
 assert.throws(()=>s.command({op:'character-rule',rule:{id:'overflow'}}));assert.deepEqual(s.snapshot(),full);
 s.command({op:'character-rule',rule:{id:'capacity-127',priority:1,enabled:false}});assert.equal(s.info().characterRules.length,128);
 s.command({op:'remove-character-rule',id:'capacity-0'});s.command({op:'character-rule',rule:{id:'replacement',enabled:false}});
 assert.equal(s.info().characterRules.length,128);const reused=s.snapshot();s.restore(reused);assert.deepEqual(s.snapshot(),reused);
 console.log(JSON.stringify({runtime:'actual WASM',independentCellOracle:true,sourceOwnership:true,replacement:true,replay:true,purity:true,atomicRejection:true}));
}finally{s.close();}
