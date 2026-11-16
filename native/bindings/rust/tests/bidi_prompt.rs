use nocturne_native::NativeScene;

#[test]
fn bidi_prompt_owned_consumer() {
 let mut s=NativeScene::new(42).unwrap();
 s.command(r#"{"op":"prompt","layout":"bidi","direction":"auto","mode":"grow"}"#).unwrap();
 s.command(r#"{"op":"draft","text":"א́ב","emitWeather":false}"#).unwrap();
 let before=s.snapshot().unwrap();let mut rows=s.prompt_visual_layout().unwrap();
 assert_eq!(rows.len(),2);assert_eq!(rows[0][0],2.0);
 assert_eq!(rows[1][0..2],[0.0,2.0]);assert_eq!(rows[1][8],1.0);
 rows[0][0]=999.0;assert_eq!(s.prompt_visual_layout().unwrap()[0][0],2.0);
 assert_eq!(s.snapshot().unwrap(),before);
 assert!(s.command(r#"{"op":"prompt","direction":"invalid"}"#).is_err());
 assert_eq!(s.snapshot().unwrap(),before);
}
