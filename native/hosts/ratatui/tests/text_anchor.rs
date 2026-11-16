use nocturne_native::NativeScene;
use nocturne_ratatui::text_anchor::RetainedTextAnchor;
#[test]
fn anchors_follow_clusters_and_cancel_when_retired(){
 let mut s=NativeScene::new(7).unwrap();s.command(r#"{"op":"draft","text":"Ae\u0301Z","emitWeather":false}"#).unwrap();
 let anchor=RetainedTextAnchor::capture(&s,0,0,2).unwrap();assert_eq!(anchor.resolve(&s).unwrap(),Some(1));
 s.command(r#"{"op":"draft","text":"XAe\u0301Z","emitWeather":false}"#).unwrap();let before=s.snapshot().unwrap();assert_eq!(anchor.resolve(&s).unwrap(),Some(2));assert_eq!(s.snapshot().unwrap(),before);
 s.command(r#"{"op":"draft","text":"XAe\u0300Z","emitWeather":false}"#).unwrap();let before=s.snapshot().unwrap();assert_eq!(anchor.resolve(&s).unwrap(),None);assert_eq!(s.snapshot().unwrap(),before);
}
#[test]
fn end_and_empty_anchors_preserve_boundary_semantics(){
 let mut s=NativeScene::new(7).unwrap();let empty=RetainedTextAnchor::capture(&s,0,0,0).unwrap();assert_eq!(empty.resolve(&s).unwrap(),Some(0));
 s.command(r#"{"op":"draft","text":"ABC","emitWeather":false}"#).unwrap();assert_eq!(empty.resolve(&s).unwrap(),None);let end=RetainedTextAnchor::capture(&s,0,0,3).unwrap();
 s.command(r#"{"op":"draft","text":"XABC","emitWeather":false}"#).unwrap();assert_eq!(end.resolve(&s).unwrap(),Some(4));assert!(RetainedTextAnchor::capture(&s,0,0,5).is_err());
}
