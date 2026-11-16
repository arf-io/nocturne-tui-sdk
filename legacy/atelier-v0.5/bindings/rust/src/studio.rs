//! Additive Studio v2 façade over the same integer C renderer.
//! No terminal ownership, hidden clock, retained FFI pointers, or dependencies.
use crate::{Cell,Error,Frame};
mod fields { include!("studio_keys.rs"); }
pub use fields::StageKey;

#[repr(C)]
#[derive(Clone)]
struct StageConfig { values:[i32;64], palette:[u32;32], starPalette:[u32;32], glyphs:[u32;32], novaGlyphs:[u32;16] }
#[repr(C)]
#[derive(Clone,Copy)]
struct RawNode { values:[i32;32] }
#[repr(C)]
#[derive(Clone,Copy)]
struct RawImpulse { values:[i32;8] }
extern "C" {
 fn nsFleetInkOpacity(ageMs:u32,fadeMs:u32,rowQ8:i32,bandQ8:i32,topMinimum:i32)->i32;
 fn nsStageVersion()->u32;
 fn nsStageConfigSize()->u32;
 fn nsStageDefaults(config:*mut StageConfig);
 fn nsStageRender(config:*const StageConfig,timeMs:u64,events:*const RawImpulse,eventCount:u32,nodes:*const RawNode,nodeCount:u32,text:*const u32,textCount:u32,data:*const i32,dataCount:u32,cells:*mut Cell,capacity:u32)->i32;
 fn nsStageHit(nodes:*const RawNode,nodeCount:u32,data:*const i32,dataCount:u32,x:i32,y:i32)->i32;
 fn nsStageComposite(dest:*mut Cell,dw:i32,dh:i32,source:*const Cell,sw:i32,sh:i32,x:i32,y:i32,fa:i32,ba:i32)->i32;
 fn nsStageTween(from:i32,to:i32,elapsed:u64,duration:u32,easing:i32)->i32;
}
/// Primitive discriminator, stable in Studio ABI v2.
#[repr(i32)]
#[derive(Clone,Copy,Debug)]
pub enum NodeKind { Text,Box,Rule,Button,Item,Cursor,Progress,Bars,Pie,Donut,Scatter,Line,Digits,Edge }
/// Node property indices. Geometry, style and bounds are checked by the C kernel.
#[repr(usize)]
#[derive(Clone,Copy,Debug)]
pub enum NodeKey { Id=1,State=6,Value=7,FromValue=8,DurationMs=11,Fg=12,Bg=13,FgOpacity=14,BgOpacity=15,Style=16,HueStep=21,HueSpeed=22,HueBase=23,RevealMs=24,HueSaturation=26,HueBrightness=27,ColorAnimation=28,Glyph=29,Zoom=30 }
/// A semantic node with owned content. No unsafe construction or raw pointers.
#[derive(Clone,Debug)]
pub struct Node { words:[i32;32], pub text:String, pub data:Vec<i32> }
impl Node {
 /// Construct a clipped primitive. Inputs: integer cell rectangle and kind.
 /// Returns an error outside x/y ±4096, width 0..512, height 0..256.
 /// Example: `let n = Node::new(NodeKind::Progress,2,4,30,1)?;`
 pub fn new(kind:NodeKind,x:i32,y:i32,width:i32,height:i32)->Result<Self,Error>{
  if !(-4096..=4096).contains(&x)||!(-4096..=4096).contains(&y)||!(0..=512).contains(&width)||!(0..=256).contains(&height){return Err(Error("Node rectangle outside bounds".into()));}
  let mut w=[0;32];w[0]=kind as i32;w[2]=x;w[3]=y;w[4]=width;w[5]=height;w[12]=0xe2d9c9;w[13]=0x11100e;w[14]=1000;w[21]=17;w[22]=24;w[26]=620;w[27]=830;w[30]=1;
  Ok(Self{words:w,text:String::new(),data:Vec::new()})
 }
 /// Set one style/value property. Full validation occurs before render/hit.
 /// Example: `n.set(NodeKey::Value,670); n.set(NodeKey::Id,42);`
 pub fn set(&mut self,key:NodeKey,value:i32){self.words[key as usize]=value;}
 /// Set an explicit transition/reveal start. No clock is read.
 pub fn changedAt(&mut self,timeMs:u64){self.words[9]=timeMs as u32 as i32;self.words[10]=(timeMs>>32) as u32 as i32;}
 /// Return the semantic ID, zero meaning a non-interactive decoration.
 pub fn id(&self)->i32{self.words[1]}
}
/// A replayable impulse. xQ8/yQ8 = cell coordinates ×256; kind 0 ripple,1 nova.
#[derive(Clone,Copy,Debug)]
pub struct Impulse { pub xQ8:i32,pub yQ8:i32,pub strength:i32,pub kind:i32,pub atMs:u64,pub id:i32 }
impl Impulse {
 /// Make a full-strength ripple at a whole-cell origin. Returns an error for
 /// coordinates outside ±4096. Example: `Impulse::ripple(12,8,1000)?`.
 pub fn ripple(x:i32,y:i32,atMs:u64)->Result<Self,Error>{if !(-4096..=4096).contains(&x)||!(-4096..=4096).contains(&y){return Err(Error("Impulse coordinates out of bounds".into()));}Ok(Self{xQ8:x*256,yQ8:y*256,strength:1000,kind:0,atMs,id:0})}
}
/// A successful hit contains the caller's stable ID and zero-based data item.
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Hit { pub id:i32,pub item:usize }
/// Deterministic configuration. Immutable rendering is Send/Sync through ordinary
/// Rust ownership; no static native state is used by this native API.
#[derive(Clone)]
pub struct Studio { config:StageConfig }
fn packNodes(nodes:&[Node])->Result<(Vec<RawNode>,Vec<u32>,Vec<i32>),Error>{
 if nodes.len()>512{return Err(Error("512 node limit".into()));}
 let mut raw=Vec::with_capacity(nodes.len());let mut text=Vec::new();let mut data=Vec::new();
 for n in nodes {
  let points:Vec<u32>=n.text.chars().map(|c|c as u32).collect();
  if points.len()>32768-text.len()||n.data.len()>16384-data.len(){return Err(Error("Scene text/data capacity".into()));}
  if n.data.iter().any(|v|!(-1000000..=1000000).contains(v)){return Err(Error("Scene numeric data out of bounds".into()));}
  let mut w=n.words;w[17]=text.len() as i32;w[18]=points.len() as i32;w[19]=data.len() as i32;w[20]=n.data.len() as i32;
  text.extend(points);data.extend_from_slice(&n.data);raw.push(RawNode{values:w});
 }
 Ok((raw,text,data))
}
impl Studio {
 /// Initialize and verify ABI/struct sizes. Returns Error for incompatible linkage.
 /// Example: `let mut studio=Studio::new()?;`
 pub fn new()->Result<Self,Error>{
  let mut c=StageConfig{values:[0;64],palette:[0;32],starPalette:[0;32],glyphs:[0;32],novaGlyphs:[0;16]};
  // SAFETY: c is an initialized, aligned repr(C) struct. C retains no pointers.
  unsafe{if nsStageVersion()!=2||nsStageConfigSize() as usize!=std::mem::size_of::<StageConfig>()||std::mem::size_of::<Cell>()!=16||std::mem::size_of::<RawNode>()!=128||std::mem::size_of::<RawImpulse>()!=32{return Err(Error("Studio ABI mismatch".into()));}nsStageDefaults(&mut c);}
  Ok(Self{config:c})
 }
 /// Atomically set a typed integer key, validated against generated schema ranges.
 /// Example: `studio.set(StageKey::FocusMode,3)?;` Errors do not mutate config.
 pub fn set(&mut self,key:StageKey,value:i32)->Result<(),Error>{let index=key as usize;let(min,max)=fields::STAGE_RANGES[index];if value<min||value>max{return Err(Error(format!("{key:?}: {min}..{max}")));}self.config.values[index]=value;Ok(())}
 /// Set 1..32 packed RGB stops. star=true selects peak star colors.
 /// Example: `studio.setColors(&[0x614971,0x428a81],false)?;`
 pub fn setColors(&mut self,colors:&[u32],star:bool)->Result<(),Error>{if colors.is_empty()||colors.len()>32||colors.iter().any(|v|*v>0xffffff){return Err(Error("1..32 RGB colors required".into()));}if star{self.config.starPalette[..colors.len()].copy_from_slice(colors);self.set(StageKey::StarColorCount,colors.len() as i32)}else{self.config.palette[..colors.len()].copy_from_slice(colors);self.set(StageKey::PaletteCount,colors.len() as i32)}}
 /// Set ordinary or nova glyphs. char excludes invalid Unicode scalars by type.
 /// Returns Error for empty/excess length. Example: `studio.setGlyphs(&['·','⠁'],false)?;`
 pub fn setGlyphs(&mut self,glyphs:&[char],nova:bool)->Result<(),Error>{let limit=if nova{16}else{32};if glyphs.is_empty()||glyphs.len()>limit{return Err(Error(format!("1..{limit} glyphs required")));}for(i,g)in glyphs.iter().enumerate(){if nova{self.config.novaGlyphs[i]=*g as u32;}else{self.config.glyphs[i]=*g as u32;}}self.set(if nova{StageKey::NovaGlyphCount}else{StageKey::StarGlyphCount},glyphs.len() as i32)}
 /// Pure render at explicit milliseconds. The result owns all cells. Errors are
 /// validated before native drawing; never exposes a partial frame.
 /// Example: `let frame=studio.render(1500,&[node],&[event])?;`
 pub fn render(&self,timeMs:u64,nodes:&[Node],events:&[Impulse])->Result<Frame,Error>{
  if events.len()>128{return Err(Error("128 impulse limit".into()));}
  let(ns,text,data)=packNodes(nodes)?;
  let ev:Vec<RawImpulse>=events.iter().map(|e|RawImpulse{values:[e.xQ8,e.yQ8,e.strength,e.kind,e.atMs as u32 as i32,(e.atMs>>32) as u32 as i32,e.id,0]}).collect();
  let width=self.config.values[0] as usize;let height=self.config.values[1] as usize;let mut cells=vec![Cell::default();width*height];
  // SAFETY: every pointer refers to an aligned live owned vector; lengths are
  // bounded before narrowing. Empty vectors are never dereferenced by C. The
  // private config maintains bounded dimensions. No native pointer is retained.
  let r=unsafe{nsStageRender(&self.config,timeMs,ev.as_ptr(),ev.len() as u32,ns.as_ptr(),ns.len() as u32,text.as_ptr(),text.len() as u32,data.as_ptr(),data.len() as u32,cells.as_mut_ptr(),cells.len() as u32)};
  if r<0{return Err(Error(format!("Studio renderer error {r}")));}Ok(Frame{width,height,cells})
 }
 /// Reverse-z geometric picking. Disabled nodes block hits; None means no target.
 /// Example: `let picked=studio.hit(&nodes,12,4)?;`
 pub fn hit(&self,nodes:&[Node],x:i32,y:i32)->Result<Option<Hit>,Error>{let(ns,_,data)=packNodes(nodes)?;
  // SAFETY: initialized, aligned arrays with exact lengths; read-only synchronous call.
  let r=unsafe{nsStageHit(ns.as_ptr(),ns.len() as u32,data.as_ptr(),data.len() as u32,x,y)};
  if r<0{return Err(Error("Invalid hit-test input".into()));}if r==0{return Ok(None);}let index=((r as u32>>16)-1) as usize;let n=nodes.get(index).ok_or_else(||Error("Invalid native hit index".into()))?;Ok(Some(Hit{id:n.id(),item:((r as u32&65535)-1) as usize}))
 }
 /// Return an owned source-over composition. Validate public Frame storage before
 /// FFI. Opacities are 0..1000; negative offsets clip. Inputs remain unchanged.
 pub fn composite(&self,dest:&Frame,source:&Frame,x:i32,y:i32,fgOpacity:i32,bgOpacity:i32)->Result<Frame,Error>{
  for f in [dest,source]{if f.width>512||f.height>256||f.cells.len()!=f.width*f.height{return Err(Error("Invalid frame storage".into()));}}
  let mut result=dest.clone();
  // SAFETY: validated dimensions exactly match the distinct owned input/output
  // buffers; no aliasing, no retained pointers, bounded native writes.
  let r=unsafe{nsStageComposite(result.cells.as_mut_ptr(),result.width as i32,result.height as i32,source.cells.as_ptr(),source.width as i32,source.height as i32,x,y,fgOpacity,bgOpacity)};
  if r<0{return Err(Error("Invalid composition parameters".into()));}Ok(result)
 }
}
/// Explicit scalar interpolation, 0 linear/1 smoothstep/2 sine/3 cubic-out.
/// Zero duration immediately returns target. Invalid easing returns Error.
pub fn tween(from:i32,to:i32,elapsed:u64,duration:u32,easing:i32)->Result<i32,Error>{if !(0..=3).contains(&easing){return Err(Error("Easing must be 0..3".into()));}
 // SAFETY: pure integer scalar operation, no pointers or retained state.
 Ok(unsafe{nsStageTween(from,to,elapsed,duration,easing)})}

