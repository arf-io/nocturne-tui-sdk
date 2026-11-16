use super::*;
extern "C" {
 fn nrModelMemorySize(ctx:*const NrContext)->u64;
 fn nrModelMemoryCapacity(ctx:*const NrContext)->u64;
 fn nrSetModelMemory(ctx:*mut NrContext,memory:*mut c_void,capacity:u64)->i32;
 fn nrModelSet(ctx:*mut NrContext,records:*const c_void,count:u32)->i32;
 fn nrModelTriangleCount(ctx:*const NrContext)->u32;
 fn nrModelCopy(ctx:*const NrContext,records:*mut c_void,capacity:u32)->i32;
}
impl NativeScene{
 pub(crate) fn ensure_model_memory(&mut self)->Result<(),String>{
  let required=unsafe{nrModelMemorySize(self.ptr())};
  if required<=unsafe{nrModelMemoryCapacity(self.ptr())}{return Err("model storage request made no progress".into());}
  let size=usize::try_from(required).map_err(|_|"model exceeds address space")?;
  let layout=Layout::from_size_align(size,8).map_err(|e|e.to_string())?;
  let memory=NonNull::new(unsafe{alloc_zeroed(layout)}).ok_or("model allocation failed")?;
  if unsafe{nrSetModelMemory(self.ptr(),memory.as_ptr().cast(),required)}!=0{unsafe{dealloc(memory.as_ptr(),layout)};return Err("model storage rejected".into());}
  if let Some((old,old_layout))=self.model_memory.replace((memory,layout)){unsafe{dealloc(old.as_ptr(),old_layout)}}
  Ok(())
 }
 /// Atomically upload original Q8/RGB geometry, separate from JSON transactions.
 pub fn set_model_records(&mut self,bytes:&[u8])->Result<(),String>{
  if bytes.len()%40!=0||u32::try_from(bytes.len()).is_err(){return Err("model record length".into());}
  // Vec<u8> does not promise C record alignment. Own aligned words at this ABI boundary.
  let mut words=Vec::<u32>::new();words.try_reserve_exact(bytes.len()/4).map_err(|e|e.to_string())?;
  for row in bytes.chunks_exact(4){words.push(u32::from_le_bytes(row.try_into().unwrap()));}
  loop{let result=unsafe{nrModelSet(self.ptr(),words.as_ptr().cast(),(bytes.len()/40) as u32)};if result==0{return Ok(());}
   let message=unsafe{CStr::from_ptr(nrError(self.ptr()))};if message.to_bytes()!=b"Model storage required"{return Err(message.to_string_lossy().into_owned());}self.ensure_model_memory()?;
  }
 }
 /// Return owned little-endian model records, with no borrowed arena pointers.
 pub fn model_records(&self)->Result<Vec<u8>,String>{
  let count=unsafe{nrModelTriangleCount(self.ptr())};let words_count=(count as usize).checked_mul(10).ok_or("model exceeds address space")?;
  let mut words=Vec::<u32>::new();words.try_reserve_exact(words_count).map_err(|e|e.to_string())?;words.resize(words_count,0);
  if unsafe{nrModelCopy(self.ptr(),words.as_mut_ptr().cast(),count)}!=count as i32{return Err("model copy rejected".into());}
  let mut bytes=Vec::new();bytes.try_reserve_exact(words_count*4).map_err(|e|e.to_string())?;for word in words{bytes.extend_from_slice(&word.to_le_bytes());}Ok(bytes)
 }
}
