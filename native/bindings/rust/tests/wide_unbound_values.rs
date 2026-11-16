#[path="support/current_writer.rs"] mod current_writer;
use current_writer::assert_current_snapshot;
use nocturne_native::NativeScene;
#[test]
fn wide_values_keep_target_validation_and_exact_restore(){
 let mut s=NativeScene::new(42).unwrap();
 for command in [r#"{"op":"define","path":"/source","value":1000000000000,"readonly":true}"#,
  r#"{"op":"define","path":"/out","value":0}"#,
  r#"{"op":"set","path":"/out","expression":{"negate":{"path":"/source"}}}"#]{s.command(command).unwrap();}
 assert!(s.info().contains("\"/out\":-1000000000000"));
 for command in [r#"{"op":"environment","background":0}"#,r#"{"op":"set","path":"/out","value":16777215}"#,
  r#"{"op":"bind","path":"/out","binding":{"family":"environment","id":0,"field":"background"}}"#,
  r#"{"op":"bind","path":"/out","binding":null}"#]{s.command(command).unwrap();}
 let before=s.snapshot().unwrap();assert_current_snapshot(&mut s,&before);
 for command in [r#"{"op":"set","path":"/out","value":1000000000001}"#,r#"{"op":"set","path":"/source","value":0}"#,
  r#"{"op":"bind","path":"/out","binding":{"family":"accessibility","id":0,"field":"screenReader"}}"#]{assert!(s.command(command).is_err());assert_eq!(s.snapshot().unwrap(),before);}
 s.restore(&before).unwrap();assert_eq!(s.snapshot().unwrap(),before);
}
