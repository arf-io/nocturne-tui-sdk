import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const scene=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
try {
 const paths=process.argv.slice(2);
 if(!paths.length)scene.command({op:'cell-art',id:1,width:1,height:1,x:2,y:2,layer:'overlay',cells:[[65,0xff0000,0x0000ff]]});
 for(const path of paths){scene.command({op:'reset'});const commands=JSON.parse(readFileSync(path,'utf8'));for(const command of commands)scene.command(command);const art=commands.find(c=>c.op==='cell-art');const frame=scene.render();for(let k=0;k<art.cells.length;k++)if(art.cells[k][0]){const index=((art.y+Math.floor(k/art.width))*frame.width+art.x+k%art.width)*4;assert.deepEqual(Array.from(frame.cells.slice(index,index+3)),art.cells[k]);}}
 scene.command({op:'schedule',id:1,atUs:100000,command:{op:'cell-art',id:1,x:9,alpha:.75}});scene.advanceTo(200000);assert.equal(scene.info().cellArt[0].x,9);
 const saved=scene.snapshot();scene.render();assert.deepEqual(scene.snapshot(),saved);
 scene.command({op:'cell-art',id:1,alpha:.5,x:7});scene.restore(saved);assert.deepEqual(scene.snapshot(),saved);
 assert.throws(()=>scene.command({op:'cell-art',id:1,width:2,cells:[[65,1,2]]}));assert.deepEqual(scene.snapshot(),saved);
 console.log(JSON.stringify({runtime:'actual WASM',tdfCases:paths.length,exactNativeCells:true,renderPure:true,snapshotReplay:true}));
} finally {scene.close();}
