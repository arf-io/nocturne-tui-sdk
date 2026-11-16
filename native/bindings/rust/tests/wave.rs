use nocturne_native::NativeScene;
#[test]
fn analytic_wave_and_rejection(){let scene=NativeScene::new(2030).unwrap();let v=scene.wave_sample(&[[2.0,3.0,4.0,5.0,0.2]],0.1,0.2,0.3).unwrap();assert!((v[0]-2.0*(-0.2f64).cos()).abs()<1e-11);assert!(scene.wave_sample(&[[f64::NAN,0.0,0.0,0.0,0.0]],0.0,0.0,0.0).is_err());assert_eq!(scene.wave_sample(&[],0.0,0.0,0.0).unwrap(),[0.0,0.0,1.0,0.0,0.0,0.0]);}
#[test]
fn retained_surface_wave(){let mut scene=NativeScene::new(2030).unwrap();scene.command(r#"{"op":"surface","id":1}"#).unwrap();scene.command(r#"{"op":"surface-waves","surfaceId":1,"waves":[[2,0,0,0,0]]}"#).unwrap();assert_eq!(scene.surface_wave_sample(1,0.0,0.0).unwrap()[0],2.0);}
#[test]
fn float_body_buoyancy(){let mut scene=NativeScene::new(2030).unwrap();for command in [r#"{"op":"surface","id":1}"#,r#"{"op":"mesh","triangles":[{"a":[-10,0,-10],"b":[10,0,-10],"c":[0,0,10],"surfaceId":1}]}"#,r#"{"op":"float-body","id":1,"surfaceId":1,"position":[0,-2,0],"mass":1000,"radius":1,"drag":0}"#]{scene.command(command).unwrap();}scene.advanceTo(8333).unwrap();let body=scene.float_body(1).unwrap().unwrap();let expected=(9.81*4.0*std::f64::consts::PI/3.0-9.81)/120.0;assert!((body[4]-expected).abs()<1e-10);}

#[test]
fn surface_foam_balance(){
 let mut scene=NativeScene::new(2030).unwrap();
 for command in [r#"{"op":"surface","id":1}"#,r#"{"op":"mesh","triangles":[{"a":[-10,0,-10],"b":[10,0,-10],"c":[0,0,10],"surfaceId":1}]}"#,r#"{"op":"surface-waves","surfaceId":1,"waves":[[1,1,0,0,0]]}"#,r#"{"op":"surface-foam","surfaceId":1,"sourceRate":2,"curvatureThreshold":0,"decay":1,"impactGain":0}"#]{scene.command(command).unwrap();}
 scene.advanceTo(8333).unwrap();let rows=scene.surface_foam(1).unwrap();let r=rows[0];
 assert!((r[1]-1.0/121.0).abs()<1e-12);assert!((r[2]-r[1]-r[3]-r[4]).abs()<1e-12);
}
