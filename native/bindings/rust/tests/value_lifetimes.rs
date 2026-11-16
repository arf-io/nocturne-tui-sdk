use nocturne_native::NativeScene;
#[test]
fn referenced_value_rejection_and_explicit_teardown(){
 let mut s=NativeScene::new(42).unwrap();
 for command in [r#"{"op":"define","path":"/source","value":0}"#,r#"{"op":"define","path":"/target","value":0}"#,r#"{"op":"trigger","id":1,"source":"/source","target":"/target"}"#]{s.command(command).unwrap();}
 let saved=s.snapshot().unwrap();assert!(s.command(r#"{"op":"remove-value","path":"/source"}"#).is_err());assert_eq!(s.snapshot().unwrap(),saved);
 for command in [r#"{"op":"remove-trigger","id":1}"#,r#"{"op":"remove-value","path":"/source"}"#,r#"{"op":"define","path":"/replacement","value":9}"#]{s.command(command).unwrap();}
 let info=s.info();assert!(!info.contains("\"/source\""));assert!(info.contains("\"triggers\":[]"));assert!(info.contains("\"/replacement\":9"));
}
