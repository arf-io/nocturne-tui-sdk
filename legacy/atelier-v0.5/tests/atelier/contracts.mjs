import test from 'node:test';
import assert from 'node:assert/strict';
import { layoutGraph, GraphLayoutJob, CameraRig } from '../../dist/typescript/spatial.js';
import { TEXT_EFFECTS, DEFAULT_TEXT_OPTIONS, sampleText, textDuration, TextPlayer } from '../../dist/typescript/text_fx.js';
import { sampleBurst, DEFAULT_PARTICLE_OPTIONS } from '../../dist/typescript/particles.js';
import { WindowManager, WINDOW_EFFECTS, windowMask, validatePolygon } from '../../dist/typescript/window_fx.js';
const graph={nodes:['a','b','c','d','alone'].map(id=>({id,label:id})),edges:[{source:'a',target:'b'},{source:'a',target:'c'},{source:'b',target:'d'},{source:'c',target:'d'}]};
for(const dimensions of [2,3])for(const algorithm of ['layered','force','radial'])test(`${algorithm}/${dimensions} deterministic, finite, input-order independent`,()=>{
 const a=layoutGraph(graph,{dimensions,algorithm,seed:42,iterations:80});
 const b=layoutGraph({nodes:[...graph.nodes].reverse(),edges:[...graph.edges].reverse()},{dimensions,algorithm,seed:42,iterations:80});
 assert.deepEqual(a,b); assert.equal(a.nodes.length,5); assert.equal(a.edges.length,4);
 assert.ok(a.nodes.every(n=>Number.isFinite(n.x+n.y+n.z)));if(dimensions===2)assert.ok(a.nodes.every(n=>n.z===0));
});
test('shared-parent nodes keep one identity and directed ranks',()=>{const r=layoutGraph(graph,{algorithm:'layered',dimensions:3});const n=Object.fromEntries(r.nodes.map(n=>[n.id,n]));assert.ok(n.d.rank>n.b.rank);assert.ok(n.d.rank>n.c.rank);assert.equal(r.nodes.filter(n=>n.id==='d').length,1);});
test('cycles condense explicitly or reject; never silently dropped',()=>{const g={nodes:[{id:'a'},{id:'b'},{id:'c'}],edges:[{source:'a',target:'b'},{source:'b',target:'a'},{source:'b',target:'c'}]};assert.throws(()=>layoutGraph(g,{cyclePolicy:'reject'}),/cycl/i);const r=layoutGraph(g);assert.equal(r.edges.length,3);assert.ok(r.cycles.some(v=>v.includes('a')&&v.includes('b')));});
test('bad graph input rejects atomically',()=>{for(const g of [{nodes:[{id:'a'},{id:'a'}],edges:[]},{nodes:[{id:'a'}],edges:[{source:'a',target:'no'}]},{nodes:[{id:'a',width:NaN}],edges:[]}])assert.throws(()=>layoutGraph(g));});
test('empty and pinned layouts',()=>{assert.equal(layoutGraph({nodes:[],edges:[]}).nodes.length,0);const r=layoutGraph({nodes:[{id:'x',pin:{x:5,y:7,z:3}},{id:'y'}],edges:[]},{dimensions:3,algorithm:'force'});assert.deepEqual([r.nodes[0].x,r.nodes[0].y,r.nodes[0].z],[5,7,3]);});
test('bounded job stepping matches full solve',()=>{const o={algorithm:'force',dimensions:3,seed:123,iterations:93};const j=new GraphLayoutJob(graph,o);while(!j.done)j.step(7);assert.deepEqual(j.result(),layoutGraph(graph,o));});
test('camera orbit, pan, dolly and fit are visibly distinct',()=>{const c=new CameraRig();const p={x:3,y:2,z:0};const before=c.project(p,120,40);c.orbit(20,10);assert.notDeepEqual(c.project(p,120,40),before);const pos=c.position();c.pan(1,2);assert.notDeepEqual(c.position(),pos);const distance=c.distance;c.dolly(.7);assert.ok(c.distance<distance);c.fit(layoutGraph(graph).bounds,120,40);assert.ok(graph.nodes.length);assert.ok(Number.isFinite(c.distance));});
for(const effect of TEXT_EFFECTS)test(`text ${effect} resolves exactly and hides completely`,()=>{
 const opt={...DEFAULT_TEXT_OPTIONS,effect,seed:67};const text='THE QUICK 67%';const duration=textDuration(text,opt);
 const end=sampleText(text,'show',duration+1,opt);assert.equal(end.map(g=>g.glyph).join(''),text);assert.ok(end.every(g=>g.opacity===1&&g.x===g.index&&g.y===0));
 assert.ok(sampleText(text,'hide',duration+1,opt).every(g=>g.opacity===0));assert.deepEqual(sampleText(text,'show',379,opt),sampleText(text,'show',379,opt));
});
test('rain has independent character origins and velocities',()=>{const p=sampleText('RAIN FROM DIFFERENT SKIES','show',320,{...DEFAULT_TEXT_OPTIONS,effect:'rain',staggerMs:0});assert.ok(new Set(p.map(g=>g.y.toFixed(2))).size>10);});
test('text reverse begins at current glyph poses',()=>{const p=new TextPlayer('REVERSE',{...DEFAULT_TEXT_OPTIONS,effect:'rain'});p.show(0);const a=p.sample(340);p.hide(340);const b=p.sample(340);assert.deepEqual(a,b);});
test('local typing cannot inherit animated reveal',()=>{const out=sampleText('NOW','show',0,{...DEFAULT_TEXT_OPTIONS,local:true,effect:'rain'});assert.equal(out.map(x=>x.glyph).join(''),'NOW');assert.ok(out.every(x=>x.opacity===1&&x.y===0));});
test('bad typography options reject',()=>{assert.throws(()=>sampleText('x','show',0,{...DEFAULT_TEXT_OPTIONS,durationMs:NaN}));assert.throws(()=>sampleText('x','show',0,{...DEFAULT_TEXT_OPTIONS,batchSize:0}));});
test('embers rise and subsequently fall',()=>{const e={id:1,x:30,y:20,atMs:0,kind:'embers'};const a=sampleBurst(e,250,DEFAULT_PARTICLE_OPTIONS),b=sampleBurst(e,3200,DEFAULT_PARTICLE_OPTIONS);assert.ok(a.points[0].y<20);assert.ok(b.points[0].y>a.points[0].y);});
test('sparks are branched segments, novae include ejecta',()=>{const spark=sampleBurst({id:8,x:30,y:20,atMs:0,kind:'sparks'},100,DEFAULT_PARTICLE_OPTIONS);assert.ok(spark.segments.length>10);const nova=sampleBurst({id:8,x:30,y:20,atMs:0,kind:'nova'},160,DEFAULT_PARTICLE_OPTIONS);assert.ok(nova.segments.length>10);assert.ok(nova.points.length>15);assert.ok(nova.glows.length);});
test('particle replay is pure and event lifetime is bounded',()=>{const e={id:9,x:20,y:10,atMs:100,kind:'nova'};assert.deepEqual(sampleBurst(e,700,DEFAULT_PARTICLE_OPTIONS),sampleBurst(e,700,DEFAULT_PARTICLE_OPTIONS));assert.equal(sampleBurst(e,99999,DEFAULT_PARTICLE_OPTIONS).points.length,0);});
for(const effect of WINDOW_EFFECTS)test(`window ${effect} reversible and restorable`,()=>{const w=new WindowManager();const id=w.add({title:'T',x:4,y:4,width:40,height:16});w.configure({effect,durationMs:800});w.hide(id,0);const a=w.sample(id,300);w.show(id,300);assert.deepEqual(w.sample(id,300),a);assert.equal(w.sample(id,2000).visibility,1);assert.ok(w.tasks().some(x=>x.id===id));});
test('shape hit mask respects holes/outside',()=>{assert.equal(windowMask('ellipse',0,0),false);assert.equal(windowMask('ellipse',.5,.5),true);assert.equal(windowMask('diamond',.5,.5),true);assert.throws(()=>validatePolygon([[0,0],[1,1],[0,1],[1,0]]));});
test('window tool styles have large color-coded controls',()=>{const w=new WindowManager();const id=w.add({title:'tools',x:4,y:5,width:52,height:18});for(const chrome of ['mac','windows','gnome','custom']){w.configure({chrome});const c=w.controls(id);assert.equal(c.length,4);assert.ok(c.every(t=>t.width>=5&&t.height>=2));assert.equal(new Set(c.map(t=>t.color)).size,4);}});

