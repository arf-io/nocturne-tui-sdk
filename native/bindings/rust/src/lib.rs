//! Direct owned C-ABI context. No interpreter, subprocess, clock, or terminal ownership.
//! All mutating/borrowed C calls require `&mut self`; the raw context cannot be shared.
//!
//! ```
//! use nocturne_native::NativeScene;
//! let mut scene = NativeScene::new(2030)?;
//! scene.command(r#"{"op":"pause","paused":true}"#)?;
//! scene.command(r#"{"op":"input","text":"Immediate native ink"}"#)?;
//! let before = scene.snapshot()?;
//! let frame = scene.render()?;
//! assert_eq!(frame.bytes.len(), (frame.width * frame.height * 16) as usize);
//! assert_eq!(scene.snapshot()?, before); // rendering is not a state transition
//! assert!(scene.info().contains("Immediate native ink"));
//! # Ok::<(), String>(())
//! ```
#![allow(non_snake_case)]
mod document;
mod model;
mod modal;
use std::{alloc::{alloc_zeroed,dealloc,Layout},ffi::{c_char,c_void,CStr},ptr::NonNull,slice};

#[repr(C)] struct NrContext { _private: [u8;0] }
extern "C" {
 fn nrScriptRuns(text:*const u32,count:u32,out:*mut u32,capacity:u32)->i32;
 fn nrBidiClusterLines(text:*const u32,count:u32,ends:*const u32,lines:u32,direction:u32,out:*mut u32,capacity:u32)->i32;
 fn nrSurfaceFluid(ctx:*const NrContext,id:u32,out:*mut f64,capacity:u32)->i32;
 fn nrSurfaceFluidAngular(ctx:*const NrContext,id:u32,out:*mut f64,capacity:u32)->i32;
 fn nrHullMeshImmersion(vertices:*const f64,count:u32,faces:*const u32,triangles:u32,water:*const f64,water_count:u32,out:*mut f64,capacity:u32)->i32;
 fn nrFloatHull(ctx:*const NrContext,id:u32,out:*mut f64,capacity:u32)->i32;
 fn nrHullImmersion(vertices:*const f64,count:u32,faces:*const u32,triangles:u32,height:f64,out:*mut f64,capacity:u32)->i32;
 fn nrFluidDragExchange(body_mass:f64,water_mass:f64,conductance:f64,seconds:f64,body_velocity:*const f64,water_velocity:*const f64,out:*mut f64,capacity:u32)->i32;
 fn nrAngularDragExchange(body_inertia:*const f64,water_inertia:*const f64,conductance:*const f64,seconds:f64,body_omega:*const f64,water_omega:*const f64,out:*mut f64,capacity:u32)->i32;
 fn nrHullImmersionPlane(vertices:*const f64,count:u32,faces:*const u32,triangles:u32,point:*const f64,normal:*const f64,out:*mut f64,capacity:u32)->i32;
 fn nrHullBuoyancyPlane(vertices:*const f64,count:u32,faces:*const u32,triangles:u32,point:*const f64,normal:*const f64,density:f64,gravity:f64,mass:f64,center:*const f64,out:*mut f64,capacity:u32)->i32;
 fn nrNegotiateShortcuts(actions:*const u32,action_count:u32,candidates:*const u32,candidate_count:u32,host:*const u32,host_count:u32,out:*mut u32,capacity:u32)->i32;
 fn nrPathSample(points:*const f64,count:u32,closed:i32,mode:i32,distance:f64,out:*mut f64,capacity:u32)->i32;
 fn nrWaveSample(waves:*const f64,count:u32,x:f64,z:f64,seconds:f64,out:*mut f64,capacity:u32)->i32;
    fn nrSurfaceFoam(ctx:*const NrContext,id:u32,out:*mut f64,capacity:u32)->i32;
    fn nrFlowThickness(ctx:*const NrContext,id:u32,out:*mut f64,capacity:u32)->i32;
    fn nrSurfaceTriangles(ctx:*const NrContext,id:u32,out:*mut f64,capacity:u32)->i32;
    fn nrSurfaceFoamTransport(ctx:*const NrContext,id:u32,out:*mut f64,capacity:u32)->i32;
    fn nrPromptLayout(ctx:*const NrContext,out:*mut f64,capacity:u32)->i32;
    fn nrPromptVisualLayout(ctx:*const NrContext,out:*mut f64,capacity:u32)->i32;
    fn nrSourceStageTween(from:i32,to:i32,elapsed:u64,duration:u32,easing:i32)->i32;
    fn nrSourceStageInkOpacity(age:u32,fade:u32,row:i32,band:i32,minimum:i32)->i32;
    fn nrSourceStageHit(ctx:*const NrContext,x:i32,y:i32,out:*mut i32,capacity:u32)->i32;
    fn nrAreaGeometry(ctx:*const NrContext,id:u32,out:*mut f64,capacity:u32)->i32;
    fn nrFieldSample(ctx:*const NrContext,id:u32,x:f64,y:f64,out:*mut f64,capacity:u32)->i32;
    fn nrThermalSample(ctx:*const NrContext,index:u32,out:*mut f64,capacity:u32)->i32;
    fn nrWaterSample(ctx:*const NrContext,index:u32,out:*mut f64,capacity:u32)->i32;
    fn nrFloatBody(ctx:*const NrContext,id:u32,out:*mut f64,capacity:u32)->i32;
    fn nrSurfaceWaveSample(ctx:*const NrContext,id:u32,x:f64,z:f64,out:*mut f64,capacity:u32)->i32;
    fn nrContextSize()->u32;
    fn nrRenderMemorySize(ctx:*const NrContext)->u64;
    fn nrRenderMemoryCapacity(ctx:*const NrContext)->u64;
    fn nrSetRenderMemory(ctx:*mut NrContext,memory:*mut c_void,capacity:u64)->i32;
    fn nrSnapshotSizeFor(ctx:*const NrContext)->u32;
    fn nrPromptMemorySize(ctx:*const NrContext)->u64;
    fn nrPromptMemoryCapacity(ctx:*const NrContext)->u64;
    fn nrSetPromptMemory(ctx:*mut NrContext,memory:*mut c_void,capacity:u64)->i32;
    fn nrInit(memory:*mut c_void, capacity:u32, seed:u32)->i32;
    fn nrCommand(ctx:*mut NrContext,json:*const c_char,length:u32)->i32;
    fn nrRender(ctx:*mut NrContext)->u32;
    fn nrCells(ctx:*const NrContext)->*const u8;
    fn nrInspectCharacterCell(ctx:*const NrContext,x:i32,y:i32,out:*mut RawCharacterCellInfo,capacity:u32)->i32;
    fn nrWidth(ctx:*const NrContext)->u32;
    fn nrHeight(ctx:*const NrContext)->u32;
    fn nrInfo(ctx:*mut NrContext)->*const c_char;
    fn nrInfoPage(ctx:*mut NrContext,offset:u32,destination:*mut c_void,capacity:u32,words:*mut u32,word_capacity:u32)->i32;
    fn nrError(ctx:*const NrContext)->*const c_char;
    fn nrCatalogue()->*const c_char;
    fn nrSave(ctx:*const NrContext,destination:*mut c_void,capacity:u32)->i32;
    fn nrLoad(ctx:*mut NrContext,source:*const c_void,length:u32)->i32;
    fn nrOklch(l:i32,c:i32,h:i32)->u32;
    fn nrComposite(base:u32,source:u32,ba:u32,sa:u32,blend:u32,operation:u32,seed:u32,out:*mut u32)->i32;
    fn nrCompositeInSpace(base:u32,source:u32,ba:u32,sa:u32,blend:u32,operation:u32,seed:u32,space:u32,out:*mut u32)->i32;
    fn nrTextTrailSample(ctx:*const NrContext,id:u32,index:u32,trail:u32,out:*mut i32,capacity:u32)->i32;
    fn nrTextClusterSample(ctx:*const NrContext,id:u32,index:u32,out:*mut i32,capacity:u32)->i32;
    fn nrTextSample(ctx:*const NrContext,id:u32,index:u32,out:*mut i32,capacity:u32)->i32;
    fn nrWindowSample(ctx:*const NrContext,id:u32,u:u32,v:u32,visibility:u32,out:*mut i32,capacity:u32)->i32;
    fn nrGraphemeBreaks(text:*const u32,count:u32,out:*mut u32,capacity:u32)->i32;
    fn nrLineBreakDetails(text:*const u32,count:u32,out:*mut u32,capacity:u32)->i32;
    fn nrLineBreaks(text:*const u32,count:u32,out:*mut u32,capacity:u32)->i32;
    fn nrPromptSelection(context:*mut NrContext,out:*mut u32,capacity:u32)->i32;
    fn nrTextRunClusters(ctx:*const NrContext,kind:u32,id:u32,out:*mut u32,capacity:u32)->i32;
    fn nrTextRunSource(ctx:*mut NrContext,kind:u32,id:u32,out:*mut u32,capacity:u32)->i32;
    fn nrTextRunLayout(ctx:*mut NrContext,kind:u32,id:u32,ambiguous:u32,columns:u32,out:*mut u32,capacity:u32)->i32;
    fn nrTextRunHit(ctx:*mut NrContext,kind:u32,id:u32,ambiguous:u32,columns:u32,column:u32,row:u32)->i32;
    fn nrTextRunClip(ctx:*mut NrContext,kind:u32,id:u32,ambiguous:u32,columns:u32,x:u32,y:u32,width:u32,height:u32,out:*mut u32,capacity:u32)->i32;
    fn nrBidiClusterLayout(text:*const u32,count:u32,ambiguous:u32,columns:u32,direction:u32,out:*mut u32,capacity:u32)->i32;
    fn nrBidiClusterHit(text:*const u32,count:u32,ambiguous:u32,columns:u32,direction:u32,column:u32,row:u32)->i32;
    fn nrBidiCaret(text:*const u32,count:u32,ambiguous:u32,columns:u32,direction:u32,offset:u32,affinity:u32,out:*mut u32,capacity:u32)->i32;
    fn nrBidiVisual(text:*const u32,count:u32,direction:u32,out:*mut u32,capacity:u32)->i32;
    fn nrGraphemeHit(text:*const u32,count:u32,ambiguous:u32,columns:u32,column:u32,row:u32)->i32;
    fn nrGraphemeLayout(text:*const u32,count:u32,ambiguous:u32,columns:u32,out:*mut u32,capacity:u32)->i32;
    fn nrGraphemeWidths(text:*const u32,count:u32,ambiguous:u32,out:*mut u32,capacity:u32)->i32;
    fn nrParticleMotion(ctx:*const NrContext,index:u32,out:*mut f64,capacity:u32)->i32;
    fn nrParticle(ctx:*const NrContext,index:u32,out:*mut i32,capacity:u32)->i32;
}
/// A copied frame: four little-endian u32 words per cell, no borrowed C pointers.
#[derive(Clone,Debug,PartialEq,Eq)]
pub struct Frame { pub width:u32, pub height:u32, pub bytes:Vec<u8> }
#[repr(C)]
struct RawCharacterCellInfo {words:[u32;5],role:[u8;129],state:[u8;129],path:[u8;128]}
#[derive(Clone,Debug,PartialEq,Eq)]
pub struct CharacterCellInfo {pub glyph:u32,pub foreground:u32,pub background:u32,pub id:u32,pub index:u32,pub role:String,pub state:String,pub path:String}
/// One exclusively owned, eight-byte-aligned native context. Drop releases it.
pub struct NativeScene { memory:NonNull<u8>, layout:Layout,render_memory:Option<(NonNull<u8>,Layout)>,prompt_memory:Option<(NonNull<u8>,Layout)>,model_memory:Option<(NonNull<u8>,Layout)>,modal_memory:Option<(NonNull<u8>,Layout)> }
impl NativeScene {
    /// Allocate a context. `seed` controls deterministic particle identities.
    /// Returns an error on allocation or native initialization failure.
    pub fn new(seed:u32)->Result<Self,String> {
        let size=unsafe{nrContextSize()} as usize;
        let layout=Layout::from_size_align(size,8).map_err(|e|e.to_string())?;
        let memory=NonNull::new(unsafe{alloc_zeroed(layout)}).ok_or("allocation failed")?;
        let scene=Self{memory,layout,render_memory:None,prompt_memory:None,model_memory:None,modal_memory:None};
        if unsafe{nrInit(scene.memory.as_ptr().cast(),size as u32,seed)}!=0 {return Err("native init failed".into());}
        Ok(scene)
    }
    fn ptr(&self)->*mut NrContext {self.memory.as_ptr().cast()}
    fn ensure_prompt_memory(&mut self)->Result<(),String> {
        let required=unsafe{nrPromptMemorySize(self.ptr())};
        if required<=unsafe{nrPromptMemoryCapacity(self.ptr())}{return Err("prompt storage request made no progress".into());}
        let size=usize::try_from(required).map_err(|_|"prompt exceeds address space")?;
        let layout=Layout::from_size_align(size,8).map_err(|e|e.to_string())?;
        let memory=NonNull::new(unsafe{alloc_zeroed(layout)}).ok_or("prompt allocation failed")?;
        if unsafe{nrSetPromptMemory(self.ptr(),memory.as_ptr().cast(),required)}!=0 {
            unsafe{dealloc(memory.as_ptr(),layout)};return Err("prompt storage rejected".into());
        }
        if let Some((old,old_layout))=self.prompt_memory.replace((memory,layout)){unsafe{dealloc(old.as_ptr(),old_layout)}}
        Ok(())
    }
    fn ensure_render_memory(&mut self)->Result<(),String> {
        let required=unsafe{nrRenderMemorySize(self.ptr())};
        if required<=unsafe{nrRenderMemoryCapacity(self.ptr())}{return Ok(());}
        let size=usize::try_from(required).map_err(|_|"viewport exceeds address space")?;
        let layout=Layout::from_size_align(size,8).map_err(|e|e.to_string())?;
        let memory=NonNull::new(unsafe{alloc_zeroed(layout)}).ok_or("viewport allocation failed")?;
        if unsafe{nrSetRenderMemory(self.ptr(),memory.as_ptr().cast(),required)}!=0 {
            unsafe{dealloc(memory.as_ptr(),layout)};return Err("viewport render memory rejected".into());
        }
        if let Some((old,old_layout))=self.render_memory.replace((memory,layout)){unsafe{dealloc(old.as_ptr(),old_layout)}}
        Ok(())
    }
    /// Apply one bounded UTF-8 JSON transaction. True means more catch-up remains.
    /// Invalid commands leave authoritative scene state unchanged.
    pub fn command(&mut self,json:&str)->Result<bool,String> {
        let length=u32::try_from(json.len()).map_err(|_|"command exceeds ABI addressability")?;
        let mut status=unsafe{nrCommand(self.ptr(),json.as_ptr().cast(),length)};
        while status<0 {
            match unsafe{CStr::from_ptr(nrError(self.ptr()))}.to_bytes() {
                b"Modal storage required" => self.ensure_modal_memory()?,
                b"Prompt storage required" => self.ensure_prompt_memory()?,
                b"Viewport render memory required" => {
                    let before=unsafe{nrRenderMemoryCapacity(self.ptr())};
                    self.ensure_render_memory()?;
                    if unsafe{nrRenderMemoryCapacity(self.ptr())}<=before{return Err("viewport storage request made no progress".into());}
                },
                _ => break,
            }
            status=unsafe{nrCommand(self.ptr(),json.as_ptr().cast(),length)};
        }
        if status<0{return Err(unsafe{CStr::from_ptr(nrError(self.ptr()))}.to_string_lossy().into_owned());}
        Ok(status==1)
    }
    /// Synchronous explicit-time catch-up; UI hosts should yield between command batches.
    pub fn advanceTo(&mut self,timeUs:u64)->Result<(),String>{
        let command=format!("{{\"op\":\"time\",\"timeUs\":{timeUs}}}");
        while self.command(&command)?{} Ok(())
    }
    /// Pure presentation. The returned bytes remain valid after later scene calls.
    pub fn render(&mut self)->Result<Frame,String>{
        self.ensure_render_memory()?;
        let n=unsafe{nrRender(self.ptr())};if n==0{return Err("render failed".into());}
        let bytes=unsafe{slice::from_raw_parts(nrCells(self.ptr()),n as usize*16)}.to_vec();
        Ok(Frame{width:unsafe{nrWidth(self.ptr())},height:unsafe{nrHeight(self.ptr())},bytes})
    }
    /// Copy semantic metadata from the latest render; never draw implicitly.
    pub fn inspectCharacterCell(&mut self,x:i32,y:i32)->Result<CharacterCellInfo,String>{
        let mut out=RawCharacterCellInfo{words:[0;5],role:[0;129],state:[0;129],path:[0;128]};
        let status=unsafe{nrInspectCharacterCell(self.ptr(),x,y,&mut out,std::mem::size_of::<RawCharacterCellInfo>() as u32)};
        if status==-2{return Err("render required before cell inspection".into());}if status!=0{return Err("cell inspection rejected".into());}
        fn text(bytes:&[u8])->Result<String,String>{let end=bytes.iter().position(|b|*b==0).ok_or("unterminated owner string")?;String::from_utf8(bytes[..end].to_vec()).map_err(|_|"invalid owner UTF-8".into())}
        Ok(CharacterCellInfo{glyph:out.words[0],foreground:out.words[1],background:out.words[2],id:out.words[3],index:out.words[4],role:text(&out.role)?,state:text(&out.state)?,path:text(&out.path)?})
    }
    /// Copied JSON metadata including complete retained text; no serde dependency required.
    pub fn info(&mut self)->String{unsafe{CStr::from_ptr(nrInfo(self.ptr()))}.to_string_lossy().into_owned()}
    /// Complete JSON recovery in 64 KiB pages, growing to the native u32 size
    /// within available memory. Allocation failures return an error.
    /// Exclusive borrowing covers the whole read. CRC32 detects accidental
    /// inconsistency, not authenticity. Do not poll this on animation frames.
    pub fn infoComplete(&mut self)->Result<String,String>{
        let mut page=vec![0u8;65536];let mut data=Vec::new();
        let mut offset=0u32;let mut identity=None;let mut crc=0xffffffffu32;
        const CRC4:[u32;16]=[0,0x1db71064,0x3b6e20c8,0x26d930ac,
          0x76dc4190,0x6b6b51f4,0x4db26158,0x5005713c,
          0xedb88320,0xf00f9344,0xd6d6a3e8,0xcb61b38c,
          0x9b64c2b0,0x86d3d2d4,0xa00ae278,0xbdbdf21c];
        loop {
            let mut words=[0u32;4];
            let status=unsafe{nrInfoPage(self.ptr(),offset,page.as_mut_ptr().cast(),65536,words.as_mut_ptr(),4)};
            if status!=0&&status!=1{return Err("metadata page rejected".into());}
            let [total,written,next,checksum]=words;
            if total<offset||written!=(total-offset).min(65536)||next!=offset+written||status!=i32::from(next<total){return Err("invalid metadata page progress".into());}
            if let Some(previous)=identity {
                if previous!=(total,checksum){return Err("metadata changed during recovery".into());}
            }else{data.try_reserve_exact(total as usize).map_err(|e|e.to_string())?;identity=Some((total,checksum));}
            for byte in &page[..written as usize] {
                let q=crc^u32::from(*byte);let q=(q>>4)^CRC4[(q&15) as usize];crc=(q>>4)^CRC4[(q&15) as usize];
            }
            data.extend_from_slice(&page[..written as usize]);offset=next;
            if status==0 {
                if data.len()!=total as usize||crc^0xffffffff!=checksum{return Err("metadata recovery checksum mismatch".into());}
                return String::from_utf8(data).map_err(|e|e.to_string());
            }
        }
    }
    /// Copied current implementation catalogue, with explicitly pending visual acceptance.
    pub fn catalogue(&self)->String{unsafe{CStr::from_ptr(nrCatalogue())}.to_string_lossy().into_owned()}
    /// Return the full pointer-free, compatible-schema state snapshot.
    pub fn snapshot(&self)->Result<Vec<u8>,String>{
        let n=unsafe{nrSnapshotSizeFor(self.ptr())};if n<24{return Err("snapshot size unavailable".into());}
        let mut bytes=Vec::new();bytes.try_reserve_exact(n as usize).map_err(|e|e.to_string())?;bytes.resize(n as usize,0);
        if unsafe{nrSave(self.ptr(),bytes.as_mut_ptr().cast(),n)}!=0{return Err("snapshot failed".into());}Ok(bytes)
    }
    /// Restore atomically. Corrupt, structurally invalid, or foreign-schema data is rejected.
    pub fn restore(&mut self,bytes:&[u8])->Result<(),String>{
        if bytes.len()<24 || u32::try_from(bytes.len()).is_err() || u32::from_le_bytes(bytes[16..20].try_into().map_err(|_|"snapshot length")?) as usize != bytes.len()-24{return Err("snapshot length".into());}
        loop {
            if unsafe{nrLoad(self.ptr(),bytes.as_ptr().cast(),bytes.len() as u32)}==0{break;}
            match unsafe{CStr::from_ptr(nrError(self.ptr()))}.to_bytes(){
                b"Prompt storage required"=>self.ensure_prompt_memory()?,
                b"Modal storage required"=>self.ensure_modal_memory()?,
                b"Model storage required"=>self.ensure_model_memory()?,
                _=>return Err("snapshot rejected".into()),
            }
        }Ok(())
    }
    /// Unicode 17 whole-grapheme script runs in owned scalar offsets.
    pub fn script_runs(&self,text:&str)->Result<Vec<ScriptRun>,String>{
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();if values.len()>2048{return Err("Script capacity".into())}
        let mut out=vec![0;values.len()*3];let count=unsafe{nrScriptRuns(values.as_ptr(),values.len() as u32,out.as_mut_ptr(),values.len() as u32)};if count<0{return Err("Invalid Unicode scalar".into())}
        out[..count as usize*3].chunks_exact(3).map(|row|Ok(ScriptRun{start:row[0],end:row[1],script:String::from_utf8(row[2].to_be_bytes().to_vec()).map_err(|_|"Invalid script tag".to_string())?})).collect()
    }
    /// Full-paragraph bidi resolution with caller-selected whole-grapheme lines.
    pub fn bidi_lines(&self,text:&str,ends:&[u32],direction:u32)->Result<Vec<[u32;7]>,String>{
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();
        if values.len()>2048||ends.len()>2048||direction>2{return Err("Invalid explicit lines".into())}
        let mut out=vec![0u32;values.len()*7];
        let count=unsafe{nrBidiClusterLines(values.as_ptr(),values.len() as u32,ends.as_ptr(),ends.len() as u32,direction,out.as_mut_ptr(),values.len() as u32)};
        if count<0{return Err("Invalid grapheme or hard-break line boundary".into())}
        Ok(out[..count as usize*7].chunks_exact(7).map(|row|row.try_into().unwrap()).collect())
    }
    /// Unicode 17 extended grapheme boundaries in owned scalar offsets.
    pub fn line_breaks(&self,text:&str)->Result<Vec<u32>,String>{
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();
        if values.len()>2048{return Err("Line-break capacity".into());}
        let mut out=vec![0;values.len()+1];
        let count=unsafe{nrLineBreaks(values.as_ptr(),values.len() as u32,out.as_mut_ptr(),out.len() as u32)};
        if count<0{return Err("Invalid Unicode scalar".into());}out.truncate(count as usize);Ok(out)
    }

