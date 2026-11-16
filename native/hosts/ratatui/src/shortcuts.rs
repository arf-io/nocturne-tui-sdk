//! Host-owned capabilities for the runnable Ratatui Unicode document example.
use ratatui::crossterm::event::{KeyCode,KeyEvent,KeyModifiers};
use nocturne_native::negotiate_shortcuts;
const CHORDS:[(&str,u32,u32);6]=[("Ctrl+q",'q' as u32,2),("Alt+q",'q' as u32,4),("F1",0x110001,0),("F7",0x110007,0),("F6",0x110006,0),("F8",0x110008,0)];
pub struct ShortcutProfile {pub rows:Vec<[u32;4]>,pub hints:String}
impl ShortcutProfile {
 pub fn new(reserved:&[String])->Result<Self,String>{
  if reserved.iter().any(|s|!CHORDS.iter().any(|c|c.0==s)){return Err("Reservation outside managed Ratatui shortcuts".into());}
  let host:Vec<[u32;3]>=CHORDS.iter().map(|&(name,key,modifiers)|[key,modifiers,u32::from(reserved.iter().any(|s|s==name))]).collect();
  let candidates=[[1,'q' as u32,2],[1,'q' as u32,4],[2,0x110001,0],[2,0x110007,0],[3,0x110006,0],[3,0x110008,0]];
  let rows=negotiate_shortcuts(&[1,2,3],&candidates,&host)?;
  let hints=rows.iter().map(|row|{
   let name=if row[3]==0{"unassigned"}else{CHORDS.iter().find(|c|c.1==row[1]&&c.2==row[2]).map(|c|c.0).unwrap_or("unassigned")};
   format!("{}: {name}",["Quit","Help","Reader"][(row[0]-1) as usize])
  }).collect::<Vec<_>>().join(" | ");Ok(Self{rows,hints})
 }
 fn normalized(event:KeyEvent)->Option<(u32,u32)>{
  let key=match event.code{KeyCode::Char(c)=>c as u32,KeyCode::F(n) if (1..=12).contains(&n)=>0x110000+u32::from(n),_=>return None};
  let known=KeyModifiers::SHIFT|KeyModifiers::CONTROL|KeyModifiers::ALT|KeyModifiers::SUPER;
  if !(event.modifiers & !known).is_empty(){return None;}
  let m=u32::from(event.modifiers.contains(KeyModifiers::SHIFT))|u32::from(event.modifiers.contains(KeyModifiers::CONTROL))*2|u32::from(event.modifiers.contains(KeyModifiers::ALT))*4|u32::from(event.modifiers.contains(KeyModifiers::SUPER))*8;
  Some((key,m))
 }
 pub fn action(&self,event:KeyEvent)->Option<u32>{
  let (k,m)=Self::normalized(event)?;self.rows.iter().find(|r|r[3]!=0&&r[1]==k&&r[2]==m).map(|r|r[0])
 }
 pub fn managed(&self,event:KeyEvent)->bool{
  Self::normalized(event).is_some_and(|(k,m)|CHORDS.iter().any(|c|c.1==k&&c.2==m))
 }
}
