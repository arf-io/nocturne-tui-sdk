use nocturne_native::NativeScene;
#[test]
fn owned_water_sample_balances_receiver_input(){
 let mut scene=NativeScene::new(2030).unwrap();
 for command in [r#"{"op":"surface","id":1}"#,r#"{"op":"mesh","triangles":[{"a":[-2,0,-2],"b":[2,0,-2],"c":[0,0,2],"surfaceId":1}]}"#,r#"{"op":"surface-water","surfaceId":1,"capacity":1}"#,r#"{"op":"surface-water-add","triangleIndex":0,"volume":0.5}"#]{scene.command(command).unwrap();}
 let before=scene.snapshot().unwrap();let mut row=scene.water_sample(0).unwrap().unwrap();assert_eq!(row,[1.0,0.5,0.5,0.5,0.0,0.0,0.0,1.0]);row[2]=999.0;assert_eq!(scene.water_sample(0).unwrap().unwrap()[2],0.5);assert_eq!(scene.snapshot().unwrap(),before);
}
