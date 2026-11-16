/** Nocturne WASM binding. No DOM, Node APIs, framework, or terminal side effects. */
export interface Field {name:string;index:number;default:number;minimum:number;maximum:number;description:string}
export interface Schema {schemaVersion:number;abiVersion:number;fields:Field[];gradientPalette:string[];starPalette:string[]}
export interface SurfaceSettings {values:Record<string,number>;palette:string[];starPalette:string[];glyphs:string[]}
export interface CellFrame {width:number;height:number;cells:Uint32Array}
interface NativeExports extends WebAssembly.Exports {
  memory:WebAssembly.Memory;
  nsInit:()=>void; nsAbiVersion:()=>number;nsConfigSize:()=>number;nsCellSize:()=>number;
  nsConfigPtr:()=>number; nsFramePtr:()=>number; nsTextPtr:()=>number;
  nsRenderFrame:(lo:number,hi:number,length:number)=>number;
}
/** Parse a strict #RRGGBB string; throws RangeError for invalid colors. */
export function parseColor(value:string):number {
  if(!/^#[0-9a-f]{6}$/i.test(value)) throw new RangeError(`Invalid color: ${value}`);
  return Number.parseInt(value.slice(1),16);
}
/** A shared, stateless renderer. Sequential calls may use unrelated configurations.
 * Each returned frame is an owned copy. An instance must not be reentered while
 * rendering. Independent instances can run in independent workers.
 */
export class NocturneEngine {
  private constructor(private native:NativeExports,public readonly schema:Schema){}
  /** Instantiate supplied bytes; no fetch, external assets, or host imports.
   * Throws WebAssembly errors for invalid bytes, Error for ABI mismatch.
   * Example: const engine=await NocturneEngine.create(bytes,schema);
   */
  static async create(bytes:Uint8Array,schema:Schema):Promise<NocturneEngine>{
    const result=await WebAssembly.instantiate(bytes as BufferSource,{});
    const native=result.instance.exports as NativeExports;
    if(schema.schemaVersion!==1||native.nsAbiVersion()!==1||native.nsConfigSize()!==448||native.nsCellSize()!==16) throw new Error('Nocturne ABI mismatch');
    native.nsInit();
    return new NocturneEngine(native,schema);
  }
  /** Produce independent defaults and validate any named integer overrides. */
  defaults(changes:Record<string,number>={}):SurfaceSettings{
    const values:Record<string,number>={};
    for(const field of this.schema.fields)values[field.name]=field.default;
    const config={values:{...values,...changes},palette:[...this.schema.gradientPalette],starPalette:[...this.schema.starPalette],glyphs:[]};
    this.validate(config);return config;
  }
  /** Validate named keys, finite integer ranges, palettes, and custom glyphs.
   * Throws RangeError or TypeError; does not mutate config.
   */
  validate(config:SurfaceSettings):void{
    const fields=new Map(this.schema.fields.map(field=>[field.name,field]));
    for(const name of Object.keys(config.values)) if(!fields.has(name))throw new RangeError(`Unknown setting: ${name}`);
    for(const field of this.schema.fields){
      const value=config.values[field.name];
      if(!Number.isInteger(value)||value<field.minimum||value>field.maximum)throw new RangeError(`${field.name}: expected ${field.minimum}..${field.maximum}`);
    }
    for(const colors of [config.palette,config.starPalette]){
      if(!Array.isArray(colors)||colors.length<1||colors.length>8)throw new RangeError('Palette needs 1..8 colors');
      colors.forEach(parseColor);
    }
    if(!Array.isArray(config.glyphs)||config.glyphs.length>32||config.glyphs.some(glyph=>typeof glyph!=='string'||[...glyph].length!==1))throw new RangeError('Custom glyphs must be up to 32 single code points');
  }
  /** Render at an explicit time. Data may change at the same motion timestamp.
   * Returns row-major [glyph, foreground, background, flags] uint32 words.
   * Inputs: validated config, safe nonnegative integer milliseconds, <=512 code
   * points of demo text. Throws RangeError for input/renderer errors.
   */
  render(config:SurfaceSettings,motionMs:number,text='Make something that feels alive.'):CellFrame{
    this.validate(config);
    if(!Number.isSafeInteger(motionMs)||motionMs<0)throw new RangeError('Time must be a nonnegative safe integer');
    const points=[...text];
    if(points.length>512)throw new RangeError('Text is limited to 512 code points');
    const words=new Int32Array(this.native.memory.buffer,this.native.nsConfigPtr(),112);
    words.fill(0);
    for(const field of this.schema.fields)words[field.index]=config.values[field.name];
    config.palette.forEach((color,i)=>words[64+i]=parseColor(color));
    config.starPalette.forEach((color,i)=>words[72+i]=parseColor(color));
    config.glyphs.forEach((glyph,i)=>words[80+i]=glyph.codePointAt(0)!);
    words[this.schema.fields.find(f=>f.name==='paletteCount')!.index]=config.palette.length;
    words[this.schema.fields.find(f=>f.name==='starPaletteCount')!.index]=config.starPalette.length;
    words[this.schema.fields.find(f=>f.name==='glyphCount')!.index]=config.glyphs.length;
    const textWords=new Uint32Array(this.native.memory.buffer,this.native.nsTextPtr(),512);
    points.forEach((glyph,i)=>textWords[i]=glyph.codePointAt(0)!);
    const count=this.native.nsRenderFrame(motionMs>>>0,Math.floor(motionMs/4294967296),points.length);
    if(count<0)throw new RangeError(`Native renderer error ${count}`);
    return {width:config.values.width,height:config.values.height,cells:new Uint32Array(this.native.memory.buffer,this.native.nsFramePtr(),count*4).slice()};
  }
}
/** Encode a complete owned frame as ANSI without taking over a terminal.
 * Synchronized output is opt-in and must be negotiated by the host.
 * Suitable for a standalone view; framework adapters should consume cells.
 */
export function toAnsi(frame:CellFrame,synchronized=false):string{
  const parts:string[]=[synchronized?'\x1b[?2026h':''];
  let previousFg=-1,previousBg=-1;
  for(let y=0;y<frame.height;y++){
    parts.push(`\x1b[${y+1};1H`);
    for(let x=0;x<frame.width;x++){
      const i=(y*frame.width+x)*4,glyph=frame.cells[i],fg=frame.cells[i+1],bg=frame.cells[i+2];
      if(fg!==previousFg){parts.push(`\x1b[38;2;${fg>>>16};${(fg>>>8)&255};${fg&255}m`);previousFg=fg;}
      if(bg!==previousBg){parts.push(`\x1b[48;2;${bg>>>16};${(bg>>>8)&255};${bg&255}m`);previousBg=bg;}
      parts.push(String.fromCodePoint(glyph));
    }
  }
  parts.push('\x1b[0m',synchronized?'\x1b[?2026l':'');return parts.join('');
}
