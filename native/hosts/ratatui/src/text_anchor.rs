//! Persistent whole-cluster input references. Clear references before native reset.
use nocturne_native::NativeScene;
#[derive(Clone,Debug)]
pub struct RetainedTextAnchor {kind:u32,id:u32,identity:u32,generation:u32,end:bool,source:String}
impl RetainedTextAnchor {
 pub fn capture(scene:&NativeScene,kind:u32,id:u32,offset:u32)->Result<Self,String>{
  let source=scene.text_run_source(kind,id)?;let chars:Vec<char>=source.chars().collect();
  if offset as usize>chars.len(){return Err("Text anchor exceeds source".into());}
  let boundary=scene.document_boundaries(&source)?.into_iter().filter(|&b|b<=offset).last().unwrap_or(0);
  let rows=scene.text_run_clusters(kind,id)?;
  let Some(row)=rows.iter().find(|r|r[1]==boundary).or_else(||rows.last()) else{return Ok(Self{kind,id,identity:0,generation:0,end:false,source:String::new()});};
  Ok(Self{kind,id,identity:row[0],generation:row[3],end:row[1]!=boundary,source:chars[row[1] as usize..row[2] as usize].iter().collect()})
 }
 pub fn resolve(&self,scene:&NativeScene)->Result<Option<u32>,String>{
  let source=match scene.text_run_source(self.kind,self.id){Ok(s)=>s,Err(_)=>return Ok(None)};
  if self.identity==0{return Ok(if source.is_empty(){Some(0)}else{None});}
  let chars:Vec<char>=source.chars().collect();
  for row in scene.text_run_clusters(self.kind,self.id)?{
   if row[0]==self.identity&&row[3]==self.generation&&chars[row[1] as usize..row[2] as usize].iter().collect::<String>()==self.source{return Ok(Some(if self.end{row[2]}else{row[1]}));}
  }Ok(None)
 }
}