#[cfg(test)]
mod tests {
 use super::*;
 #[test]fn replayAndOwnership(){let mut s=Studio::new().unwrap();s.set(StageKey::Width,40).unwrap();let a=s.render(1234,&[],&[]).unwrap();let before=a.toBytes();let _=s.render(8000,&[],&[]).unwrap();assert_eq!(before,a.toBytes());assert_eq!(a,s.render(1234,&[],&[]).unwrap());}
 #[test]fn everyWidget(){let s=Studio::new().unwrap();for kind in [NodeKind::Text,NodeKind::Box,NodeKind::Rule,NodeKind::Button,NodeKind::Item,NodeKind::Cursor,NodeKind::Progress,NodeKind::Bars,NodeKind::Pie,NodeKind::Donut,NodeKind::Scatter,NodeKind::Line,NodeKind::Digits,NodeKind::Edge]{let mut n=Node::new(kind,2,2,30,10).unwrap();n.text="67".into();n.data=vec![200,400,700,900];n.set(NodeKey::Value,670);assert!(s.render(4000,&[n],&[]).is_ok());}}
 #[test]fn disabledAndHit(){let s=Studio::new().unwrap();let mut n=Node::new(NodeKind::Button,1,1,10,3).unwrap();n.set(NodeKey::Id,7);assert_eq!(s.hit(&[n.clone()],2,2).unwrap().unwrap().id,7);n.set(NodeKey::State,3);assert!(s.hit(&[n],2,2).unwrap().is_none());}
 #[test]fn validationAndEmpty(){let mut s=Studio::new().unwrap();assert!(s.set(StageKey::Width,-1).is_err());assert!(s.setColors(&[0x1000000],false).is_err());s.set(StageKey::Width,0).unwrap();assert!(s.render(0,&[],&[]).unwrap().cells.is_empty());}
 #[test]fn compositionAndTween(){let s=Studio::new().unwrap();let a=s.render(1000,&[],&[]).unwrap();let b=s.render(2000,&[],&[]).unwrap();assert_eq!(a,s.composite(&a,&b,0,0,0,0).unwrap());assert!(s.composite(&Frame{width:1,height:1,cells:vec![]},&b,0,0,0,0).is_err());for e in 0..4{assert_eq!(tween(0,670,1000,1000,e).unwrap(),670);}}
 #[test]fn impulseAndImmediateData(){let s=Studio::new().unwrap();let mut n=Node::new(NodeKind::Text,1,1,30,1).unwrap();n.text="first".into();let a=s.render(5000,&[n.clone()],&[]).unwrap();n.text="second".into();assert_ne!(a,s.render(5000,&[n],&[]).unwrap());let e=Impulse::ripple(20,10,4000).unwrap();assert_ne!(s.render(5000,&[],&[]).unwrap(),s.render(5000,&[],&[e]).unwrap());}
}

