use nocturne_native::NativeScene;
#[test]
fn explicit_rotating_surface_frame_queries(){
 let mut scene=NativeScene::new(2030).unwrap();
 for command in [r#"{"op":"surface","id":1}"#,r#"{"op":"mesh","triangles":[{"a":[10,20,30],"b":[14,20,30],"c":[10,20,34],"surfaceId":1}]}"#,r#"{"op":"surface-fluid","surfaceId":1,"mass":3}"#,r#"{"op":"surface-fluid-angular","surfaceId":1,"inertia":3,"pivot":[10,20,30],"orientation":[0,0,0.3826834323650898,0.9238795325112867],"omega":[0,0,1.5707963267948966]}"#]{scene.command(command).unwrap();}
 let before=scene.snapshot().unwrap();let mut rows=scene.surface_triangles(1).unwrap();assert_eq!(rows.len(),1);let expected=10.0+4.0*0.5_f64.sqrt();assert!((rows[0][4]-expected).abs()<1e-9);rows[0][4]=999.0;assert!((scene.surface_triangles(1).unwrap()[0][4]-expected).abs()<1e-9);
 let sample=scene.surface_wave_sample(1,11.0,31.0).unwrap();let expected=[21.0,-0.5_f64.sqrt(),0.5_f64.sqrt(),0.0,std::f64::consts::FRAC_PI_2,0.0];for (a,b) in sample.iter().zip(expected){assert!((a-b).abs()<1e-9);}
 assert_eq!(scene.snapshot().unwrap(),before);
}
#[test]
fn angular_water_owned_lifecycle(){
 let mut scene=NativeScene::new(2030).unwrap();assert_eq!(scene.surface_fluid_angular(1).unwrap(),None);
 for command in [r#"{"op":"surface","id":1}"#,r#"{"op":"surface-fluid","surfaceId":1,"mass":3}"#,r#"{"op":"surface-fluid-angular","surfaceId":1,"inertia":3,"omega":[1,2,3]}"#]{scene.command(command).unwrap();}
 let expected=[3.0,1.0,2.0,3.0,3.0,6.0,9.0,0.0,0.0,0.0,0.0,21.0];let mut row=scene.surface_fluid_angular(1).unwrap().unwrap();assert_eq!(row,expected);row[0]=999.0;assert_eq!(scene.surface_fluid_angular(1).unwrap().unwrap(),expected);
 scene.command(r#"{"op":"export-surface-fluid","surfaceId":1}"#).unwrap();scene.command(r#"{"op":"surface-fluid","surfaceId":1,"mass":5}"#).unwrap();assert_eq!(scene.surface_fluid_angular(1).unwrap(),None);assert!(scene.surface_fluid_angular(0).is_err());
}
#[test]
fn finite_water_owned_record(){
 let mut scene=NativeScene::new(2030).unwrap();scene.command(r#"{"op":"surface","id":1}"#).unwrap();assert_eq!(scene.surface_fluid(1).unwrap(),None);
 scene.command(r#"{"op":"surface-fluid","surfaceId":1,"mass":3,"velocity":[1,2,3]}"#).unwrap();let expected=[3.0,1.0,2.0,3.0,0.0,0.0,0.0,3.0,6.0,9.0,0.0,0.0,0.0,0.0,21.0];let mut row=scene.surface_fluid(1).unwrap().unwrap();assert_eq!(row,expected);row[0]=999.0;assert_eq!(scene.surface_fluid(1).unwrap().unwrap(),expected);assert!(scene.surface_fluid(0).is_err());
}
