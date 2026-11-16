use nocturne_native::NativeScene;
#[test]
fn registered_resource_controls_match_public_authoring(){
 let burst=r#"{"op":"emitter","id":1,"effect":"weather/chrysanthemum","seed":73,"count":8,"runningTimeMs":0,"lifetimeMinMs":2000,"lifetimeMaxMs":2000}"#;
 let arc=r#"{"op":"electrical-arc","id":7,"points":[{"position":[0,0,0],"parent":-1},{"position":[3,0,0],"parent":0}]}"#;
 let fields=[("glitterHz",30.0),("glitterDepth",0.2),("coreAlpha",0.3),("residualMs",350.125),("residualAlpha",0.4),("speed",20.0),("jitter",0.5),("alpha",0.4),("flicker",0.2),("delayMs",50.125),("holdMs",150.125),("fadeMs",250.125),("repeatMs",3000.125)];
 for (index,(field,value)) in fields.iter().enumerate(){
  let (family,id,base)=if index<5{("emitter",1,burst)}else{("electrical-arc",7,arc)};
  let mut s=NativeScene::new(42).unwrap();let mut o=NativeScene::new(42).unwrap();s.command(base).unwrap();
  if index<5{o.command(base).unwrap();s.advanceTo(250000).unwrap();o.advanceTo(250000).unwrap();o.command(&format!(r#"{{"op":"burst-style","id":1,"{field}":{value}}}"#)).unwrap();}
  else{o.command(&format!("{},\"{field}\":{value}}}",base.trim_end_matches('}'))).unwrap();}
  s.command(&format!(r#"{{"op":"define","path":"/control","value":{value},"binding":{{"family":"{family}","id":{id},"field":"{field}"}}}}"#)).unwrap();
  s.command(r#"{"op":"remove-value","path":"/control"}"#).unwrap();
  let expected=s.snapshot().unwrap();assert!(expected==o.snapshot().unwrap(),"public authoring differs: {family}/{field}");
  assert!(s.command(&format!(r#"{{"op":"define","path":"/bad","value":-1,"binding":{{"family":"{family}","id":{id},"field":"{field}"}}}}"#)).is_err());
  assert!(s.snapshot().unwrap()==expected,"rollback differs: {family}/{field}");
 }
}
