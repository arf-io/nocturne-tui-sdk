use nocturne_native::NativeScene;
#[test]
fn owned_firework_stage_readback(){
 let mut s=NativeScene::new(42).unwrap();s.command(r#"{"op":"emitter","id":1,"effect":"weather/chrysanthemum","seed":73,"count":1,"runningTimeMs":0,"coreMs":200}"#).unwrap();s.advanceTo(8333).unwrap();
 let before=s.snapshot().unwrap();let mut info=s.infoComplete().unwrap();assert!(info.contains(r#""sampleLimit":16"#));
 let tail=info.split(r#""samples":[["#).nth(1).unwrap();let row:Vec<f64>=tail.split(']').next().unwrap().split(',').map(|x|x.parse().unwrap()).collect();
 assert_eq!(row.len(),6);assert_eq!(row[0],1.0);assert_eq!(row[3],1.0);assert_eq!(row[5],1.0);
 info.clear();assert!(s.infoComplete().unwrap().contains("burstStages"));assert_eq!(before,s.snapshot().unwrap());
}
