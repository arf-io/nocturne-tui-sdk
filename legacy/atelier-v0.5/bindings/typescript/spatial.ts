/** Deterministic, bounded graph layout and an explicit camera rig.
 * All lengths are world units; angles are degrees. No timers or rendering APIs.
 * The synchronous convenience solver and chunked job use identical iterations.
 */
import {clamp, finite, hash32, randomAt, Vec3} from './observatory.js';
export interface GraphNode {id:string;label?:string;width?:number;height?:number;pin?:Vec3}
export interface GraphEdge {source:string;target:string}
export interface Graph {nodes:GraphNode[];edges:GraphEdge[]}
export interface LayoutOptions {dimensions:2|3;algorithm:'layered'|'force'|'radial';seed:number;iterations:number;rankGap:number;nodeGap:number;depthGap:number;repulsion:number;spring:number;damping:number;cyclePolicy:'condense'|'reject'}
export interface PlacedNode extends GraphNode,Vec3 {label:string;width:number;height:number;rank:number;component:number}
export interface Bounds3 {min:Vec3;max:Vec3}
export interface GraphLayout {nodes:PlacedNode[];edges:GraphEdge[];cycles:string[][];bounds:Bounds3;warnings:string[];iterations:number;options:LayoutOptions}
export const DEFAULT_LAYOUT_OPTIONS:LayoutOptions={dimensions:3,algorithm:'layered',seed:7341,iterations:180,rankGap:7,nodeGap:3,depthGap:5,repulsion:42,spring:.055,damping:.76,cyclePolicy:'condense'};
const order=(a:string,b:string)=>a<b?-1:a>b?1:0;
export function idHash(id:string):number{let h=2166136261;for(const c of id)h=Math.imul(h^c.codePointAt(0)!,16777619);return hash32(h);}
export function layoutOptions(patch:Partial<LayoutOptions>={}):LayoutOptions{
 const o={...DEFAULT_LAYOUT_OPTIONS,...patch};for(const key of Object.keys(patch))if(!(key in DEFAULT_LAYOUT_OPTIONS))throw new RangeError('Unknown layout field '+key);
 if(![2,3].includes(o.dimensions)||!['layered','force','radial'].includes(o.algorithm)||!['condense','reject'].includes(o.cyclePolicy))throw new RangeError('layout enum');
 for(const [key,lo,hi]of [['seed',0,4294967295],['iterations',1,600],['rankGap',1,40],['nodeGap',0,30],['depthGap',0,30],['repulsion',0,300],['spring',0,1],['damping',0,.99]] as const)finite(o[key],lo,hi,key);
 if(!Number.isInteger(o.seed)||!Number.isInteger(o.iterations))throw new RangeError('seed / iterations must be integers');return o;
}
/** Validate and clone a graph. Limit: 256 nodes, 2048 edges. Stable IDs are
 * sorted with codepoint ordering, independent of locale and input order.
 * Duplicate IDs/edges and dangling references are errors, not implicit edits.
 */
export function validateGraph(graph:Graph):Graph{
 if(!graph||!Array.isArray(graph.nodes)||!Array.isArray(graph.edges)||graph.nodes.length>256||graph.edges.length>2048)throw new RangeError('Graph limit: 256 nodes / 2048 edges');
 const ids=new Set<string>();const nodes=graph.nodes.map(n=>{if(!n||typeof n.id!=='string'||!/^[\w.:-]{1,80}$/.test(n.id)||ids.has(n.id))throw new RangeError('Invalid or duplicate node ID');ids.add(n.id);
  const label=n.label??n.id;if(typeof label!=='string'||[...label].length>96||/[\x00-\x1f\x7f-\x9f]/.test(label))throw new RangeError('Invalid graph label');
  const width=finite(n.width??Math.max(4,Math.min(20,[...label].length*.55+1.5)),.5,50,'node width'),height=finite(n.height??2,.5,30,'node height');let pin:Vec3|undefined;
  if(n.pin)pin={x:finite(n.pin.x,-10000,10000,'pin.x'),y:finite(n.pin.y,-10000,10000,'pin.y'),z:finite(n.pin.z,-10000,10000,'pin.z')};return {id:n.id,label,width,height,...(pin?{pin}:{})};
 }).sort((a,b)=>order(a.id,b.id));const seen=new Set<string>();const edges=graph.edges.map(e=>{if(!e||!ids.has(e.source)||!ids.has(e.target))throw new RangeError('Dangling graph edge');const key=e.source+'\0'+e.target;if(seen.has(key))throw new RangeError('Duplicate graph edge');seen.add(key);return {source:e.source,target:e.target};}).sort((a,b)=>order(a.source,b.source)||order(a.target,b.target));return {nodes,edges};
}
/** Tarjan SCCs make cycles explicit. Condensation preserves every input edge;
 * it does not duplicate shared children or silently delete backward edges. */
