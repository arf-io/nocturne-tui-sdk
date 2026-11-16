use super::*;
extern "C" {fn nrSourceStageOklch(lightness:i32,chroma:i32,hue:i32)->u32;fn nrModalMemorySize(ctx:*const NrContext)->u64;fn nrModalMemoryCapacity(ctx:*const NrContext)->u64;fn nrSetModalMemory(ctx:*mut NrContext,memory:*mut c_void,capacity:u64)->i32;}
impl NativeScene{
 pub(crate) fn ensure_modal_memory(&mut self)->Result<(),String>{
  let required=unsafe{nrModalMemorySize(self.ptr())};
  if required<=unsafe{nrModalMemoryCapacity(self.ptr())}{return Err("modal storage request made no progress".into());}
  let size=usize::try_from(required).map_err(|_|"modal exceeds address space")?;
  let layout=Layout::from_size_align(size,8).map_err(|e|e.to_string())?;
  let memory=NonNull::new(unsafe{alloc_zeroed(layout)}).ok_or("modal allocation failed")?;
  if unsafe{nrSetModalMemory(self.ptr(),memory.as_ptr().cast(),required)}!=0{unsafe{dealloc(memory.as_ptr(),layout)};return Err("modal storage rejected".into());}
  if let Some((old,old_layout))=self.modal_memory.replace((memory,layout)){unsafe{dealloc(old.as_ptr(),old_layout)}}
  Ok(())
 }
}

impl NativeScene{pub fn source_stage_oklch(&self,l:i32,c:i32,h:i32)->Result<u32,String>{if !(0..=1000).contains(&l)||!(0..=4000).contains(&c){return Err("original source color domain".into())}Ok(unsafe{nrSourceStageOklch(l,c,h)})}}
