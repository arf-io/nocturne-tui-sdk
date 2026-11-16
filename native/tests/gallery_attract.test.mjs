// Gallery attract policy: shuffle-bag rotation, eligibility and provenance captions.
// Pure module tests with a seeded generator; the built-gallery boundary is tested in
// gallery_attract_built.test.mjs.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createAttractRotation,isAttractRecipe,recipeProvenance,GALLERY_SCENIC_FEATURES} from '../bindings/typescript/gallery_attract.mjs';

function mulberry32(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
const library=size=>Array.from({length:size},(_,i)=>({id:'recipe-'+i,name:'Recipe '+i}));
const SIZES=[2,3,7,129];
const SEEDS=Array.from({length:40},(_,i)=>i*7919+1);
// Uninterrupted attract: each call passes the recipe currently on screen.
function rotate(recipes,seed,draws,initial){
 const rotation=createAttractRotation(recipes,mulberry32(seed)),shown=[];let current=initial;
 for(let i=0;i<draws;i++){const next=rotation.next(current);assert.ok(next,'rotation stopped at draw '+i);shown.push(next.id);current=next.id;}
 return shown;
}

test('every recipe appears exactly once per bag across many bags and seeds',()=>{
 for(const size of SIZES){const recipes=library(size),ids=recipes.map(r=>r.id).sort();
  for(const seed of SEEDS){const shown=rotate(recipes,seed,size*6,recipes[0].id);
   for(let bag=0;bag<6;bag++)assert.deepEqual(shown.slice(bag*size,(bag+1)*size).sort(),ids,`size ${size} seed ${seed} bag ${bag}`);}}
});

test('no recipe is shown twice in a row, including the first draw and every bag boundary',()=>{
 for(const size of SIZES){const recipes=library(size);
  for(const seed of SEEDS){const shown=rotate(recipes,seed,size*6,recipes[0].id);
   assert.notEqual(shown[0],recipes[0].id,`size ${size} seed ${seed} repeated the initial recipe`);
   for(let i=1;i<shown.length;i++)assert.notEqual(shown[i],shown[i-1],`size ${size} seed ${seed} repeated at draw ${i}`);}}
});

test('the bag-boundary hazard is real for an unguarded shuffle under the same seeds',()=>{
 // A plain refill shuffle starts a new bag with the previous bag's last recipe about 1/size of the time.
 const plainBags=(size,seed,bags)=>{const random=mulberry32(seed),out=[];for(let b=0;b<bags;b++){const bag=library(size).map(r=>r.id);for(let i=bag.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[bag[i],bag[j]]=[bag[j],bag[i]];}out.push(...bag);}return out;};
 let collisions=0;for(const seed of SEEDS){const shown=plainBags(3,seed,6);for(let b=1;b<6;b++)if(shown[b*3]===shown[b*3-1])collisions++;}
 assert.ok(collisions>0,'seeds never exercise a boundary repeat; the guard test would be vacuous');
});

test('a seeded generator reproduces the order and different seeds differ',()=>{
 const recipes=library(129);
 assert.deepEqual(rotate(recipes,2030,129*3,'recipe-0'),rotate(recipes,2030,129*3,'recipe-0'));
 assert.notDeepEqual(rotate(recipes,2030,129,'recipe-0'),rotate(recipes,2031,129,'recipe-0'));
});

// Random order, not merely complete bags: every refill is a fresh shuffle of the library. These
// statistics are computed from seeded draws, so each bound is checked deterministically; for a
// uniform shuffle of 129 recipes the observed values sit far inside them.
const LARGE=129,BAGS=6;
function libraryBags(seed){
 const shown=rotate(library(LARGE),seed,LARGE*BAGS,'recipe-0').map(id=>Number(id.slice('recipe-'.length)));
 return Array.from({length:BAGS},(_,bag)=>shown.slice(bag*LARGE,(bag+1)*LARGE));
}

test('an exhausted bag is reshuffled: consecutive bags are different orders',()=>{
 // Two independent shuffles agree in about one position; a replayed order agrees in all of them.
 for(const seed of SEEDS){const bags=libraryBags(seed);
  for(let bag=1;bag<BAGS;bag++){const same=bags[bag].filter((index,k)=>index===bags[bag-1][k]).length;
   assert.ok(same<=10,`seed ${seed}: bag ${bag} repeats ${same} of ${LARGE} positions of bag ${bag-1}`);}}
});

test('bag order is not library order from a random start or a fixed stride',()=>{
 // A rotation or stride walk has one library step between neighbours; a shuffle has about 0.63 n.
 for(const seed of SEEDS)for(const [bag,order] of libraryBags(seed).entries()){
  const steps=new Set();for(let k=1;k<LARGE;k++)steps.add((order[k]-order[k-1]+LARGE)%LARGE);
  assert.ok(steps.size>=LARGE/4,`seed ${seed} bag ${bag}: only ${steps.size} distinct library steps between neighbours`);
 }
});

test('no recipe is pinned to a bag position across seeds and bags',()=>{
 const placements=new Map(),first=new Set(),placeOfFirstRecipe=new Set();let samples=0;
 for(const seed of SEEDS){const bags=libraryBags(seed);
  for(const order of bags){samples++;order.forEach((index,k)=>placements.set(index+'@'+k,(placements.get(index+'@'+k)??0)+1));}
  // The second bag starts after an ordinary boundary, not after the caller's initial recipe.
  first.add(bags[1][0]);placeOfFirstRecipe.add(bags[1].indexOf(0));
 }
 const [placement,count]=[...placements].reduce((worst,entry)=>entry[1]>worst[1]?entry:worst);
 assert.ok(count<=samples/4,`library index@position ${placement} occurs in ${count} of ${samples} bags`);
 assert.ok(first.size>=SEEDS.length/2,`only ${first.size} distinct opening recipes across ${SEEDS.length} seeds`);
 assert.ok(placeOfFirstRecipe.size>=SEEDS.length/2,`the first library recipe took only ${placeOfFirstRecipe.size} distinct positions across ${SEEDS.length} seeds`);
});

test('randomness is injected: Math.random is never consulted and invalid sources are rejected',()=>{
 assert.throws(()=>createAttractRotation(library(3)),TypeError);
 assert.throws(()=>createAttractRotation(library(3),0.5),TypeError);
 const original=Math.random;Math.random=()=>{throw new Error('pure rotation consulted Math.random');};
 try{assert.equal(rotate(library(7),9,7*4,undefined).length,28);}finally{Math.random=original;}
 for(const bad of [()=>1,()=>-0.1,()=>Number.NaN,()=>'0.5'])assert.throws(()=>createAttractRotation(library(3),bad).next(undefined),RangeError);
});

test('recipe identities must be unique and nonempty',()=>{
 assert.throws(()=>createAttractRotation([{id:'same'},{id:'same'}],mulberry32(1)));
 assert.throws(()=>createAttractRotation([{id:''},{id:'other'}],mulberry32(1)));
 assert.throws(()=>createAttractRotation([{name:'no identity'}],mulberry32(1)));
 assert.throws(()=>createAttractRotation('recipes',mulberry32(1)),TypeError);
});

test('degenerate libraries: empty and single-recipe rotations never repeat the screen',()=>{
 assert.equal(createAttractRotation([],mulberry32(1)).next(undefined),null);
 const single=createAttractRotation([{id:'only'}],mulberry32(1));
 assert.equal(single.next('only'),null);
 assert.equal(single.next('elsewhere').id,'only');
 assert.equal(single.next('only'),null);
});

test('two recipes strictly alternate for every seed',()=>{
 for(const seed of SEEDS){const shown=rotate(library(2),seed,40,undefined);for(let i=2;i<shown.length;i++)assert.equal(shown[i],shown[i-2],`seed ${seed} draw ${i}`);}
});

test('a recipe already on screen after manual exploration is not drawn again in that bag',()=>{
 const size=12,recipes=library(size),ids=recipes.map(r=>r.id);
 for(const seed of SEEDS){
  const rotation=createAttractRotation(recipes,mulberry32(seed)),bag=[];let current;
  for(let i=0;i<4;i++){const next=rotation.next(current);bag.push(next.id);current=next.id;}
  // The visitor picks a recipe that this bag has not reached, then resumes demos.
  const manual=ids.find(id=>!bag.includes(id));current=manual;
  const rest=[];for(let i=0;i<size-bag.length-1;i++){const next=rotation.next(current);assert.notEqual(next.id,current);rest.push(next.id);current=next.id;}
  assert.deepEqual([...bag,manual,...rest].sort(),[...ids].sort(),`seed ${seed}: the bag skipped or repeated a recipe`);
  const fresh=[];for(let i=0;i<size;i++){const next=rotation.next(current);assert.notEqual(next.id,current);fresh.push(next.id);current=next.id;}
  assert.deepEqual(fresh.sort(),[...ids].sort(),`seed ${seed}: the following bag is not a full permutation`);
 }
});

test('a recipe outside the rotation on screen does not disturb the bag',()=>{
 const recipes=library(5),rotation=createAttractRotation(recipes,mulberry32(77)),shown=[];
 for(let i=0;i<5;i++)shown.push(rotation.next('study-not-in-rotation').id);
 assert.deepEqual(shown.sort(),recipes.map(r=>r.id).sort());
});

test('attract eligibility keeps classic, original and isolated scenic demos, not parameter probes',()=>{
 assert.deepEqual([...GALLERY_SCENIC_FEATURES],['shared-ocean','waterfall-composition','road-composition','garden-composition']);
 assert.equal(isAttractRecipe({id:'autumn',name:'Autumn Drift',commands:[]}),true);
 assert.equal(isAttractRecipe({id:'rc2-windows-application',demo:true,mode:'application',demonstrates:{feature:'rc2-window-compositions'}}),true);
 assert.equal(isAttractRecipe({id:'rc2-windows-isolated',demo:false,mode:'isolated',demonstrates:{feature:'rc2-window-compositions'}}),false);
 for(const feature of GALLERY_SCENIC_FEATURES){
  assert.equal(isAttractRecipe({id:feature+'-isolated',mode:'isolated',demonstrates:{feature}}),true,feature);
  assert.equal(isAttractRecipe({id:feature+'-application',mode:'application',demonstrates:{feature}}),false,feature);
 }
 assert.equal(isAttractRecipe({id:'study-weather-pearl-bloom-isolated',mode:'isolated',demonstrates:{effect:'weather/pearl-bloom',contract:'ParticleEmitter'}}),false);
});

test('provenance names the edition, component or commit, source identity and stable recipe identity',()=>{
 assert.equal(recipeProvenance({id:'rc2-windows-application',name:'Window Theatre / application',demo:true,provenance:{release:'0.9.0-rc.2',component:'Window Theatre',htmlSha256:'375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385'}}),
  '0.9.0-rc.2 / Window Theatre · rc2-windows-application');
 assert.equal(recipeProvenance({id:'first-prompt-black-creme',name:'Prompt / Black Creme / stardust',demo:true,provenance:{release:'Nocturne v0.1',sourceCommit:'7dccd5ec04a6b6cb81c67e765bae4c23954a6b0a',kernelSha256:'11911d3466a9fe9a29c5c2672089c7a24fa6a288bf02'}}),
  'Nocturne v0.1 / commit 7dccd5ec04a6 · first-prompt-black-creme');
 assert.equal(recipeProvenance({id:'original-pearl-cascade',name:'Pearl Cascade',demo:true,originalScenic:'pearl-cascade',provenance:{release:'Workbench RC2',component:'Original Pearl Cascade world painter and controls',sourceIdentity:'scene:waterfall',sourceSha256:'ea65'}}),
  'Workbench RC2 / Original Pearl Cascade world painter and controls / scene:waterfall · original-pearl-cascade');
 assert.equal(recipeProvenance({id:'waterfall-composition-delayed-isolated',mode:'isolated',demonstrates:{feature:'waterfall-composition',treatment:'delayed'}}),
  'API study / waterfall-composition · waterfall-composition-delayed-isolated');
 // A catalogue identity is historical naming, not an accepted faithful port: it is labelled as such.
 assert.equal(recipeProvenance({id:'study-weather-pearl-bloom-isolated',mode:'isolated',demonstrates:{effect:'weather/pearl-bloom',contract:'ParticleEmitter'},catalogueEffect:'weather/pearl-bloom',sourceIdentity:'weather/studio.nova'}),
  'API study / weather/pearl-bloom / catalogue identity weather/studio.nova · study-weather-pearl-bloom-isolated');
 assert.equal(recipeProvenance({id:'autumn',name:'Autumn Drift',subtitle:'',commands:[]}),'SDK recipe · autumn');
 assert.equal(recipeProvenance({id:'bare-provenance',provenance:{}}),'Recipe · bare-provenance');
 for(const recipe of [{},{id:''},{id:7},null])assert.throws(()=>recipeProvenance(recipe),TypeError);
});