function components(g:Graph):string[][]{
 const adjacency=new Map(g.nodes.map(n=>[n.id,[] as string[]]));for(const e of g.edges)adjacency.get(e.source)!.push(e.target);
 let serial=0;const index=new Map<string,number>(),low=new Map<string,number>(),stack:string[]=[],active=new Set<string>(),out:string[][]=[];
 const visit=(id:string)=>{index.set(id,serial);low.set(id,serial++);stack.push(id);active.add(id);for(const target of adjacency.get(id)!){if(!index.has(target)){visit(target);low.set(id,Math.min(low.get(id)!,low.get(target)!));}else if(active.has(target))low.set(id,Math.min(low.get(id)!,index.get(target)!));}
  if(low.get(id)===index.get(id)){const group:string[]=[];let x:string;do{x=stack.pop()!;active.delete(x);group.push(x);}while(x!==id);out.push(group.sort(order));}};
 for(const n of g.nodes)if(!index.has(n.id))visit(n.id);return out.sort((a,b)=>order(a[0],b[0]));
}
function bounds(nodes:PlacedNode[]):Bounds3{if(!nodes.length)return {min:{x:0,y:0,z:0},max:{x:0,y:0,z:0}};return {min:{x:Math.min(...nodes.map(n=>n.x-n.width/2)),y:Math.min(...nodes.map(n=>n.y-n.height/2)),z:Math.min(...nodes.map(n=>n.z))},max:{x:Math.max(...nodes.map(n=>n.x+n.width/2)),y:Math.max(...nodes.map(n=>n.y+n.height/2)),z:Math.max(...nodes.map(n=>n.z))}};}
/** Cooperative graph layout. Call step(4..16) from the host's work queue, NOT
 * from render(); commit result only when done. Fixed iterations, stable seed,
 * and copied inputs make the result independent of scheduler chunk size/FPS.
 * Force solving is O(iterations * nodes²), deliberately capped at 256 nodes.
 * Pins may overlap; warnings disclose conflicts instead of moving a pin.
 */
