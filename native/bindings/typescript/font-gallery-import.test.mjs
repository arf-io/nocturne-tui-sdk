import assert from 'node:assert/strict';import{readFileSync}from'node:fs';
import{parseTdfCellArtImport}from'./font_gallery.mjs';import{NativeScene}from'./native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)),2030);
try{
 const art={op:'cell-art',id:1,width:1,height:1,cells:[[65,0xffffff,0x123456]],x:5,y:5,layer:'overlay'};
 s.command({op:'draft',text:'Native source stays intact',emitWeather:false});const source=s.info().prompt.text,clock=s.info().clock.timeUs;
 s.command(parseTdfCellArtImport(art));assert.equal(s.render().cells[(5*160+5)*4],65);const before=s.snapshot();
 for(const payload of [{op:'reset'},{op:'schedule',command:art},[art,{op:'reset'}],{...art,command:{op:'reset'}}]){assert.throws(()=>parseTdfCellArtImport(payload));assert.deepEqual(s.snapshot(),before);}
 const bad=parseTdfCellArtImport([art,{...art,id:2,alpha:2}]);assert.throws(()=>s.command(bad));assert.deepEqual(s.snapshot(),before,'last rejected cell-art keeps whole batch atomic');assert.equal(s.info().prompt.text,source);assert.equal(s.info().clock.timeUs,clock);
 console.log('PASS actual WASM TDF cell-art import, strict op boundary, atomic last-item rejection and source/clock preservation');
}finally{s.close();}
