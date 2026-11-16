use nocturne_native::NativeScene;
#[test]
fn owned_electrical_geometry(){
 let mut s=NativeScene::new(42).unwrap();
 s.command(r#"{"op":"electrical-arc","id":7,"points":[{"position":[0,0,0],"parent":-1},{"position":[3,0,0],"parent":0}],"speed":10,"holdMs":200,"fadeMs":300,"jitter":0,"flicker":0}"#).unwrap();
 s.advanceTo(200000).unwrap();let before=s.snapshot().unwrap();let mut info=s.infoComplete().unwrap();
 assert!(info.contains(r#""phase":"leader""#));
 let tail=info.split(r#""segments":[["#).nth(1).unwrap();let row:Vec<f64>=tail.split(']').next().unwrap().split(',').map(|x|x.parse().unwrap()).collect();
 assert_eq!(row,vec![0.0,0.0,0.0,2.0,0.0,0.0,1.0]);info.clear();assert!(s.infoComplete().unwrap().contains("electricalArcs"));assert_eq!(s.snapshot().unwrap(),before);
}