export class GraphLayoutJob {
 readonly options:LayoutOptions;readonly graph:Graph;readonly cycles:string[][];readonly nodes:PlacedNode[];done=false;completed=0;
 private velocities:Vec3[]=[];private indices=new Map<string,number>();private total:number;
 constructor(graph:Graph,options:Partial<LayoutOptions>={}){
  this.options=layoutOptions(options);this.graph=validateGraph(graph);const g=this.graph,o=this.options,groups=components(g),which=new Map<string,number>();groups.forEach((a,i)=>a.forEach(id=>which.set(id,i)));
  this.cycles=groups.filter(a=>a.length>1||g.edges.some(e=>e.source===a[0]&&e.target===a[0]));if(o.cyclePolicy==='reject'&&this.cycles.length)throw new RangeError('Graph contains a cycle: '+this.cycles[0].join(', '));
  const ranks=groups.map(()=>0),indeg=groups.map(()=>0),children=groups.map(()=>new Set<number>());for(const e of g.edges){const a=which.get(e.source)!,b=which.get(e.target)!;if(a!==b&&!children[a].has(b)){children[a].add(b);indeg[b]++;}}
  const queue=groups.map((_,i)=>i).filter(i=>indeg[i]===0);while(queue.length){queue.sort((a,b)=>a-b);const a=queue.shift()!;for(const b of [...children[a]].sort((a,b)=>a-b)){ranks[b]=Math.max(ranks[b],ranks[a]+1);if(--indeg[b]===0)queue.push(b);}}
  this.nodes=g.nodes.map(n=>({...n,label:n.label!,width:n.width!,height:n.height!,rank:ranks[which.get(n.id)!],component:which.get(n.id)!,x:0,y:0,z:0}));this.nodes.forEach((n,i)=>this.indices.set(n.id,i));
  const layers:PlacedNode[][]=[];for(const n of this.nodes)(layers[n.rank]??=[]).push(n);
  // Alternating barycentric sweeps order neighboring ranks without changing IDs.
  for(let sweep=0;sweep<8;sweep++){
   const position=new Map<string,number>();layers.forEach(row=>row.forEach((n,i)=>position.set(n.id,i)));const down=sweep%2===0,sequence=layers.map((_,i)=>i);if(!down)sequence.reverse();
   for(const r of sequence){const bary=(n:PlacedNode)=>{const near=g.edges.filter(e=>down?e.target===n.id:e.source===n.id).map(e=>position.get(down?e.source:e.target)!).filter(Number.isFinite);return near.length?near.reduce((a,b)=>a+b,0)/near.length:position.get(n.id)!;};layers[r].sort((a,b)=>bary(a)-bary(b)||order(a.id,b.id));layers[r].forEach((n,i)=>position.set(n.id,i));}
  }
  const rankCenter=(layers.length-1)/2,rankY=layers.map(()=>0),rankHeights=layers.map(row=>Math.max(0,...row.map(n=>n.height)));for(let i=1;i<layers.length;i++)rankY[i]=rankY[i-1]+(rankHeights[i-1]+rankHeights[i])/2+o.rankGap;const yCenter=rankY.length?rankY[rankY.length-1]/2:0;
  layers.forEach((row,r)=>{const totalWidth=row.reduce((s,n)=>s+n.width+o.nodeGap,0)-o.nodeGap;let x=-totalWidth/2;row.forEach((n,i)=>{n.x=x+n.width/2;n.y=yCenter-rankY[r];n.z=o.dimensions===3?(r-rankCenter)*o.depthGap+Math.sin(i*2.399963)*o.depthGap*.35:0;x+=n.width+o.nodeGap;});});
  if(o.algorithm==='radial'){layers.forEach((row,r)=>{const circumference=row.reduce((s,n)=>s+n.width+o.nodeGap,0),radius=Math.max(o.rankGap*(r+1),circumference/(2*Math.PI));row.forEach((n,i)=>{const a=2*Math.PI*i/Math.max(1,row.length)-Math.PI/2;n.x=Math.cos(a)*radius;n.y=Math.sin(a)*radius;n.z=o.dimensions===3?(r-rankCenter)*o.depthGap:0;});});}
  if(o.algorithm==='force'){this.nodes.forEach((n,i)=>{const seed=idHash(n.id)^o.seed,extent=Math.max(8,Math.sqrt(this.nodes.length)*4);n.x=(randomAt(seed,0)-.5)*extent*2;n.y=(randomAt(seed,1)-.5)*extent*2;n.z=o.dimensions===3?(randomAt(seed,2)-.5)*extent*2:0;});}
  this.nodes.forEach(n=>{if(n.pin){n.x=n.pin.x;n.y=n.pin.y;n.z=o.dimensions===3?n.pin.z:0;}});this.velocities=this.nodes.map(()=>({x:0,y:0,z:0}));this.total=o.algorithm==='force'?o.iterations:0;this.done=this.total===0||this.nodes.length===0;
 }
 step(budget=8):boolean{
  finite(budget,1,600,'step budget');if(!Number.isInteger(budget))throw new RangeError('whole iteration budget required');if(this.done)return true;const o=this.options,ns=this.nodes;
  for(let k=0;k<budget&&this.completed<this.total;k++,this.completed++){
   const force=ns.map(n=>({x:-n.x*.018,y:-n.y*.018,z:-n.z*.018}));const cooling=1-.78*this.completed/this.total;
   for(let i=0;i<ns.length;i++)for(let j=i+1;j<ns.length;j++){
    let dx=ns[i].x-ns[j].x,dy=ns[i].y-ns[j].y,dz=o.dimensions===3?ns[i].z-ns[j].z:0;let d=Math.hypot(dx,dy,dz);if(d<1e-6){dx=.1;dy=.07;dz=o.dimensions===3?.09:0;d=Math.hypot(dx,dy,dz);}
    const min=(ns[i].width+ns[j].width)*.55+o.nodeGap,rep=o.repulsion/(d*d+4)+Math.max(0,min-d)*.45;const f=rep/d;for(const axis of ['x','y','z'] as const){const v=(axis==='x'?dx:axis==='y'?dy:dz)*f;force[i][axis]+=v;force[j][axis]-=v;}
   }
   for(const e of this.graph.edges){const i=this.indices.get(e.source)!,j=this.indices.get(e.target)!;if(i===j)continue;const a=ns[i],b=ns[j],d=Math.max(.01,Math.hypot(b.x-a.x,b.y-a.y,b.z-a.z)),rest=(a.width+b.width)*.6+o.nodeGap+3,f=(d-rest)*o.spring/d;for(const axis of ['x','y','z'] as const){const v=(b[axis]-a[axis])*f;force[i][axis]+=v;force[j][axis]-=v;}}
   ns.forEach((n,i)=>{if(n.pin)return;for(const axis of ['x','y','z'] as const){if(axis==='z'&&o.dimensions===2){n.z=0;continue;}const v=this.velocities[i];v[axis]=clamp((v[axis]+force[i][axis]*cooling)*o.damping,-2.5,2.5);n[axis]=clamp(n[axis]+v[axis],-10000,10000);}});
  }
  this.done=this.completed>=this.total;return this.done;
 }
 result():GraphLayout{
  if(!this.done)throw new Error('Graph layout job is not finished');const nodes=this.nodes.map(n=>({...n,...(n.pin?{pin:{...n.pin}}:{})})),warnings:string[]=[];
  if(this.cycles.length)warnings.push(`${this.cycles.length} strongly connected group(s); original cyclic edges retained.`);
  if(nodes.some(n=>n.pin))warnings.push('Pinned coordinates are exact; pin overlap/edge crossings are not forcibly repaired.');
  return {nodes,edges:this.graph.edges.map(e=>({...e})),cycles:this.cycles.map(c=>[...c]),bounds:bounds(nodes),warnings,iterations:this.completed,options:{...this.options}};
 }
}
/** Blocking convenience for small graphs, CLI hosts and tests. Throws on invalid
 * data/limits; does not mutate the graph. Browser hosts should step a job. */