    /// Owned scalar offset and mandatory (0 or 1) line-break rows.
    pub fn line_break_details(&self,text:&str)->Result<Vec<[u32;2]>,String>{
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();
        if values.len()>2048{return Err("Line-break capacity".into());}
        let mut out=vec![0;2*(values.len()+1)];
        let count=unsafe{nrLineBreakDetails(values.as_ptr(),values.len() as u32,out.as_mut_ptr(),(values.len()+1) as u32)};
        if count<0{return Err("Invalid Unicode scalar".into());}
        Ok(out[..count as usize*2].chunks_exact(2).map(|row|[row[0],row[1]]).collect())
    }

    pub fn grapheme_boundaries(&self,text:&str)->Result<Vec<u32>,String>{
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();
        if values.len()>2048{return Err("Grapheme capacity".into());}
        let mut out=vec![0;values.len()+1];
        let count=unsafe{nrGraphemeBreaks(values.as_ptr(),values.len() as u32,out.as_mut_ptr(),out.len() as u32)};
        if count<0{return Err("Invalid Unicode scalar".into());}out.truncate(count as usize);Ok(out)
    }
    /// Owned [start scalar, end scalar, columns] under nr-grapheme-cell-width-v1.
    pub fn grapheme_widths(&self,text:&str,ambiguous:u32)->Result<Vec<[u32;3]>,String>{
        if ambiguous!=1&&ambiguous!=2{return Err("Ambiguous width must be 1 or 2".into());}
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();
        if values.len()>2048{return Err("Grapheme capacity".into());}
        let mut out=vec![0;values.len()*3];
        let count=unsafe{nrGraphemeWidths(values.as_ptr(),values.len() as u32,ambiguous,out.as_mut_ptr(),values.len() as u32)};
        if count<0{return Err("Invalid Unicode scalar".into());}
        Ok(out[..count as usize*3].chunks_exact(3).map(|r|[r[0],r[1],r[2]]).collect())
    }
    /// Owned [start scalar, end scalar, column, row, width] under nr-grapheme-layout-v1.
    pub fn grapheme_layout(&self,text:&str,columns:u32,ambiguous:u32)->Result<Vec<[u32;5]>,String>{
        if columns==0{return Err("Positive columns required".into());}
        if ambiguous!=1&&ambiguous!=2{return Err("Ambiguous width must be 1 or 2".into());}
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();
        if values.len()>2048{return Err("Grapheme capacity".into());}
        let mut out=vec![0;values.len()*5];
        let count=unsafe{nrGraphemeLayout(values.as_ptr(),values.len() as u32,ambiguous,columns,out.as_mut_ptr(),values.len() as u32)};
        if count<0{return Err("Invalid Unicode scalar".into());}
        Ok(out[..count as usize*5].chunks_exact(5).map(|r|[r[0],r[1],r[2],r[3],r[4]]).collect())
    }
    pub fn text_run_clusters(&self,kind:u32,id:u32)->Result<Vec<[u32;4]>,String>{
        let n=unsafe{nrTextRunClusters(self.ptr(),kind,id,std::ptr::null_mut(),0)};
        if n<0{return Err("Invalid text run query".into());}if n==0{return Ok(Vec::new());}
        let size=(n as usize).checked_mul(4).ok_or("text query exceeds address space")?;
        let mut out=Vec::new();out.try_reserve_exact(size).map_err(|e|e.to_string())?;out.resize(size,0u32);
        if unsafe{nrTextRunClusters(self.ptr(),kind,id,out.as_mut_ptr(),n as u32)}!=n{return Err("Text run changed during read".into());}
        if n<0{return Err("Missing or invalid text run".into());}
        Ok(out[..n as usize*4].chunks_exact(4).map(|r|[r[0],r[1],r[2],r[3]]).collect())
    }
    pub fn text_run_source(&self,kind:u32,id:u32)->Result<String,String>{
        let n=unsafe{nrTextRunSource(self.ptr(),kind,id,std::ptr::null_mut(),0)};
        if n<0{return Err("Missing or invalid text run".into());}
        if n==0{return Ok(String::new());}
        let mut out=vec![0u32;n as usize];let written=unsafe{nrTextRunSource(self.ptr(),kind,id,out.as_mut_ptr(),n as u32)};
        if written!=n{return Err("Text source changed during read".into());}
        let mut text=String::new();for &scalar in &out[..n as usize]{text.push(char::from_u32(scalar).ok_or("Invalid source scalar")?);}Ok(text)
    }
    pub fn text_run_layout(&self,kind:u32,id:u32,columns:u32,ambiguous:u32)->Result<Vec<[u32;7]>,String>{
        let n=unsafe{nrTextRunLayout(self.ptr(),kind,id,ambiguous,columns,std::ptr::null_mut(),0)};
        if n<0{return Err("Invalid text run query".into());}if n==0{return Ok(Vec::new());}
        let size=(n as usize).checked_mul(7).ok_or("text query exceeds address space")?;
        let mut out=Vec::new();out.try_reserve_exact(size).map_err(|e|e.to_string())?;out.resize(size,0u32);
        if unsafe{nrTextRunLayout(self.ptr(),kind,id,ambiguous,columns,out.as_mut_ptr(),n as u32)}!=n{return Err("Text run changed during read".into());}
        if n<0{return Err("Missing run or invalid layout policy".into());}
        Ok(out[..n as usize*7].chunks_exact(7).map(|r|[r[0],r[1],r[2],r[3],r[4],r[5],r[6]]).collect())
    }
    pub fn text_run_hit(&self,kind:u32,id:u32,columns:u32,column:u32,row:u32,ambiguous:u32)->Result<u32,String>{
        let n=unsafe{nrTextRunHit(self.ptr(),kind,id,ambiguous,columns,column,row)};
        if n<0{return Err("Missing run or invalid layout policy".into());}Ok(n as u32)
    }
    pub fn text_run_clip(&self,kind:u32,id:u32,columns:u32,x:u32,y:u32,width:u32,height:u32,ambiguous:u32)->Result<Vec<[u32;9]>,String>{
        let n=unsafe{nrTextRunClip(self.ptr(),kind,id,ambiguous,columns,x,y,width,height,std::ptr::null_mut(),0)};
        if n<0{return Err("Invalid text run query".into());}if n==0{return Ok(Vec::new());}
        let size=(n as usize).checked_mul(9).ok_or("text query exceeds address space")?;
        let mut out=Vec::new();out.try_reserve_exact(size).map_err(|e|e.to_string())?;out.resize(size,0u32);
        if unsafe{nrTextRunClip(self.ptr(),kind,id,ambiguous,columns,x,y,width,height,out.as_mut_ptr(),n as u32)}!=n{return Err("Text run changed during read".into());}
        if n<0{return Err("Missing run or invalid layout policy".into());}
        Ok(out[..n as usize*9].chunks_exact(9).map(|r|[r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8]]).collect())
    }
    pub fn surface_foam(&self,id:u32)->Result<Vec<[f64;5]>,String>{
        let mut out=vec![0.0;256*5];let count=unsafe{nrSurfaceFoam(self.ptr(),id,out.as_mut_ptr(),256)};
        if count<0{return Err("Invalid surface foam query".into())}Ok(out[..count as usize*5].chunks_exact(5).map(|r|[r[0],r[1],r[2],r[3],r[4]]).collect())
    }
    /// Owned final velocities, water impulse and dissipated relative energy.
    pub fn angular_drag_exchange(&self,body_inertia:[f64;3],water_inertia:[f64;3],conductance:[f64;3],seconds:f64,body_omega:[f64;3],water_omega:[f64;3])->Result<[f64;10],String>{
        let mut out=[0.0;10];if unsafe{nrAngularDragExchange(body_inertia.as_ptr(),water_inertia.as_ptr(),conductance.as_ptr(),seconds,body_omega.as_ptr(),water_omega.as_ptr(),out.as_mut_ptr(),10)}!=1{return Err("Invalid finite-inertia angular exchange".into())}Ok(out)
    }
    /// Owned final velocities, water impulse and dissipated relative energy.
    pub fn fluid_drag_exchange(&self,body_mass:f64,water_mass:f64,conductance:f64,seconds:f64,body_velocity:[f64;3],water_velocity:[f64;3])->Result<[f64;10],String>{
        let mut out=[0.0;10];if unsafe{nrFluidDragExchange(body_mass,water_mass,conductance,seconds,body_velocity.as_ptr(),water_velocity.as_ptr(),out.as_mut_ptr(),10)}!=1{return Err("Invalid finite-mass drag parameters".into())}Ok(out)
    }
    /// Owned immersion in an explicitly oriented water half-space.
    pub fn hull_immersion_plane(&self,vertices:&[[f64;3]],faces:&[[u32;3]],point:[f64;3],normal:[f64;3])->Result<[f64;5],String>{
        if !(4..=128).contains(&vertices.len())||!(4..=256).contains(&faces.len()){return Err("Hull size".into())}
        let mut out=[0.0;5];if unsafe{nrHullImmersionPlane(vertices.as_ptr().cast(),vertices.len() as u32,faces.as_ptr().cast(),faces.len() as u32,point.as_ptr(),normal.as_ptr(),out.as_mut_ptr(),5)}!=1{return Err("Invalid convex hull or plane".into())}Ok(out)
    }
    /// Owned immersion, net force and torque; native lift remains vertical.
    pub fn hull_buoyancy_plane(&self,vertices:&[[f64;3]],faces:&[[u32;3]],point:[f64;3],normal:[f64;3],density:f64,gravity:f64,mass:f64,center_of_mass:[f64;3])->Result<[f64;11],String>{
        if !(4..=128).contains(&vertices.len())||!(4..=256).contains(&faces.len()){return Err("Hull size".into())}
        let mut out=[0.0;11];if unsafe{nrHullBuoyancyPlane(vertices.as_ptr().cast(),vertices.len() as u32,faces.as_ptr().cast(),faces.len() as u32,point.as_ptr(),normal.as_ptr(),density,gravity,mass,center_of_mass.as_ptr(),out.as_mut_ptr(),11)}!=1{return Err("Invalid hull buoyancy parameters".into())}Ok(out)
    }
    pub fn hull_immersion(&self,vertices:&[[f64;3]],faces:&[[u32;3]],height:f64)->Result<[f64;5],String>{
        if !(4..=128).contains(&vertices.len())||!(4..=256).contains(&faces.len()){return Err("Hull size".into())}
        let mut out=[0.0;5];if unsafe{nrHullImmersion(vertices.as_ptr().cast(),vertices.len() as u32,faces.as_ptr().cast(),faces.len() as u32,height,out.as_mut_ptr(),5)}!=1{return Err("Invalid convex hull".into())}Ok(out)
    }
    pub fn hull_mesh_immersion(&self,vertices:&[[f64;3]],faces:&[[u32;3]],water:&[[f64;9]])->Result<[f64;5],String>{
        if !(4..=128).contains(&vertices.len())||!(4..=256).contains(&faces.len())||!(1..=256).contains(&water.len()){return Err("Hull/surface size".into())}
        let mut out=[0.0;5];if unsafe{nrHullMeshImmersion(vertices.as_ptr().cast(),vertices.len() as u32,faces.as_ptr().cast(),faces.len() as u32,water.as_ptr().cast(),water.len() as u32,out.as_mut_ptr(),5)}!=1{return Err("Invalid hull/surface mesh".into())}Ok(out)
    }
    pub fn surface_fluid_angular(&self,id:u32)->Result<Option<[f64;12]>,String>{
        let mut out=[0.0;12];match unsafe{nrSurfaceFluidAngular(self.ptr(),id,out.as_mut_ptr(),12)}{1=>Ok(Some(out)),0=>Ok(None),_=>Err("Invalid angular fluid query".into())}
    }
    pub fn surface_fluid(&self,id:u32)->Result<Option<[f64;15]>,String>{
        let mut out=[0.0;15];match unsafe{nrSurfaceFluid(self.ptr(),id,out.as_mut_ptr(),15)}{1=>Ok(Some(out)),0=>Ok(None),_=>Err("Invalid finite water query".into())}
    }
    pub fn float_hull(&self,id:u32)->Result<Option<[f64;14]>,String>{
        let mut out=[0.0;14];match unsafe{nrFloatHull(self.ptr(),id,out.as_mut_ptr(),14)}{1=>Ok(Some(out)),0=>Ok(None),_=>Err("Invalid hull query".into())}
    }
    pub fn prompt_layout(&self)->Result<Vec<[f64;8]>,String>{let n=unsafe{nrPromptLayout(self.ptr(),std::ptr::null_mut(),0)};if n<0{return Err("Invalid prompt layout".into());}let mut rows=vec![[0.0;8];n as usize];if n>0&&unsafe{nrPromptLayout(self.ptr(),rows.as_mut_ptr() as *mut f64,n as u32)}!=n{return Err("Invalid prompt layout".into());}Ok(rows)}
    pub fn prompt_visual_layout(&self)->Result<Vec<[f64;10]>,String>{let n=unsafe{nrPromptVisualLayout(self.ptr(),std::ptr::null_mut(),0)};if n<0{return Err("Invalid prompt layout".into());}let mut rows=vec![[0.0;10];n as usize];if n>0&&unsafe{nrPromptVisualLayout(self.ptr(),rows.as_mut_ptr() as *mut f64,n as u32)}!=n{return Err("Invalid prompt layout".into());}Ok(rows)}
    /// Original Stage interpolation using explicit milliseconds.
    pub fn source_stage_tween(&self,from:i32,to:i32,elapsed:u64,duration:u32,easing:i32)->Result<i32,String>{if !(0..=3).contains(&easing){return Err("Invalid source Stage easing".into());}Ok(unsafe{nrSourceStageTween(from,to,elapsed,duration,easing)})}
    /// Original arrival and top-horizon ink opacity, in thousandths.
    pub fn source_stage_ink_opacity(&self,age:u32,fade:u32,row:i32,band:i32,minimum:i32)->Result<i32,String>{let v=unsafe{nrSourceStageInkOpacity(age,fade,row,band,minimum)};if v<0{Err("Invalid source Stage opacity".into())}else{Ok(v)}}
    /// Owned original semantic ID and zero-based subitem, without rendering.
    pub fn source_stage_hit(&self,x:i32,y:i32)->Result<Option<[i32;2]>,String>{let mut out=[0;2];match unsafe{nrSourceStageHit(self.ptr(),x,y,out.as_mut_ptr(),2)}{1=>Ok(Some(out)),0=>Ok(None),_=>Err("Invalid source Stage hit".into())}}
    pub fn area_geometry(&self,id:u32)->Result<Option<[f64;12]>,String>{
        let mut out=[0.0;12];match unsafe{nrAreaGeometry(self.ptr(),id,out.as_mut_ptr(),12)}{1=>Ok(Some(out)),0=>Ok(None),_=>Err("Invalid area geometry".into())}
    }
    pub fn field_sample(&self,id:u32,x:f64,y:f64)->Result<Option<[f64;4]>,String>{
        let mut out=[0.0;4];match unsafe{nrFieldSample(self.ptr(),id,x,y,out.as_mut_ptr(),4)}{1=>Ok(Some(out)),0=>Ok(None),_=>Err("Invalid field sample".into())}
    }
    pub fn water_sample(&self,index:u32)->Result<Option<[f64;8]>,String>{
        let mut out=[0.0;8];match unsafe{nrWaterSample(self.ptr(),index,out.as_mut_ptr(),8)}{1=>Ok(Some(out)),0=>Ok(None),_=>Err("Invalid water sample".into())}
    }
    pub fn thermal_sample(&self,index:u32)->Result<Option<[f64;10]>,String>{
        let mut out=[0.0;10];match unsafe{nrThermalSample(self.ptr(),index,out.as_mut_ptr(),10)}{1=>Ok(Some(out)),0=>Ok(None),_=>Err("Invalid thermal sample".into())}
    }
    pub fn surface_foam_transport(&self,id:u32)->Result<Vec<[f64;7]>,String>{
        let mut out=vec![0.0;256*7];let count=unsafe{nrSurfaceFoamTransport(self.ptr(),id,out.as_mut_ptr(),256)};
        if count<0{return Err("Invalid surface foam query".into())}Ok(out[..count as usize*7].chunks_exact(7).map(|r|[r[0],r[1],r[2],r[3],r[4],r[5],r[6]]).collect())
    }
    pub fn flow_thickness(&self,id:u32)->Result<Option<[f64;6]>,String>{
        let mut out=[0.0;6];match unsafe{nrFlowThickness(self.ptr(),id,out.as_mut_ptr(),6)}{1=>Ok(Some(out)),0=>Ok(None),_=>Err("Invalid flow thickness query".into())}
    }
    pub fn surface_triangles(&self,id:u32)->Result<Vec<[f64;12]>,String>{
        let mut out=vec![0.0;256*12];let count=unsafe{nrSurfaceTriangles(self.ptr(),id,out.as_mut_ptr(),256)};
        if count<0{return Err("Invalid surface geometry query".into())}Ok(out[..count as usize*12].chunks_exact(12).map(|r|{let mut row=[0.0;12];row.copy_from_slice(r);row}).collect())
    }
    pub fn float_body(&self,id:u32)->Result<Option<[f64;12]>,String>{
        let mut out=[0.0;12];match unsafe{nrFloatBody(self.ptr(),id,out.as_mut_ptr(),12)}{1=>Ok(Some(out)),0=>Ok(None),_=>Err("Invalid float body query".into())}
    }
    pub fn surface_wave_sample(&self,id:u32,x:f64,z:f64)->Result<[f64;6],String>{
        let mut out=[0.0;6];if unsafe{nrSurfaceWaveSample(self.ptr(),id,x,z,out.as_mut_ptr(),6)}!=1{return Err("Invalid surface wave sample".into())}Ok(out)
    }
    pub fn path_sample(&self,points:&[[f64;3]],distance:f64,closed:bool,mode:u32)->Result<[f64;8],String>{
        if points.len()<2||points.len()>129||mode>2{return Err("Invalid path shape or mode".into())}
        let mut out=[0.0;8];if unsafe{nrPathSample(points.as_ptr().cast(),points.len() as u32,closed as i32,mode as i32,distance,out.as_mut_ptr(),8)}!=1{return Err("Invalid path parameters".into())}Ok(out)
    }
    pub fn wave_sample(&self,waves:&[[f64;5]],x:f64,z:f64,seconds:f64)->Result<[f64;6],String>{
        if waves.len()>32{return Err("Wave capacity".into())}
        let mut out=[0.0;6];
        if unsafe{nrWaveSample(waves.as_ptr().cast(),waves.len() as u32,x,z,seconds,out.as_mut_ptr(),6)}!=1{return Err("Invalid wave field".into())}
        Ok(out)
    }
    pub fn bidi_visual(&self,text:&str,direction:u32)->Result<Vec<[u32;4]>,String>{
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();
        if values.len()>2048||direction>2{return Err("Invalid bidi capacity or direction".into());}
        let mut out=vec![0u32;values.len().max(1)*4];let n=unsafe{nrBidiVisual(values.as_ptr(),values.len() as u32,direction,out.as_mut_ptr(),values.len() as u32)};
        if n<0{return Err("Invalid Unicode scalar".into());}
        Ok(out[..n as usize*4].chunks_exact(4).map(|r|[r[0],r[1],r[2],r[3]]).collect())
    }
    pub fn bidi_layout(&self,text:&str,columns:u32,direction:u32,ambiguous:u32)->Result<Vec<[u32;7]>,String>{
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();
        if values.len()>2048||direction>2||columns==0||(ambiguous!=1&&ambiguous!=2){return Err("Invalid bidi layout policy or capacity".into());}
        let mut out=vec![0u32;values.len().max(1)*7];let n=unsafe{nrBidiClusterLayout(values.as_ptr(),values.len() as u32,ambiguous,columns,direction,out.as_mut_ptr(),values.len() as u32)};
        if n<0{return Err("Invalid Unicode scalar".into());}
        Ok(out[..n as usize*7].chunks_exact(7).map(|r|[r[0],r[1],r[2],r[3],r[4],r[5],r[6]]).collect())
    }
    pub fn bidi_hit(&self,text:&str,columns:u32,column:u32,row:u32,direction:u32,ambiguous:u32)->Result<u32,String>{
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();if values.len()>2048{return Err("Bidi capacity".into());}
        let n=unsafe{nrBidiClusterHit(values.as_ptr(),values.len() as u32,ambiguous,columns,direction,column,row)};
        if n<0{return Err("Invalid bidi mapping input".into());}Ok(n as u32)
    }
    pub fn bidi_caret(&self,text:&str,columns:u32,offset:u32,affinity:u32,direction:u32,ambiguous:u32)->Result<[u32;3],String>{
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();if values.len()>2048{return Err("Bidi capacity".into());}
        let mut out=[0u32;3];if unsafe{nrBidiCaret(values.as_ptr(),values.len() as u32,ambiguous,columns,direction,offset,affinity,out.as_mut_ptr(),3)}<0{return Err("Invalid bidi caret input".into());}Ok(out)
    }
    pub fn selected_text(&self)->Result<Option<String>,String>{
        let n=unsafe{nrPromptSelection(self.ptr(),std::ptr::null_mut(),0)};
        if n<0{return Err("Invalid selection export".into());}if n==0{return Ok(None);}
        let mut out=Vec::new();out.try_reserve_exact(n as usize).map_err(|e|e.to_string())?;out.resize(n as usize,0u32);
        if unsafe{nrPromptSelection(self.ptr(),out.as_mut_ptr(),n as u32)}!=n{return Err("Selection changed during read".into());}
        if n<0{return Err("Invalid selection export".into());}if n==0{return Ok(None);}
        let mut text=String::new();for &scalar in &out[..n as usize]{text.push(char::from_u32(scalar).ok_or("Invalid selected scalar")?);}Ok(Some(text))
    }
    pub fn grapheme_hit(&self,text:&str,columns:u32,column:u32,row:u32,ambiguous:u32)->Result<u32,String>{
        if columns==0||(ambiguous!=1&&ambiguous!=2){return Err("Invalid layout policy".into());}
        let values:Vec<u32>=text.chars().take(2049).map(|c|c as u32).collect();
        if values.len()>2048{return Err("Grapheme capacity".into());}
        let result=unsafe{nrGraphemeHit(values.as_ptr(),values.len() as u32,ambiguous,columns,column,row)};
        if result<0{return Err("Invalid Unicode scalar".into());}Ok(result as u32)
    }
    pub fn particle_motions(&self)->Vec<[f64;7]>{let mut out=Vec::new();for i in 0..2048{let mut values=[0.;6];if unsafe{nrParticleMotion(self.ptr(),i,values.as_mut_ptr(),6)}>0{let mut p=[0;12];unsafe{nrParticle(self.ptr(),i,p.as_mut_ptr(),12)};let mut row=[0.;7];row[0]=(p[0] as u32) as f64;row[1..].copy_from_slice(&values);out.push(row);}}out}
    pub fn particles(&self)->Vec<[i32;12]>{let mut out=Vec::new();for i in 0..2048{let mut p=[0;12];if unsafe{nrParticle(self.ptr(),i,p.as_mut_ptr(),12)}>0{out.push(p);}}out}
    /// Pure copied scalar pose. Word two holds unsigned identity bits; XY uses Q16.
    pub fn textClusterSample(&self,id:u32,index:u32)->Result<[i32;8],String>{
        let mut out=[0;8];if unsafe{nrTextClusterSample(self.ptr(),id,index,out.as_mut_ptr(),8)}!=0{return Err("text cluster not found".into());}Ok(out)
    }
    /// Owned trail row: source identity bits, glyph, ordinal, XY Q16, alpha, hue, settled.
    pub fn textTrailSample(&self,id:u32,index:u32,trail:u32)->Result<[i32;8],String>{
        let mut out=[0;8];if unsafe{nrTextTrailSample(self.ptr(),id,index,trail,out.as_mut_ptr(),8)}!=0{return Err("text trail not found".into());}Ok(out)
    }
    pub fn textSample(&self,id:u32,index:u32)->Result<[i32;8],String>{
        let mut out=[0;8];if unsafe{nrTextSample(self.ptr(),id,index,out.as_mut_ptr(),8)}!=0{return Err("text run or index not found".into());}Ok(out)
    }
    /// UV and visibility use integer millionths. Returns local XYZ Q16, alpha, mask.
    pub fn windowSample(&self,id:u32,u:u32,v:u32,visibility:u32)->Result<[i32;5],String>{
        let mut out=[0;5];if unsafe{nrWindowSample(self.ptr(),id,u,v,visibility,out.as_mut_ptr(),5)}!=0{return Err("window sample bounds or unknown identity".into());}Ok(out)
    }
    /// OKLCh millionths/millidegrees to packed RGB; bounds errors are explicit.
    pub fn oklch(lightness:i32,chroma:i32,hue:i32)->Result<u32,String>{
        let value=unsafe{nrOklch(lightness,chroma,hue)};if value==u32::MAX{Err("color bounds".into())}else{Ok(value)}
    }
    /// Pure RGB blend plus independent alpha composition. Returns (packed RGB, alpha/65535).
    pub fn composite(base:u32,source:u32,baseAlpha:u32,sourceAlpha:u32,blend:u32,operator:u32,seed:u32)->Result<[u32;2],String>{
        let mut out=[0;2];if unsafe{nrComposite(base,source,baseAlpha,sourceAlpha,blend,operator,seed,out.as_mut_ptr())}<0{Err("composition bounds".into())}else{Ok(out)}
    }
    /// Pure composition: 0 sRGB, 1 linear sRGB, 2 OKLab, 3 OKLCh.
    pub fn compositeInSpace(base:u32,source:u32,baseAlpha:u32,sourceAlpha:u32,blend:u32,operator:u32,seed:u32,space:u32)->Result<[u32;2],String>{
        let mut out=[0;2];if unsafe{nrCompositeInSpace(base,source,baseAlpha,sourceAlpha,blend,operator,seed,space,out.as_mut_ptr())}<0{Err("composition bounds".into())}else{Ok(out)}
    }
}
impl Drop for NativeScene{fn drop(&mut self){unsafe{
    if let Some((memory,layout))=self.render_memory.take(){dealloc(memory.as_ptr(),layout)}
    if let Some((memory,layout))=self.prompt_memory.take(){dealloc(memory.as_ptr(),layout)}
    if let Some((memory,layout))=self.modal_memory.take(){dealloc(memory.as_ptr(),layout)}
    if let Some((memory,layout))=self.model_memory.take(){dealloc(memory.as_ptr(),layout)}
    dealloc(self.memory.as_ptr(),self.layout)
}}}
#[cfg(test)]mod tests{
 use super::*;
 #[test]fn ownershipAndPurity(){let mut s=NativeScene::new(7).unwrap();let snap=s.snapshot().unwrap();let f=s.render().unwrap();assert_eq!(snap,s.snapshot().unwrap());s.command(r#"{"op":"input","text":"Hi"}"#).unwrap();assert_ne!(f,s.render().unwrap());assert_eq!(f,f.clone());}
 #[test]fn invalidAtomic(){let mut s=NativeScene::new(3).unwrap();let before=s.snapshot().unwrap();assert!(s.command(r#"{"op":"camera","near":4,"far":1}"#).is_err());assert_eq!(before,s.snapshot().unwrap());}
 #[test]fn nestedWeatherAuthoringMatchesFlatEmitter(){
  let mut nested=NativeScene::new(9).unwrap();
  let mut flat=NativeScene::new(9).unwrap();
  nested.command(r#"{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":4,"effect":"weather/silver-squall","emission":{"rate":12,"runningTimeMs":1000},"birth":{"position":[0,10,0],"extent":[1,1,1]},"collision":{"enabled":false,"deposit":false}}"#).unwrap();
  flat.command(r#"{"op":"emitter","id":4,"effect":"weather/silver-squall","rate":12,"runningTimeMs":1000,"position":[0,10,0],"extent":[1,1,1],"collision":false,"deposit":false}"#).unwrap();
  assert_eq!(nested.snapshot().unwrap(),flat.snapshot().unwrap());
  nested.advanceTo(500_000).unwrap();flat.advanceTo(500_000).unwrap();
  assert_eq!(nested.snapshot().unwrap(),flat.snapshot().unwrap());
  assert_eq!(nested.render().unwrap().bytes,flat.render().unwrap().bytes);
 }
 #[test]fn snapshotRecovery(){let mut s=NativeScene::new(2).unwrap();s.command(r#"{"op":"input","text":"retained"}"#).unwrap();let snap=s.snapshot().unwrap();s.command(r#"{"op":"reset"}"#).unwrap();s.restore(&snap).unwrap();assert!(s.info().contains("retained"));let mut bad=snap;bad[40]^=1;assert!(s.restore(&bad).is_err());}
 #[test]fn eventIntentValueActionThroughCAbiAndSnapshot(){
  let mut s=NativeScene::new(2030).unwrap();
  s.command(r#"{"op":"define","path":"/enabled","value":1}"#).unwrap();
  s.command(r#"{"op":"define","path":"/out","value":0}"#).unwrap();
  s.command(r#"{"op":"trigger","id":1,"when":{"path":"/enabled","comparison":"equal","value":1},"event":"/task/approved","target":"/out","action":"set","valueFrom":"intentValue"}"#).unwrap();
  s.command(r#"{"op":"status","id":1,"area":0,"text":"Approve","durationMs":0,"actions":[{"id":1,"label":"Confirm","event":"/task/approved","value":7}]}"#).unwrap();
  s.command(r#"{"op":"notification-action","id":1,"actionId":1}"#).unwrap();
  let accepted=s.info();
  assert!(accepted.contains(r#""/out":7"#),"{accepted}");
  assert!(accepted.contains(r#""valueSource":"intentValue""#),"{accepted}");
  assert!(accepted.contains(r#""lastIntentSource":{"id":1,"event":"/task/approved""#),"{accepted}");
  let snapshot=s.snapshot().unwrap();
  let mut restored=NativeScene::new(9).unwrap();
  restored.restore(&snapshot).unwrap();
  let after=restored.info();
  assert!(after.contains(r#""/out":7"#),"{after}");
  assert!(after.contains(r#""lastIntentSource":{"id":1,"event":"/task/approved""#),"{after}");
 }
 #[test]fn colorEndpoints(){assert_eq!(NativeScene::oklch(0,0,0).unwrap(),0);assert_eq!(NativeScene::oklch(1000000,0,0).unwrap(),0xffffff);assert!(NativeScene::oklch(-1,0,0).is_err());}
}

/// Pure maximum-cardinality shortcut assignment; host explicitly reserves chords.
pub fn negotiate_shortcuts(actions:&[u32],candidates:&[[u32;3]],host:&[[u32;3]])->Result<Vec<[u32;4]>,String>{
 if actions.len()>64||candidates.len()>256||host.len()>256{return Err("Shortcut table capacity".into());}
 let mut out=vec![[0u32;4];actions.len()];
 let n=unsafe{nrNegotiateShortcuts(actions.as_ptr(),actions.len() as u32,candidates.as_ptr() as *const u32,candidates.len() as u32,host.as_ptr() as *const u32,host.len() as u32,out.as_mut_ptr() as *mut u32,actions.len() as u32)};
 if n<0{return Err("Invalid shortcut capabilities/preferences".into());}Ok(out)
}

/// Owned logical whole-grapheme run with an ISO15924 script tag.
#[derive(Debug,Clone,PartialEq,Eq)]
pub struct ScriptRun {pub start:u32,pub end:u32,pub script:String}
#[cfg(test)]mod prompt_presentation_test{use super::*;#[test]fn owned_prompt_layout(){let mut s=NativeScene::new(42).unwrap();for c in [r#"{"op":"resize","width":8,"height":18}"#,r#"{"op":"prompt","layout":"grapheme","mode":"grow","minRows":2}"#,r#"{"op":"draft","text":"Aé界Z","emitWeather":false}"#]{s.command(c).unwrap();}let b=s.snapshot().unwrap();let mut rows=s.prompt_layout().unwrap();assert_eq!(rows.len(),4);assert_eq!(rows[1][1],3.0);assert_eq!(rows[2][4],2.0);rows[0][0]=99.0;assert_eq!(s.prompt_layout().unwrap()[0][0],0.0);assert_eq!(b,s.snapshot().unwrap());}}
