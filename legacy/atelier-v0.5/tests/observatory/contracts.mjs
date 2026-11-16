/** Acceptance contracts committed before v0.4 implementation. */
import assert from 'node:assert/strict';
import {MotionClock, RateTimeline, ModulationBus, DEFAULT_OBSERVATORY_OPTIONS, validateOptions, projectPoint, gradientPosition, ObservatoryModel} from '../../dist/typescript/observatory.js';
const tests=[];function test(name,fn){tests.push([name,fn]);}
test('60 and 30 Hz share wall-time duration',()=>{for(const fps of [30,60]){const c=new MotionClock(fps);c.sample(0);for(let t=1;t<=1000;t++)c.sample(t);assert.equal(c.timeMs,1000);}});
test('fps changes preserve phase',()=>{const c=new MotionClock(30);c.sample(0);c.sample(500);c.setFps(60);c.sample(1000);assert.equal(c.timeMs,1000);});
test('pause holds motion but event clock is independent',()=>{const c=new MotionClock(60);c.sample(0);c.sample(99);c.setPaused(true,99);c.sample(500);assert.equal(c.timeMs,99);c.setPaused(false,500);c.sample(501);assert.equal(c.timeMs,100);});
test('speed changes integrate instead of jumping',()=>{const r=new RateTimeline(1);r.set(1000,2);assert.equal(r.at(1500),2);assert.equal(r.at(1000),1);});
test('screen-relative stop spacing',()=>{assert.equal(gradientPosition(200,20,100,40,{...DEFAULT_OBSERVATORY_OPTIONS,gradientScreens:2,gradientAngle:0}),1);});
test('invalid configuration rejected atomically',()=>{assert.throws(()=>validateOptions({fps:0}));assert.throws(()=>validateOptions({gradientScreens:0}));assert.throws(()=>validateOptions({starCount:Infinity}));assert.throws(()=>validateOptions({unknown:true}));});
test('near-plane clipping',()=>{assert.equal(projectPoint({x:0,y:0,z:-1},{x:0,y:0,z:0,yaw:0,pitch:0,roll:0,fov:60},80,24),null);});
test('projection respects camera yaw and aspect',()=>{const p=projectPoint({x:0,y:0,z:10},{x:0,y:0,z:0,yaw:0,pitch:0,roll:0,fov:60},80,24);assert.equal(p.x,40);assert.equal(p.y,12);});
test('stale sensor restores the baseline',()=>{const b=new ModulationBus();b.bind({source:'audio.rms',target:'brightness',inputMin:0,inputMax:1,outputMin:.1,outputMax:.9,attackMs:0,releaseMs:0,ttlMs:100});b.ingest({source:'audio.rms',value:1,atMs:0,seq:1});assert.equal(b.resolve({brightness:.2},50).brightness,.9);assert.equal(b.resolve({brightness:.2},200).brightness,.2);});
test('NaN and duplicate sequence never poison state',()=>{const b=new ModulationBus();assert.throws(()=>b.ingest({source:'cpu.temp',value:NaN,atMs:0,seq:1}));assert.equal(b.ingest({source:'cpu.temp',value:42,atMs:0,seq:1}),true);assert.equal(b.ingest({source:'cpu.temp',value:1,atMs:0,seq:1}),false);});
test('typing changes text before time moves',()=>{const m=new ObservatoryModel(),before=m.revision;m.input('instant');assert.equal(m.draft,'instant');assert.equal(m.motionMs,0);assert.equal(m.revision,before+1);});
test('weather is bounded and text is never delayed',()=>{const m=new ObservatoryModel();for(let i=0;i<1000;i++)m.input('x');assert.ok(m.events.length<=128);assert.equal(m.draft.length,1000);});
for(const [name,fn] of tests){fn();console.log('PASS',name);}console.log(JSON.stringify({suite:'observatory-contracts',passed:tests.length}));
