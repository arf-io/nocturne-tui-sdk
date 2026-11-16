import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {NativeScene} from './native_scene.mjs';
const s=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
s.command({op:'mesh',triangles:[{a:[-2,-2,0],b:[2,-2,0],c:[0,2,0]}]});s.command({op:'surface-thermal',triangleIndex:0,temperature:400,capacity:2,ambientTemperature:300,conductance:4});s.advanceTo(500000);const q=s.info().surfaceThermal.cells[0];assert.ok(Math.abs(q.temperature-300-100*Math.exp(-1))<1e-5);assert.ok(Math.abs(q.energy-q.initialEnergy-q.appliedEnergy-q.environmentEnergy)<1e-5);const checkpoint=s.snapshot();s.render();assert.deepEqual(s.snapshot(),checkpoint);s.command({op:'surface-thermal-power',triangleIndex:0,power:4});s.advanceTo(1000000);const expected=s.snapshot();s.restore(checkpoint);s.command({op:'surface-thermal-power',triangleIndex:0,power:4});s.advanceTo(1000000);assert.deepEqual(s.snapshot(),expected);s.command({op:'mesh',triangles:[]});assert.ok(s.info().surfaceThermal.exportedEnergy>0);s.close();console.log('PASS native WASM spatial thermal energy accounting');

const transfer=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
transfer.command({op:'mesh',triangles:[{a:[-2,-2,0],b:[2,-2,0],c:[0,2,0]},{a:[8,-2,0],b:[12,-2,0],c:[10,2,0]}]});transfer.command({op:'surface-thermal',triangleIndex:0,temperature:400,capacity:2});transfer.command({op:'surface-thermal',triangleIndex:1,temperature:300,capacity:4});transfer.command({op:'surface-thermal-transfer',fromTriangle:0,toTriangle:1,energy:100});const cells=transfer.info().surfaceThermal.cells;assert.equal(cells[0].temperature,350);assert.equal(cells[1].temperature,325);assert.equal(cells[0].energy+cells[1].energy,2000);for(const c of cells)assert.equal(c.energy,c.initialEnergy+c.appliedEnergy+c.environmentEnergy+c.importedEnergy-c.transferredEnergy);transfer.close();console.log('PASS native WASM conserved intercell heat transfer');

const conduction=await NativeScene.create(readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
conduction.command({op:'mesh',triangles:[{a:[-2,-2,0],b:[2,-2,0],c:[0,2,0]},{a:[8,-2,0],b:[12,-2,0],c:[10,2,0]}]});
conduction.command({op:'surface-thermal',triangleIndex:0,temperature:400,capacity:2});
conduction.command({op:'surface-thermal',triangleIndex:1,temperature:300,capacity:4});
conduction.command({op:'surface-thermal-link',id:1,fromTriangle:0,toTriangle:1,conductance:3});
const start=conduction.snapshot();conduction.advanceTo(500000);
const conducted=conduction.info().surfaceThermal.cells;
const difference=100/Math.pow(1+2.25/120,60);
assert.ok(Math.abs(conducted[0].temperature-(2000/6+2*difference/3))<1e-5);
assert.ok(Math.abs(conducted[1].temperature-(2000/6-difference/3))<1e-5);
assert.ok(Math.abs(conducted[0].energy+conducted[1].energy-2000)<1e-5);
const finish=conduction.snapshot();conduction.render();assert.deepEqual(conduction.snapshot(),finish);
conduction.restore(start);for(const time of [123456,250000,333333,500000])conduction.advanceTo(time);
assert.deepEqual(conduction.snapshot(),finish);conduction.close();console.log('PASS native WASM conserved conduction and partition replay');
