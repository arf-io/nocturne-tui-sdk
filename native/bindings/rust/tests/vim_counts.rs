use nocturne_native::NativeScene;
#[test]
fn counted_delete(){let mut s=NativeScene::new(17).unwrap();for c in [r#"{"op":"prompt","mode":"vim-inline"}"#,r#"{"op":"draft","text":"abcdef","caret":0,"emitWeather":false}"#,r#"{"op":"key","key":"Escape"}"#,r#"{"op":"key","key":"3"}"#,r#"{"op":"key","key":"x"}"#]{s.command(c).unwrap();}assert_eq!(s.text_run_source(0,0).unwrap(),"def");}

#[test]
fn delete_word_operator(){let mut s=NativeScene::new(17).unwrap();for c in [r#"{"op":"prompt","mode":"vim-inline"}"#,r#"{"op":"draft","text":"one two","caret":0,"emitWeather":false}"#,r#"{"op":"key","key":"Escape"}"#,r#"{"op":"key","key":"d"}"#,r#"{"op":"key","key":"w"}"#]{s.command(c).unwrap();}assert_eq!(s.text_run_source(0,0).unwrap(),"two");}

#[test]
fn register_put(){let mut s=NativeScene::new(17).unwrap();for c in [r#"{"op":"prompt","mode":"vim-inline"}"#,r#"{"op":"draft","text":"one two","caret":0,"emitWeather":false}"#,r#"{"op":"key","key":"Escape"}"#,r#"{"op":"key","key":"d"}"#,r#"{"op":"key","key":"w"}"#,r#"{"op":"key","key":"P"}"#]{s.command(c).unwrap();}assert_eq!(s.text_run_source(0,0).unwrap(),"one two");}
#[test]
fn named_register_put(){let mut s=NativeScene::new(17).unwrap();for c in [r#"{"op":"prompt","mode":"vim-inline"}"#,r#"{"op":"draft","text":"saved","caret":0,"emitWeather":false}"#,r#"{"op":"key","key":"Escape"}"#,r#"{"op":"key","key":"\""}"#,r#"{"op":"key","key":"a"}"#,r#"{"op":"key","key":"y"}"#,r#"{"op":"key","key":"w"}"#,r#"{"op":"draft","text":"Z","caret":0,"emitWeather":false}"#,r#"{"op":"key","key":"Escape"}"#,r#"{"op":"key","key":"\""}"#,r#"{"op":"key","key":"a"}"#,r#"{"op":"key","key":"P"}"#]{s.command(c).unwrap();}assert_eq!(s.text_run_source(0,0).unwrap(),"savedZ");}

#[test]
fn native_redo(){let mut s=NativeScene::new(17).unwrap();for c in [r#"{"op":"prompt","mode":"vim-inline"}"#,r#"{"op":"draft","text":"abcdef","caret":0,"emitWeather":false}"#,r#"{"op":"key","key":"Escape"}"#,r#"{"op":"key","key":"x"}"#,r#"{"op":"key","key":"u"}"#,r#"{"op":"key","key":"r","ctrl":true}"#]{s.command(c).unwrap();}assert_eq!(s.text_run_source(0,0).unwrap(),"bcdef");}
