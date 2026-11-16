use nocturne_native::NativeScene;
#[test]
fn native_expression_and_atomic_fault(){
 let mut s=NativeScene::new(42).unwrap();
 for command in [r#"{"op":"define","path":"/scale","value":2}"#,r#"{"op":"define","path":"/out","value":0}"#,r#"{"op":"set","path":"/out","expression":{"add":[{"multiply":[{"path":"/scale"},4]},3]}}"#]{s.command(command).unwrap();}
 assert!(s.info().contains("\"/out\":11"));let saved=s.snapshot().unwrap();
 assert!(s.command(r#"{"op":"set","path":"/out","expression":{"divide":[1,0]}}"#).is_err());assert_eq!(s.snapshot().unwrap(),saved);
}
