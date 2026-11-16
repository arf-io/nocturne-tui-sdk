use nocturne_native::NativeScene;
#[test]
fn owned_flux_balance_and_replay(){
 let mut scene=NativeScene::new(2030).unwrap();
 for command in [
r#"{"op":"floor","enabled":false}"#,
r#"{"op":"surface","id":1,"restitution":1,"friction":0,"settleSpeed":0}"#,
r#"{"op":"mesh","triangles":[{"a":[0,0,0],"b":[1,0,0],"c":[0,0,1],"surfaceId":1},{"a":[1,0,0],"b":[1,0,1],"c":[0,0,1],"surfaceId":1}]}"#,
r#"{"op":"surface-foam","surfaceId":1,"sourceRate":0,"decay":0,"impactGain":0.001}"#,
r#"{"op":"emitter","id":1,"effect":"weather/autumn-drift","count":1,"runningTimeMs":0,"shape":"point","position":[0.2,1,0.2],"velocity":[0,-240,0],"extent":[0,0,0],"spread":[0,0,0],"gravity":[0,0,0],"wind":[0,0,0],"windVariation":[0,0,0],"drag":0,"lift":0,"flutterHz":0,"flutterAmount":0,"tumble":[0,0,0],"deposit":false,"collision":true,"lifetimeMinMs":10000,"lifetimeMaxMs":10000,"sizeMin":1,"sizeMax":1,"colliders":{"surfaces":[1]}}"#,
]{scene.command(command).unwrap();}
 scene.advanceTo(8333).unwrap();scene.command(r#"{"op":"surface-foam-transport","surfaceId":1,"velocity":[1,0]}"#).unwrap();
 let saved=scene.snapshot().unwrap();scene.advanceTo(16666).unwrap();let mut rows=scene.surface_foam_transport(1).unwrap();
 assert_eq!(rows.len(),2);let amount=0.24*2.0/120.0;
 assert!((rows[0][1]-(0.24-amount)).abs()<1e-11);assert!((rows[1][1]-amount).abs()<1e-11);
 for r in &rows{assert!((r[2]+r[5]-r[1]-r[3]-r[4]-r[6]).abs()<1e-11);}
 let finish=scene.snapshot().unwrap();rows[0][1]=99.0;assert_ne!(scene.surface_foam_transport(1).unwrap()[0][1],99.0);
 scene.restore(&saved).unwrap();scene.advanceTo(16666).unwrap();assert_eq!(scene.snapshot().unwrap(),finish);
}
