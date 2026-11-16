use nocturne_native::NativeScene;
#[test]
fn public_scenic_fixtures_execute_owned_and_pure(){
 for (name,fixture) in [("waterfall",include_str!("../../../examples/waterfall-scene.json")),("road",include_str!("../../../examples/road-scene.json")),("garden",include_str!("../../../examples/garden-scene.json"))]{
  let commands=fixture.split("\"commands\":").nth(1).unwrap().trim().strip_suffix('}').unwrap().trim();
  let mut s=NativeScene::new(42).unwrap();s.command(&format!(r#"{{"op":"batch","commands":{commands}}}"#)).unwrap();s.advanceTo(1000000).unwrap();
  let before=s.snapshot().unwrap();let mut info=s.infoComplete().unwrap();assert!(info.contains("nocturne.metadata/v1"));
  if name=="road"{
   let camera=info.split(r#""camera":{"#).nth(1).unwrap();
   let position=camera.split(r#""position":["#).nth(1).unwrap().split(']').next().unwrap();
   let values:Vec<f64>=position.split(',').map(|value|value.parse().unwrap()).collect();
   assert_eq!(values,vec![0.0,1.7,-2.0]);
  }
  if name=="waterfall"{assert!(info.contains(r#""deliveredVolume":1"#));}
  s.render().unwrap();assert!(s.snapshot().unwrap()==before);info.clear();assert!(!s.infoComplete().unwrap().is_empty());
 }
}
