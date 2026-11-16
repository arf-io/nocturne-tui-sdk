use nocturne_native::NativeScene;
#[test]
fn ribbon_matches_authored_geometry(){
 let mut a=NativeScene::new(17).unwrap();let mut b=NativeScene::new(17).unwrap();
 a.command(r#"{"op":"ribbon","points":[[0,0,0],[4,0,0]],"width":2}"#).unwrap();
 b.command(r#"{"op":"mesh","triangles":[{"a":[0,0,-1],"b":[0,0,1],"c":[4,0,-1]},{"a":[0,0,1],"b":[4,0,1],"c":[4,0,-1]}]}"#).unwrap();
 assert_eq!(a.snapshot().unwrap(),b.snapshot().unwrap());
}

#[test]
fn path_arc_length(){let s=NativeScene::new(17).unwrap();assert_eq!(s.path_sample(&[[0.0,0.0,0.0],[3.0,0.0,0.0],[3.0,4.0,0.0]],5.0,false,0).unwrap(),[3.0,2.0,0.0,0.0,1.0,0.0,7.0,5.0]);}

#[test]
fn retained_camera_travel(){let mut s=NativeScene::new(17).unwrap();s.command(r#"{"op":"path-travel","id":1,"target":{"family":"camera","id":0},"points":[[0,0,0],[4,0,0]],"speed":2}"#).unwrap();s.advanceTo(1000000).unwrap();assert!(s.info().contains("\"camera\":{\"position\":[2.000000,0.000000,0.000000]"));}
