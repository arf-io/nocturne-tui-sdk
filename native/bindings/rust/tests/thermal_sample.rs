use nocturne_native::NativeScene;
#[test]
fn owned_thermal_sample_matches_analytic_energy(){
 let mut scene=NativeScene::new(2030).unwrap();
 scene.command(r#"{"op":"mesh","triangles":[{"a":[-2,-2,0],"b":[2,-2,0],"c":[0,2,0]}]}"#).unwrap();
 assert_eq!(scene.thermal_sample(0).unwrap(),None);
 scene.command(r#"{"op":"surface-thermal","triangleIndex":0,"temperature":293,"capacity":2,"power":4}"#).unwrap();
 scene.advanceTo(500000).unwrap();let before=scene.snapshot().unwrap();let mut row=scene.thermal_sample(0).unwrap().unwrap();
 for (actual,expected) in row.iter().zip([294.0,588.0,586.0,2.0,0.0,0.0,0.0,2.0,4.0,293.0]){assert!((*actual-expected).abs()<1e-6);}
 row[0]=999.0;assert!((scene.thermal_sample(0).unwrap().unwrap()[0]-294.0).abs()<1e-6);
 assert_eq!(scene.snapshot().unwrap(),before);assert!(scene.thermal_sample(1).is_err());
}
