import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
import {NativeScene} from './native_scene.mjs';

// Execute the actual original JS closure, including its validator and sampler.
// Extraction only makes its existing return value available to the test.
const html = gunzipSync(readFileSync(new URL('../../tests/fixtures/original-rc2-workbench-docs.html.gz', import.meta.url)));
assert.equal(createHash('sha256').update(html).digest('hex'),
  '375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385');
const source = html.toString('utf8');
const start = 'const {TEXT_REVEALS,TEXT_HIDES,DEFAULT_TEXT_OPTIONS,TEXT_CONTROLS,validateTextOptions,textDuration,sampleText,TextActor}=(()=>{';
const end = 'return {TEXT_REVEALS,TEXT_HIDES,DEFAULT_TEXT_OPTIONS,TEXT_CONTROLS,validateTextOptions,textDuration,sampleText,TextActor};\n})();';
assert.equal(source.split(start).length, 2);
assert.equal(source.split(end).length, 2);
const first = source.indexOf(start) + start.length;
const last = source.indexOf(end, first) + end.length;
// The text closure imports the original shared math/validation helpers. Execute
// their complete unchanged closure too, rather than substituting host helpers.
const sharedStart = source.indexOf('const {TAU,clamp,fract,smooth,finite,hash32,randomAt,');
assert.ok(sharedStart >= 0, 'original shared-helper closure');
const sharedEnd = source.indexOf('\n})();', sharedStart) + '\n})();'.length;
assert.ok(sharedEnd > sharedStart, 'original shared-helper closure terminator');
const original = vm.runInNewContext(source.slice(sharedStart, sharedEnd) +
  '\n(()=>{' + source.slice(first, last), {}, {timeout: 5000});
const wasm = readFileSync(new URL('../../dist/nocturne_native.wasm', import.meta.url));
let samples = 0;
for (const effect of ['fall', 'ash']) for (const phase of ['reveal', 'hide']) {
  const options = original.validateTextOptions({effect,phase,durationMs:1000,
    staggerMs:20,jitterMs:0,batchSize:1,distanceRows:6,scatterCols:3,
    speedVariation:0,scrambleHz:10,cycles:2,wind:1,overshoot:.2,seed:42,
    easing:'smooth',originX:10,originY:15,width:120,hueSpread:10});
  const scene = await NativeScene.create(wasm, 2030);
  try {
    scene.command({op:'resize',width:120,height:40});
    scene.command({op:'text',id:4,text:'NODE',effect:'text/'+(effect==='fall'?'glyph-fall':'ash-type'),
      phase:phase==='reveal'?'show':'hide',phaseModel:'source',durationMs:1000,
      staggerMs:20,jitterMs:0,batchSize:1,distance:6,scatter:3,variation:0,
      scrambleHz:10,cycles:2,wind:1,overshoot:.2,seed:42,easing:'smooth',
      x:10,y:15,width:120,hueSpread:10});
    const initial = scene.snapshot(), frames = [];
    for (const time of [0,11,110,370,990,1800]) {
      scene.advanceTo(time*1000);
      const retained = scene.snapshot();
      const reference = original.sampleText('NODE',time,options);
      for (const [i, expected] of reference.entries()) {
        const actual = scene.textSample(4,i);
        assert.equal(actual[0], expected.glyph.codePointAt(0));
        assert.ok(Math.abs(actual[3]/65536-expected.x)<=2/65536, 'source x');
        assert.ok(Math.abs(actual[4]/65536-expected.y)<=2/65536, 'source y');
        assert.ok(Math.abs(actual[5]/1e6-expected.opacity)<=.000002, 'source opacity');
        assert.deepEqual(scene.textClusterSample(4,i).slice(3,7), actual.slice(3,7));
        samples++;
      }
      frames.push(scene.render().bytes.slice());
      assert.deepEqual(scene.snapshot(),retained,'sampling/render must be pure');
    }
    const final = scene.snapshot();
    for (const mode of ['unknown',null,1,true]) {
      assert.throws(()=>scene.command({op:'text',id:4,phaseModel:mode}));
      assert.deepEqual(scene.snapshot(),final,'invalid mode must be atomic');
    }
    scene.restore(initial);
    for (const [index,time] of [0,11,110,370,990,1800].entries()) {
      scene.advanceTo(time*1000);
      assert.deepEqual(scene.render().bytes,frames[index],'source replay frame');
    }
    assert.deepEqual(scene.snapshot(),final,'source replay state');
    assert.equal(scene.infoComplete().textRuns[0].phaseModel,'source');
  } finally { scene.close(); }
}
console.log('PASS original JavaScript versus current WASM source text phases: '+samples+' glyph poses');