export function layoutGraph(graph:Graph,options:Partial<LayoutOptions>={}):GraphLayout{const j=new GraphLayoutJob(graph,options);while(!j.done)j.step(32);return j.result();}
/** Camera looking toward target, with screen-right x and screen-up y. Orbit
 * moves around target; look rotates without moving the eye; pan moves both.
 * All interaction deltas are explicit, and work with a paused animation clock.
 */
export class CameraRig {
 target:Vec3={x:0,y:0,z:0};yaw=0;pitch=0;roll=0;distance=38;fov=68;
 private radians(v:number){return v*Math.PI/180;}
 basis():{forward:Vec3;right:Vec3;up:Vec3}{const y=this.radians(this.yaw),p=this.radians(this.pitch),r=this.radians(this.roll),f={x:Math.sin(y)*Math.cos(p),y:Math.sin(p),z:Math.cos(y)*Math.cos(p)},a={x:Math.cos(y),y:0,z:-Math.sin(y)},b={x:-Math.sin(y)*Math.sin(p),y:Math.cos(p),z:-Math.cos(y)*Math.sin(p)};return {forward:f,right:{x:a.x*Math.cos(r)+b.x*Math.sin(r),y:a.y*Math.cos(r)+b.y*Math.sin(r),z:a.z*Math.cos(r)+b.z*Math.sin(r)},up:{x:b.x*Math.cos(r)-a.x*Math.sin(r),y:b.y*Math.cos(r)-a.y*Math.sin(r),z:b.z*Math.cos(r)-a.z*Math.sin(r)}};}
 position():Vec3{const f=this.basis().forward;return {x:this.target.x-f.x*this.distance,y:this.target.y-f.y*this.distance,z:this.target.z-f.z*this.distance};}
 orbit(dx:number,dy:number):void{finite(dx,-3600,3600,'orbit yaw');finite(dy,-3600,3600,'orbit pitch');this.yaw=((this.yaw+dx+180)%360+360)%360-180;this.pitch=clamp(this.pitch+dy,-89,89);}
 look(dx:number,dy:number):void{const pos=this.position();this.orbit(dx,dy);const f=this.basis().forward;this.target={x:pos.x+f.x*this.distance,y:pos.y+f.y*this.distance,z:pos.z+f.z*this.distance};}
 pan(right:number,up:number,forward=0):void{for(const v of [right,up,forward])finite(v,-1000,1000,'pan');const b=this.basis();for(const a of ['x','y','z'] as const)this.target[a]=clamp(this.target[a]+b.right[a]*right+b.up[a]*up+b.forward[a]*forward,-10000,10000);}
 dolly(factor:number):void{finite(factor,.001,1000,'dolly factor');this.distance=clamp(this.distance*factor,2,500);}
 reset():void{this.target={x:0,y:0,z:0};this.yaw=this.pitch=this.roll=0;this.distance=38;this.fov=68;}
 fit(b:Bounds3,width=120,height=40):void{this.target={x:(b.min.x+b.max.x)/2,y:(b.min.y+b.max.y)/2,z:(b.min.z+b.max.z)/2};const radius=Math.max(2,Math.hypot(b.max.x-b.min.x,b.max.y-b.min.y,b.max.z-b.min.z)/2),tan=Math.tan(this.radians(this.fov/2)),vertical=tan*height*2/width;this.distance=clamp(radius/Math.sin(Math.atan(Math.min(tan,vertical)))*1.15,4,500);}
 /** Capture a projection transform once per render. Later camera edits do
  * not mutate this snapshot. Reuse it for many points instead of recalculating
  * trigonometry per cell. Width/height are terminal-cell dimensions. */
 projector(width:number,height:number):(p:Vec3)=>{x:number;y:number;z:number;scale:number}|null{finite(width,1,4096,'projection width');finite(height,1,4096,'projection height');const b=this.basis(),eye=this.position(),f=width/(2*Math.tan(this.radians(this.fov/2)));return (p:Vec3)=>{const v={x:p.x-eye.x,y:p.y-eye.y,z:p.z-eye.z},dot=(a:Vec3)=>v.x*a.x+v.y*a.y+v.z*a.z,z=dot(b.forward);if(!Number.isFinite(z)||z<=.2||z>20000)return null;return {x:width/2+dot(b.right)*f/z,y:height/2-dot(b.up)*f/z/2,z,scale:f/z};};}
 project(p:Vec3,width:number,height:number):{x:number;y:number;z:number;scale:number}|null{return this.projector(width,height)(p);}

 snapshot(){return {target:{...this.target},yaw:this.yaw,pitch:this.pitch,roll:this.roll,distance:this.distance,fov:this.fov};}
}
