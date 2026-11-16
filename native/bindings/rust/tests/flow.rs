use nocturne_native::NativeScene;
#[test]
fn native_flow_delays(){
 let mut s=NativeScene::new(17).unwrap();
 s.command(r#"{"op":"flow","id":1,"flux":2,"stages":[{"name":"channel","delayUs":500000},{"name":"sheet","delayUs":250000}]}"#).unwrap();
 s.advanceTo(1_000_000).unwrap();
 assert!(s.info().contains("\"deliveredVolume\":0.500000"));
 s.command(r#"{"op":"flow-rate","id":1,"flux":0}"#).unwrap();
 s.advanceTo(2_000_000).unwrap();
 assert!(s.info().contains("\"storedVolume\":0.000000"));
}
