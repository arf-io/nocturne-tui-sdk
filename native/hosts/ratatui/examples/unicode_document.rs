//! Runnable native Unicode document viewport. Ctrl-Q exits.
mod support;
use nocturne_native::NativeScene;
use nocturne_ratatui::{UnicodeDocument,SceneCells,shortcuts::ShortcutProfile,text_anchor::RetainedTextAnchor};
use ratatui::{backend::CrosstermBackend,Terminal};
use ratatui::crossterm::{execute,event::{self,Event,KeyCode,KeyModifiers,KeyEventKind,MouseEventKind,MouseButton,EnableMouseCapture,DisableMouseCapture,EnableBracketedPaste,DisableBracketedPaste,EnableFocusChange,DisableFocusChange},terminal::{enable_raw_mode,disable_raw_mode,EnterAlternateScreen,LeaveAlternateScreen}};
use std::{io,env};
fn document_owned(scene:&mut NativeScene)->Result<bool,Box<dyn std::error::Error>> {
 let info:serde_json::Value=serde_json::from_str(&scene.infoComplete()?)?;
 Ok(info["inputOwner"].as_str()==Some("prompt"))
}
struct Guard;
impl Drop for Guard {fn drop(&mut self){let _=execute!(io::stdout(),DisableMouseCapture,DisableBracketedPaste,DisableFocusChange,LeaveAlternateScreen);let _=disable_raw_mode();}}
fn main()->Result<(),Box<dyn std::error::Error>> {
 let mut scene=NativeScene::new(2030)?;let mut info_path=None;let mut reservations=Vec::new();
 for arg in env::args().skip(1){
  if let Some(label)=arg.strip_prefix("--reserve-shortcut="){reservations.push(label.to_string());}
  if let Some(text)=arg.strip_prefix("--document-text="){scene.command(&support::pasteCommand(text))?;}
  if let Some(path)=arg.strip_prefix("--info-on-exit="){info_path=Some(path.to_string());}
 }
 let shortcuts=ShortcutProfile::new(&reservations)?;
 enable_raw_mode()?;let _guard=Guard;
 execute!(io::stdout(),EnterAlternateScreen,EnableMouseCapture,EnableBracketedPaste,EnableFocusChange)?;
 let mut terminal=Terminal::new(CrosstermBackend::new(io::stdout()))?;
 let mut view=UnicodeDocument::new();let mut drag=None;let mut viewport=None;
 loop {
  let terminal_area=terminal.size()?;
  let mut area=ratatui::layout::Rect::new(0,0,terminal_area.width,terminal_area.height);if area.height>1{area.height-=1;}
  if let Some(cmd)=support::resizeCommand(area.width,area.height,&mut viewport){scene.command(&cmd)?;}
  let owned=document_owned(&mut scene)?;if !owned{drag=None;}
  let metadata:serde_json::Value=serde_json::from_str(&scene.infoComplete()?)?;
  let caret=metadata["prompt"]["caret"].as_u64().ok_or("missing native caret")? as u32;
  let anchor=metadata["prompt"]["anchor"].as_i64().unwrap_or(-1);
  let selection=if anchor>=0{Some([anchor as u32,caret])}else{None};
  if owned {
  view.presentation(&scene,u32::from(area.width),u32::from(area.height),selection)?;
  view.follow_caret(&scene,caret)?;
  let frame=view.presentation(&scene,u32::from(area.width),u32::from(area.height),selection)?;
  terminal.draw(|f|{let a=area;f.render_widget(ratatui::widgets::Paragraph::new("NOCTURNE Unicode document"),ratatui::layout::Rect::new(a.x,a.y,a.width,1));f.render_widget(&frame,a);if terminal_area.height>1{f.render_widget(ratatui::widgets::Paragraph::new(shortcuts.hints.as_str()),ratatui::layout::Rect::new(0,area.height,area.width,1));}})?;
  }else{let frame=scene.render()?;terminal.draw(|f|{f.render_widget(SceneCells{frame:&frame},area);if terminal_area.height>1{f.render_widget(ratatui::widgets::Paragraph::new(shortcuts.hints.as_str()),ratatui::layout::Rect::new(0,area.height,area.width,1));}})?;}
  match event::read()? {
   Event::FocusLost=>{drag=None;scene.command(r#"{"op":"pointer","phase":"cancel","x":-1,"y":-1}"#)?;},
   Event::Key(k) if k.kind==KeyEventKind::Release=>{},
   Event::Key(k) if k.code==KeyCode::Char('c') && k.modifiers.contains(KeyModifiers::CONTROL)=>break,
   Event::Key(k)=>{
    match shortcuts.action(k){Some(1)=>break,Some(2)=>{scene.command(&support::keyCommand("F1",false,false,false))?;continue;},Some(3)=>{scene.command(&support::keyCommand("F6",false,false,false))?;continue;},_=>{}}
    if shortcuts.managed(k){continue;}

    let name=match k.code {KeyCode::Left=>Some("ArrowLeft"),KeyCode::Right=>Some("ArrowRight"),KeyCode::Up=>Some("ArrowUp"),KeyCode::Down=>Some("ArrowDown"),KeyCode::Home=>Some("Home"),KeyCode::End=>Some("End"),KeyCode::PageUp=>Some("PageUp"),KeyCode::PageDown=>Some("PageDown"),KeyCode::Backspace=>Some("Backspace"),KeyCode::Delete=>Some("Delete"),KeyCode::Enter=>Some("Enter"),KeyCode::Esc=>Some("Escape"),_=>None};
    if let Some(name)=name{
     if owned && !k.modifiers.contains(KeyModifiers::CONTROL) && matches!(name,"ArrowLeft"|"ArrowRight"|"ArrowUp"|"ArrowDown"|"Home"|"End"|"PageUp"|"PageDown") {
      let offset=view.move_offset(&scene,caret,name)?;
      let start=if k.modifiers.contains(KeyModifiers::SHIFT){if anchor>=0{anchor as u32}else{caret}}else{offset};
      scene.command(&format!("{{\"op\":\"select\",\"anchor\":{start},\"caret\":{offset},\"unit\":\"grapheme\"}}"))?;
     }else{scene.command(&support::keyCommand(name,k.modifiers.contains(KeyModifiers::CONTROL),k.modifiers.contains(KeyModifiers::SHIFT),false))?;}}
    else if let KeyCode::Char(c)=k.code{if !k.modifiers.contains(KeyModifiers::CONTROL){scene.command(&support::keyCommand(&c.to_string(),false,k.modifiers.contains(KeyModifiers::SHIFT),k.modifiers.contains(KeyModifiers::ALT)))?;}}
   }
   Event::Paste(text)=>{scene.command(&support::pasteCommand(&text))?;}
   Event::Mouse(m) if m.row==0||m.row>=area.height=>{if matches!(m.kind,MouseEventKind::Up(_)){drag=None;}},
   Event::Mouse(m) if !owned=>{
    let phase=match m.kind{MouseEventKind::Down(_)=>"down",MouseEventKind::Up(_)=>"up",_=>"move"};
    match m.kind {
     MouseEventKind::ScrollUp|MouseEventKind::ScrollDown=>{let delta=if matches!(m.kind,MouseEventKind::ScrollUp){1}else{-1};scene.command(&format!("{{\"op\":\"wheel\",\"x\":{},\"y\":{},\"delta\":{delta}}}",m.column,m.row))?;},
     _=>{scene.command(&format!("{{\"op\":\"pointer\",\"phase\":\"{phase}\",\"x\":{},\"y\":{},\"button\":0}}",m.column,m.row))?;}
    }
   },
   Event::Mouse(m)=>match m.kind {
    MouseEventKind::ScrollDown=>view.scroll_by(3),MouseEventKind::ScrollUp=>view.scroll_by(-3),
    MouseEventKind::Down(MouseButton::Left)|MouseEventKind::Drag(MouseButton::Left)|MouseEventKind::Up(MouseButton::Left) if m.row>0 && m.row<area.height=>{
     let offset=view.hit(&scene,u32::from(m.column),u32::from(m.row))?;
     if matches!(m.kind,MouseEventKind::Down(_)){drag=Some(RetainedTextAnchor::capture(&scene,0,0,if m.modifiers.contains(KeyModifiers::SHIFT){if anchor>=0{anchor as u32}else{caret}}else{offset})?);view.reset_column();}
     if let Some(reference)=&drag{if let Some(start)=reference.resolve(&scene)?{scene.command(&format!("{{\"op\":\"select\",\"anchor\":{start},\"caret\":{offset},\"unit\":\"grapheme\"}}"))?;}else{drag=None;}}
     if matches!(m.kind,MouseEventKind::Up(_)){drag=None;}
    },_=>{}
   },_=>{}
  }
 }
 if let Some(path)=info_path{std::fs::write(path,scene.infoComplete()?)?;}
 Ok(())
}

#[cfg(test)]
mod ownership_tests {
 use super::*;
 #[test]
 fn modal_and_reader_ownership_yield_the_document() {
  let mut scene=NativeScene::new(2030).unwrap();
  assert!(document_owned(&mut scene).unwrap());
  scene.command(r#"{"op":"key","key":"F1"}"#).unwrap();
  assert!(!document_owned(&mut scene).unwrap());
  let before=scene.text_run_source(0,0).unwrap();
  scene.command(&support::keyCommand("ArrowRight",false,false,false)).unwrap();
  assert_eq!(before,scene.text_run_source(0,0).unwrap());
  scene.command(r#"{"op":"key","key":"F1"}"#).unwrap();
  assert!(document_owned(&mut scene).unwrap());
  scene.command(r#"{"op":"window","id":1,"title":"Read","text":"Body"}"#).unwrap();
  scene.command(r#"{"op":"key","key":"F6"}"#).unwrap();
  assert!(!document_owned(&mut scene).unwrap());
 }
}