/// Pure arriving-text and spatial-horizon visual utility. No retained pointers.
/// Input units are milliseconds, Q8 cells, and thousandths. A zero fade/band
/// disables that effect. Invalid band/minimum returns Error.
/// Example: `assert_eq!(fleetInkOpacity(420,420,768,1536,760)?,880);`
#[allow(non_snake_case)]
pub fn fleetInkOpacity(ageMs:u32,fadeMs:u32,rowQ8:i32,bandQ8:i32,topMinimum:i32)->Result<i32,Error>{
 if bandQ8<0 || !(0..=1000).contains(&topMinimum){return Err(Error("Invalid Fleet opacity bounds".into()));}
 // SAFETY: scalar-only ABI, validated ranges, no pointers or shared mutable state.
 Ok(unsafe{nsFleetInkOpacity(ageMs,fadeMs,rowQ8,bandQ8,topMinimum)})
}
#[cfg(test)]
mod fleet_tests {
 use super::*;
 #[test] fn arrival_and_horizon(){assert_eq!(fleetInkOpacity(0,420,1536,1536,760).unwrap(),0);assert_eq!(fleetInkOpacity(420,420,768,1536,760).unwrap(),880);assert_eq!(fleetInkOpacity(u32::MAX,420,1536,1536,760).unwrap(),1000);}
 #[test] fn invalid_and_immediate(){assert!(fleetInkOpacity(0,0,0,-1,760).is_err());assert!(fleetInkOpacity(0,0,0,0,1001).is_err());assert_eq!(fleetInkOpacity(0,0,0,0,760).unwrap(),1000);}
}

