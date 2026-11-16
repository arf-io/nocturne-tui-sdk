/** Nocturne Studio. One native/WASM material and widget kernel; no host side effects. */
export interface StudioField {name:string;index:number;default:number;minimum:number;maximum:number;description:string}
export interface StudioSchema {abiVersion:number;fields:StudioField[]}
export interface StudioConfig {values:Record<string,number>;palette:string[];starPalette:string[];glyphs:string[];novaGlyphs:string[]}
export interface StudioFrame {width:number;height:number;cells:Uint32Array}
export interface StudioNode {kind:string;x:number;y:number;width:number;height:number;text?:string;data?:number[];changedMs?:number;[key:string]:string|number|number[]|undefined}
export interface StudioImpulse {x:number;y:number;atMs:number;strength?:number;kind?:number;id?:number}
export const STUDIO_KINDS=['text','box','rule','button','item','cursor','progress','bars','pie','donut','scatter','line','digits','edge'];
const NODE_KEYS=['kind','id','x','y','width','height','state','value','fromValue','changedLo','changedHi','durationMs','fg','bg','fgOpacity','bgOpacity','style','textOffset','textLength','dataOffset','dataLength','hueStep','hueSpeed','hueBase','revealMs','reserved','hueSaturation','hueBrightness','colorAnimation','glyph','zoom','reserved2'];
interface StudioNative extends WebAssembly.Exports {
 nsOklchColor:(l:number,c:number,h:number)=>number;nsOklchLightness:(rgb:number)=>number;
 nsStagePaintFrame:(lo:number,hi:number,nc:number,tc:number,dc:number)=>number;
 nsFleetInkOpacity:(age:number,fade:number,row:number,band:number,minimum:number)=>number;
 memory:WebAssembly.Memory;nsStageInit:()=>void;nsStageVersion:()=>number;nsStageConfigSize:()=>number;
 nsStageConfigPtr:()=>number;nsStageNodesPtr:()=>number;nsStageEventsPtr:()=>number;nsStageTextPtr:()=>number;nsStageDataPtr:()=>number;nsFramePtr:()=>number;nsStageLayerPtr:()=>number;
 nsStageRenderFrame:(lo:number,hi:number,ec:number,nc:number,tc:number,dc:number)=>number;
 nsStageHitFrame:(nc:number,dc:number,x:number,y:number)=>number;
 nsStageComposite:(dest:number,dw:number,dh:number,src:number,sw:number,sh:number,x:number,y:number,fa:number,ba:number)=>number;
 nsStageTweenWords:(from:number,to:number,lo:number,hi:number,duration:number,ease:number)=>number;
}
function int(value:unknown,min:number,max:number,label:string):number {if(typeof value!=='number'||!Number.isSafeInteger(value)||value<min||value>max)throw new RangeError(`${label}: integer ${min}..${max}`);return value;}
function rgb(value:unknown):number {if(typeof value==='number')return int(value,0,0xffffff,'color');if(typeof value==='string'&&/^#[\da-f]{6}$/i.test(value))return parseInt(value.slice(1),16);throw new RangeError('Expected #RRGGBB');}
/** Stateful configuration is owned by the caller. Calls are synchronous, non-reentrant.
 * Returned frames own storage. Use separate engines in separate workers.
 */
export class StudioEngine {
 private constructor(private native:StudioNative,public readonly schema:StudioSchema){}
 /** Instantiate caller-supplied WASM. No fetch, imports, terminal, or event loop. */
 static async create(bytes:Uint8Array,schema:StudioSchema):Promise<StudioEngine>{const r=await WebAssembly.instantiate(bytes as BufferSource,{});const n=r.instance.exports as StudioNative;if(n.nsStageVersion()!==2||n.nsStageConfigSize()!==704||schema.abiVersion!==2)throw new Error('Studio ABI mismatch');n.nsStageInit();return new StudioEngine(n,schema);}
 /** Create independent defaults. Unknown or out-of-range values are rejected at render. */
 defaults(overrides:Record<string,number>={}):StudioConfig{return {values:{...Object.fromEntries(this.schema.fields.map(f=>[f.name,f.default])),...overrides},palette:['#28304f','#785c89','#367876','#ae7357','#504565'],starPalette:['#b6a4c4','#9fb9b0','#c7bca7','#9cacca','#c6a0aa','#adbdbb'],glyphs:[...'.·∙⋅⠁⠂⠄⡀⠈⠐⠠⢀'],novaGlyphs:[...'·∙*✦✧']};}
 /** Validate before copying config into bounded native scratch. */
 private packConfig(config:StudioConfig):void {
  const fields=new Map(this.schema.fields.map(f=>[f.name,f]));for(const name of Object.keys(config.values))if(!fields.has(name))throw new RangeError(`Unknown field ${name}`);
  const words=new Int32Array(176);for(const f of this.schema.fields)words[f.index]=int(config.values[f.name],f.minimum,f.maximum,f.name);
  for(const [key,offset,limit,count] of [['palette',64,32,'paletteCount'],['starPalette',96,32,'starColorCount'],['glyphs',128,32,'starGlyphCount'],['novaGlyphs',160,16,'novaGlyphCount']] as const){
   const values=config[key];if(!Array.isArray(values)||values.length<1||values.length>limit)throw new RangeError(`${key}: 1..${limit} entries`);
   values.forEach((v,i)=>{if(key==='palette'||key==='starPalette')words[offset+i]=rgb(v);else {if(typeof v!=='string'||[...v].length!==1)throw new RangeError('single scalar glyph required');const g=v.codePointAt(0)!;if(g>=0xd800&&g<=0xdfff)throw new RangeError('surrogate glyph');words[offset+i]=g;}});words[fields.get(count)!.index]=values.length;
  }
  new Int32Array(this.native.memory.buffer,this.native.nsStageConfigPtr(),176).set(words);
 }
 private packNodes(nodes:StudioNode[]):[number,number]{
  if(nodes.length>512)throw new RangeError('512 node limit');const records=new Int32Array(nodes.length*32),text:number[]=[],data:number[]=[];
  nodes.forEach((n,index)=>{const kind=STUDIO_KINDS.indexOf(n.kind);if(kind<0)throw new RangeError(`Unknown node ${n.kind}`);
   const values:Record<string,unknown>={id:0,fg:0xe2d9c9,bg:0x11100e,fgOpacity:1000,bgOpacity:0,hueStep:17,hueSpeed:24,hueSaturation:620,hueBrightness:830,zoom:1,...n};
   for(const [key,value] of Object.entries(values)){if(['kind','text','data','changedMs'].includes(key))continue;const k=NODE_KEYS.indexOf(key);if(k<0||['textOffset','textLength','dataOffset','dataLength'].includes(key))throw new RangeError(`Unknown/reserved node key ${key}`);records[index*32+k]=key==='fg'||key==='bg'?rgb(value):int(value,-2147483648,2147483647,key);}
   const at=int(n.changedMs??0,0,Number.MAX_SAFE_INTEGER,'changedMs');records[index*32]=kind;records[index*32+9]=at>>>0;records[index*32+10]=Math.floor(at/4294967296);
   const chars=[...(n.text??'')];records[index*32+17]=text.length;records[index*32+18]=chars.length;chars.forEach(c=>text.push(c.codePointAt(0)!));
   records[index*32+19]=data.length;records[index*32+20]=(n.data??[]).length;(n.data??[]).forEach(v=>data.push(int(v,-1000000,1000000,'data')));
  });
  if(text.length>32768||data.length>16384)throw new RangeError('scene text/data capacity');
  new Int32Array(this.native.memory.buffer,this.native.nsStageNodesPtr(),records.length).set(records);new Uint32Array(this.native.memory.buffer,this.native.nsStageTextPtr(),text.length).set(text);new Int32Array(this.native.memory.buffer,this.native.nsStageDataPtr(),data.length).set(data);return [text.length,data.length];
 }
 /** Pure rendering. timeMs is explicit, safe integer milliseconds. Calling again
  * at the same time with new nodes implements an immediate data-only commit.
  * Throws RangeError for bounds/invalid config; output never aliases scratch.
  */
 render(config:StudioConfig,timeMs:number,nodes:StudioNode[]=[],events:StudioImpulse[]=[]):StudioFrame{
  int(timeMs,0,Number.MAX_SAFE_INTEGER,'timeMs');if(events.length>128)throw new RangeError('128 impulse limit');this.packConfig(config);const [tc,dc]=this.packNodes(nodes);
  const ev=new Int32Array(events.length*8);events.forEach((e,i)=>{int(e.atMs,0,Number.MAX_SAFE_INTEGER,'atMs');ev.set([int(Math.round(e.x*256),-1048576,1048576,'x'),int(Math.round(e.y*256),-1048576,1048576,'y'),int(e.strength??1000,0,1000,'strength'),int(e.kind??0,0,1,'kind'),e.atMs>>>0,Math.floor(e.atMs/4294967296),int(e.id??0,0,2147483647,'id'),0],i*8);});
  new Int32Array(this.native.memory.buffer,this.native.nsStageEventsPtr(),ev.length).set(ev);
  const count=this.native.nsStageRenderFrame(timeMs>>>0,Math.floor(timeMs/4294967296),events.length,nodes.length,tc,dc);if(count<0)throw new RangeError(`Native scene validation ${count}`);
  return {width:config.values.width,height:config.values.height,cells:new Uint32Array(this.native.memory.buffer,this.native.nsFramePtr(),count*4).slice()};
 }
 /** Gamut-mapped OKLCh, integer L/1000, C/10000, millidegrees. Throws RangeError.
  * Example: engine.oklch(700,1400,270000). No allocation or clock access. */
 oklch(l:number,c:number,h:number):number {return this.native.nsOklchColor(int(l,0,1000,'L'),int(c,0,4000,'C'),int(h,-2147483648,2147483647,'h'));}
 /** Approximate Oklab lightness of packed sRGB in thousandths. */
 lightness(color:number):number{return this.native.nsOklchLightness(int(color,0,0xffffff,'RGB'));}
 /** Paint nodes over an existing surface. Retains background sampling until ink
  * occupies a cell. Caller retains original storage; result is a copied frame. */
 paint(frame:StudioFrame,timeMs:number,nodes:StudioNode[],config?:StudioConfig):StudioFrame {
  int(frame.width,0,512,'width');int(frame.height,0,256,'height');int(timeMs,0,Number.MAX_SAFE_INTEGER,'timeMs');
  if(frame.cells.length!==frame.width*frame.height*4)throw new RangeError('frame storage mismatch');
  const cfg=config?{...config,values:{...config.values,width:frame.width,height:frame.height}}:this.defaults({width:frame.width,height:frame.height});
  this.packConfig(cfg);const [tc,dc]=this.packNodes(nodes);
  new Uint32Array(this.native.memory.buffer,this.native.nsFramePtr(),frame.cells.length).set(frame.cells);
  const n=this.native.nsStagePaintFrame(timeMs>>>0,Math.floor(timeMs/4294967296),nodes.length,tc,dc);if(n<0)throw new RangeError('Invalid overlay '+n);
  return {...frame,cells:new Uint32Array(this.native.memory.buffer,this.native.nsFramePtr(),n*4).slice()};
 }
 /** Reverse-z hit testing; disabled regions block. Returns semantic ID and subitem. */
 hit(nodes:StudioNode[],x:number,y:number):{id:number;item:number}|null {const [,dc]=this.packNodes(nodes);const r=this.native.nsStageHitFrame(nodes.length,dc,int(x,-4096,4096,'x'),int(y,-4096,4096,'y'));if(r<0)throw new RangeError('Invalid hit test');return r?{id:Number(nodes[(r>>>16)-1].id??0),item:(r&65535)-1}:null;}
 /** Composite an independent source frame into dest and return an owned result. */
 composite(dest:StudioFrame,src:StudioFrame,x=0,y=0,fgOpacity=1000,bgOpacity=1000):StudioFrame{
  for(const f of [dest,src]){int(f.width,0,512,'width');int(f.height,0,256,'height');if(f.cells.length!==f.width*f.height*4)throw new RangeError('frame storage mismatch');}
  new Uint32Array(this.native.memory.buffer,this.native.nsFramePtr(),dest.cells.length).set(dest.cells);new Uint32Array(this.native.memory.buffer,this.native.nsStageLayerPtr(),src.cells.length).set(src.cells);
  const r=this.native.nsStageComposite(this.native.nsFramePtr(),dest.width,dest.height,this.native.nsStageLayerPtr(),src.width,src.height,int(x,-4096,4096,'x'),int(y,-4096,4096,'y'),int(fgOpacity,0,1000,'fgOpacity'),int(bgOpacity,0,1000,'bgOpacity'));if(r)throw new RangeError('Composite error');return {...dest,cells:new Uint32Array(this.native.memory.buffer,this.native.nsFramePtr(),dest.cells.length).slice()};
 }
 /** Scalar keyframe interpolation, clamped at the target; same arithmetic as C. */
 tween(from:number,to:number,elapsedMs:number,durationMs:number,easing=1):number {int(elapsedMs,0,Number.MAX_SAFE_INTEGER,'elapsed');return this.native.nsStageTweenWords(int(from,-2147483648,2147483647,'from'),int(to,-2147483648,2147483647,'to'),elapsedMs>>>0,Math.floor(elapsedMs/4294967296),int(durationMs,0,4294967295,'duration'),int(easing,0,3,'easing'));}
 /** Opacity for arriving transcript ink with a spatial top-edge fade.
  * Inputs: arrival age/duration in ms, row and top band in Q8 cells, minimum
  * in thousandths. fadeMs=0 disables arrival animation. Returns 0..1000.
  * Throws RangeError for invalid values; no mutation. Example:
  * engine.inkOpacity(420,420,3*256,6*256,760) === 880.
  */
 inkOpacity(ageMs:number,fadeMs:number,rowQ8:number,bandQ8:number,topMinimum:number):number {
  return this.native.nsFleetInkOpacity(int(ageMs,0,4294967295,'ageMs'),int(fadeMs,0,4294967295,'fadeMs'),int(rowQ8,-2147483648,2147483647,'rowQ8'),int(bandQ8,0,2147483647,'bandQ8'),int(topMinimum,0,1000,'topMinimum'));
 }

}
