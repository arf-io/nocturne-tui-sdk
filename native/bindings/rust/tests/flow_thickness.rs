use nocturne_native::NativeScene;
#[test]
fn owned_thickness_geometry_and_replay(){
 let mut scene=NativeScene::new(2030).unwrap();
 for command in [r#"{"op":"surface","id":1}"#,r#"{"op":"ribbon","points":[[0,0,-2],[0,0,0]],"width":2,"surfaceId":1}"#,r#"{"op":"flow","id":1,"flux":2,"stages":[{"name":"channel"}]}"#,r#"{"op":"flow-surface","surfaceId":1,"flowId":1,"stage":"channel","referenceFlux":2}"#,r#"{"op":"flow-thickness","surfaceId":1,"width":2,"speed":2,"maxDepth":1}"#]{scene.command(command).unwrap();}
 assert!((scene.flow_thickness(1).unwrap().unwrap()[1]-0.5).abs()<1e-11);
 let mut rows=scene.surface_triangles(1).unwrap();assert_eq!(rows.len(),12);let saved=scene.snapshot().unwrap();rows[0][1]=99.0;assert_ne!(scene.surface_triangles(1).unwrap()[0][1],99.0);
 scene.advanceTo(500000).unwrap();let finish=scene.snapshot().unwrap();scene.restore(&saved).unwrap();scene.advanceTo(500000).unwrap();assert_eq!(scene.snapshot().unwrap(),finish);
}
