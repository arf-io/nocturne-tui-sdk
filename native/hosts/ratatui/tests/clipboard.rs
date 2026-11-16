#[path="../examples/support/mod.rs"] mod support;
use nocturne_native::NativeScene;
#[test]
fn selected_clipboard_roundtrip()->Result<(),String>{
 let mut s=NativeScene::new(2030)?;s.command(r#"{"op":"draft","text":"Aé日本Z","emitWeather":false}"#)?;s.command(r#"{"op":"select","anchor":1,"caret":5}"#)?;
 let mut buffer=String::new();for action in ["copy","cut","paste"]{if let Some(c)=support::clipboardCommand(&s,&mut buffer,action)?{s.command(&c)?;}}
 assert_eq!(buffer,"é日本");assert!(s.info().contains("Aé日本Z"));s.command(r#"{"op":"key","key":"F1"}"#)?;let before=s.snapshot()?;
 assert!(support::clipboardCommand(&s,&mut buffer,"cut")?.is_none());assert_eq!(s.snapshot()?,before);Ok(())
}
