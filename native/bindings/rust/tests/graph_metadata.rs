use nocturne_native::NativeScene;
#[test]
fn graph_metadata_owned_readback(){
 let mut s=NativeScene::new(42).unwrap();
 for c in [r#"{"op":"node","id":1,"pinned":true,"position":[1,2,3]}"#,r#"{"op":"node","id":2}"#,r#"{"op":"edge","from":1,"to":2,"kind":"depends"}"#]{s.command(c).unwrap();}
 let before=s.snapshot().unwrap();let mut info=s.infoComplete().unwrap();
 assert!(info.contains(r#""layoutMode":"layered""#));assert!(info.contains(r#""edges":[{"from":1,"to":2,"kind":"depends"}]"#));
 assert!(info.contains(r#""pinned":true"#));
 let tail=info.split(r#""targetPosition":["#).nth(1).unwrap();
 let target:Vec<f64>=tail.split(']').next().unwrap().split(',').map(|v|v.trim().parse().unwrap()).collect();
 assert_eq!(target,vec![1.0,2.0,3.0]);
 info.clear();let again=s.infoComplete().unwrap();assert!(again.contains("depends"));assert_eq!(before,s.snapshot().unwrap());
}