extern "C" {
 fn nsOklchColor(lightness:i32,chroma:i32,hueMilliDegrees:i32)->i32;
 fn nsOklchLightness(color:u32)->i32;
}
/// Gamut-mapped sRGB from L/1000, C/10000, signed hue/1000 degrees.
/// Reduces chroma at fixed L/h. Invalid L/C returns Error; no retained state.
/// Example: `let color = oklchColor(700, 1200, 270000)?;`
#[allow(non_snake_case)]
pub fn oklchColor(lightness:i32,chroma:i32,hueMilliDegrees:i32)->Result<u32,Error>{
 if !(0..=1000).contains(&lightness)||!(0..=4000).contains(&chroma){return Err(Error("OKLCh L/C outside range".into()));}
 // SAFETY: scalar-only integer ABI; input bounds checked above.
 Ok(unsafe{nsOklchColor(lightness,chroma,hueMilliDegrees)} as u32)
}
/// Return Oklab L * 1000 for 24-bit sRGB. Invalid RGB returns Error.
#[allow(non_snake_case)]
pub fn oklchLightness(color:u32)->Result<i32,Error>{
 if color>0xffffff{return Err(Error("24-bit RGB required".into()));}
 // SAFETY: scalar-only integer ABI; color range checked.
 Ok(unsafe{nsOklchLightness(color)})
}
#[cfg(test)] mod oklch_tests {
 use super::*;
 #[test] fn endpoints_and_invalid(){assert_eq!(oklchColor(0,4000,270000).unwrap(),0);assert_eq!(oklchColor(1000,0,0).unwrap(),0xffffff);assert!(oklchColor(-1,0,0).is_err());assert!(oklchLightness(0x1000000).is_err());}
 #[test] fn sweep_holds_lightness(){for h in (0..360000).step_by(3000){let c=oklchColor(700,3000,h).unwrap();assert!((oklchLightness(c).unwrap()-700).abs()<=5);}}
}
