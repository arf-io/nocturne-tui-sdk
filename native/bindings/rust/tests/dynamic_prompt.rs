use nocturne_native::NativeScene;

#[test]
fn dynamic_prompt_growth_and_restore() {
 let mut s=NativeScene::new(2030).unwrap();
 s.command(r#"{"op":"prompt","presentation":"framed"}"#).unwrap();
 let mut text=String::new();
 for n in [35001,35003,70007] {
  let part="🌧".repeat(n);
  s.command(&format!(r#"{{"op":"input","text":"{}"}}"#,part)).unwrap();
  text.push_str(&part);
  assert_eq!(s.text_run_source(0,0).unwrap(),text);
 }
 let count=text.chars().count();
 s.command(&format!(r#"{{"op":"select","anchor":0,"caret":{count}}}"#)).unwrap();
 assert_eq!(s.selected_text().unwrap(),Some(text.clone()));
 assert_eq!(s.text_run_clusters(0,0).unwrap().len(),count);
 assert_eq!(s.text_run_layout(0,0,80,1).unwrap().len(),count);
 s.render().unwrap();
 let saved=s.snapshot().unwrap();
 let mut restored=NativeScene::new(99).unwrap();restored.restore(&saved).unwrap();
 assert_eq!(restored.text_run_source(0,0).unwrap(),text);
 let before=s.snapshot().unwrap();
 assert!(s.command(r#"{"op":"select","anchor":0,"caret":-1}"#).is_err());
 assert_eq!(s.snapshot().unwrap(),before);
}

#[test]
fn dynamic_prompt_large_utf8_command() {
 let mut s=NativeScene::new(2030).unwrap();
 s.command(r#"{"op":"prompt","presentation":"framed"}"#).unwrap();
 let text="🌧".repeat(270001);
 s.command(&format!(r#"{{"op":"draft","text":"{}","emitWeather":false}}"#,text)).unwrap();
 assert_eq!(s.text_run_source(0,0).unwrap(),text);
}