test('text reconfiguration preserves current poses when switching to an exit effect',()=>{
 const player=new TextPlayer('CONTINUITY',{effect:'rain',durationMs:1200});player.show(0);
 const before=player.sample(420);player.configure({effect:'flipboard'},420);player.hide(420);
 assert.deepEqual(player.sample(420),before);
});
test('roll-body is a reversible tween rather than an instant clipping flag',()=>{
 const manager=new WindowManager();const id=manager.add({title:'roll',x:2,y:6,width:50,height:24});
 manager.toggleRoll(id,0);const halfway=manager.sample(id,350);assert.ok(halfway.bodyScale>0&&halfway.bodyScale<1);
 manager.toggleRoll(id,350);assert.equal(manager.sample(id,350).bodyScale,halfway.bodyScale);
 assert.equal(manager.sample(id,5000).bodyScale,1);
});
test('layered 2D layout includes node dimensions in inter-rank clearance',()=>{
 const g={nodes:[{id:'a',height:24,width:10},{id:'b',height:18,width:9},{id:'c',height:10,width:12}],edges:[{source:'a',target:'b'},{source:'a',target:'c'}]},l=layoutGraph(g,{algorithm:'layered',dimensions:2,rankGap:2,nodeGap:0});
 for(let i=0;i<l.nodes.length;i++)for(let j=i+1;j<l.nodes.length;j++){const a=l.nodes[i],b=l.nodes[j];assert.ok(Math.abs(a.x-b.x)>=(a.width+b.width)/2-1e-8||Math.abs(a.y-b.y)>=(a.height+b.height)/2-1e-8);}
});
test('projection snapshots preserve a camera sample after later movement',()=>{
 const c=new CameraRig(),project=c.projector(120,40),point={x:2,y:3,z:5},before=project(point);assert.deepEqual(before,c.project(point,120,40));c.look(12,8);assert.deepEqual(before,project(point));assert.notDeepEqual(before,c.project(point,120,40));
});
test('dock restoration also recovers a faded and rolled window',()=>{
 const wm=new WindowManager(),id=wm.add({title:'recover',x:2,y:5,width:40,height:18});wm.action(id,'fade',0);wm.toggleRoll(id,0);wm.hide(id,0,true);wm.restore(id,2000);const state=wm.sample(id,5000);assert.equal(state.visibility,1);assert.equal(state.alpha,1);assert.equal(state.bodyScale,1);assert.equal(wm.get(id).mode,'normal');
});

test('nova core is layered after ejecta so the exploding glyph cannot be overwritten',()=>{
 const frame=sampleBurst({id:99,x:12,y:9,atMs:0,kind:'nova'},70,{count:80});
 assert.equal(frame.points.at(-1).glyph,'✶');assert.equal(frame.points.at(-1).x,12);assert.equal(frame.points.at(-1).y,9);
});

test('nova defaults to ejecta and a core, with a shockwave only when requested',()=>{
 const frame=sampleBurst({id:5,x:12,y:9,atMs:0,kind:'nova'},600);
 assert.ok(frame.segments.length>10);assert.equal(frame.glows.filter(g=>g.ring).length,0);
 assert.ok(sampleBurst({id:5,x:12,y:9,atMs:0,kind:'nova'},600,{shockwave:.15}).glows.some(g=>g.ring));
});
