//! Scalar-hex conformance transport using only std; segmentation stays native.
use std::io::{self,BufRead};
use nocturne_native::NativeScene;
fn main()->Result<(),String>{
 let scene=NativeScene::new(2030)?;
 for (index,line) in io::stdin().lock().lines().enumerate(){
  let line=line.map_err(|e|e.to_string())?;let mut text=String::new();
  for word in line.split_ascii_whitespace(){
   let scalar=u32::from_str_radix(word,16).map_err(|e|e.to_string())?;
   text.push(char::from_u32(scalar).ok_or("Invalid Unicode scalar")?);
  }
  let mut layouts=Vec::new();for columns in [1,3,8]{for policy in [1,2]{layouts.push(scene.grapheme_layout(&text,columns,policy)?);}}
  println!("{{\"index\":{index},\"boundaries\":{:?},\"widths1\":{:?},\"widths2\":{:?},\"layouts\":{:?}}}",scene.grapheme_boundaries(&text)?,scene.grapheme_widths(&text,1)?,scene.grapheme_widths(&text,2)?,layouts);
 }Ok(())
}
