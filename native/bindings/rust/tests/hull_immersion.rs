use nocturne_native::NativeScene;
#[test]
fn oriented_immersion_and_wrench_owned(){
 let scene=NativeScene::new(2030).unwrap();
 let vertices=[[0.0,0.0,0.0],[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]];let faces=[[0,2,1],[0,1,3],[0,3,2],[1,2,3]];
 let expected=[1.0/6.0,7.0/48.0,15.0/56.0,11.0/56.0,15.0/56.0];
 let mut row=scene.hull_immersion_plane(&vertices,&faces,[0.0,0.5,0.0],[0.0,10.0,0.0]).unwrap();
 for(a,b)in row.iter().zip(expected){assert!((a-b).abs()<1e-9)}
 row[1]=999.0;assert!((scene.hull_immersion_plane(&vertices,&faces,[0.0,0.5,0.0],[0.0,1.0,0.0]).unwrap()[1]-7.0/48.0).abs()<1e-9);
 let wrench=scene.hull_buoyancy_plane(&vertices,&faces,[0.0,0.5,0.0],[0.0,1.0,0.0],48.0,1.0,7.0,[0.0;3]).unwrap();
 for(a,b)in wrench.iter().zip([1.0/6.0,7.0/48.0,15.0/56.0,11.0/56.0,15.0/56.0,0.0,0.0,0.0,-15.0/8.0,0.0,15.0/8.0]){assert!((a-b).abs()<1e-9)}
 assert!(scene.hull_immersion_plane(&vertices,&faces,[0.0;3],[0.0;3]).is_err());
}
#[test]
fn analytic_hull_immersion_owned(){
 let scene=NativeScene::new(2030).unwrap();
 let vertices=[[0.0,0.0,0.0],[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]];
 let faces=[[0,2,1],[0,1,3],[0,3,2],[1,2,3]];
 let mut row=scene.hull_immersion(&vertices,&faces,0.5).unwrap();let expected=[1.0/6.0,7.0/48.0,15.0/56.0,11.0/56.0,15.0/56.0];
 for (a,b) in row.iter().zip(expected){assert!((a-b).abs()<1e-9);}
 row[0]=999.0;assert!((scene.hull_immersion(&vertices,&faces,0.5).unwrap()[0]-1.0/6.0).abs()<1e-9);
 assert!(scene.hull_immersion(&vertices,&faces,f64::NAN).is_err());
 assert!(scene.hull_immersion(&vertices,&faces[..3],0.5).is_err());
}
#[test]
fn retained_pose_owned_and_retired(){
 let mut scene=NativeScene::new(2030).unwrap();
 for command in [r#"{"op":"surface","id":1}"#,r#"{"op":"float-body","id":1,"surfaceId":1}"#,r#"{"op":"float-hull","id":1,"vertices":[[0,0,0],[1,0,0],[0,1,0],[0,0,1]],"faces":[[0,2,1],[0,1,3],[0,3,2],[1,2,3]],"inertia":[1,2,3]}"#]{scene.command(command).unwrap();}
 let mut row=scene.float_hull(1).unwrap().unwrap();assert!((row[13]-1.0/6.0).abs()<1e-9);assert_eq!(&row[7..10],&[1.0,2.0,3.0]);assert_eq!(row[3],1.0);
 row[13]=999.0;assert!((scene.float_hull(1).unwrap().unwrap()[13]-1.0/6.0).abs()<1e-9);
 scene.command(r#"{"op":"remove-float-body","id":1}"#).unwrap();assert_eq!(scene.float_hull(1).unwrap(),None);
}
#[test]
fn mesh_immersion_independent_tetrahedron(){
 let scene=NativeScene::new(2030).unwrap();let vertices=[[0.0,0.0,0.0],[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]];let faces=[[0,2,1],[0,1,3],[0,3,2],[1,2,3]];let water=[[-2.0,0.5,-2.0,4.0,0.5,-2.0,-2.0,0.5,4.0]];
 let mut row=scene.hull_mesh_immersion(&vertices,&faces,&water).unwrap();for(a,b)in row.iter().zip([1.0/6.0,7.0/48.0,15.0/56.0,11.0/56.0,15.0/56.0]){assert!((a-b).abs()<1e-9);}
 row[1]=999.0;assert!((scene.hull_mesh_immersion(&vertices,&faces,&water).unwrap()[1]-7.0/48.0).abs()<1e-9);
 assert!(scene.hull_mesh_immersion(&vertices,&faces,&[water[0],water[0]]).is_err());
}
