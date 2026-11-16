use nocturne_native::NativeScene;
#[test]
fn text_run_identity_source_and_reflow(){
 let mut s=NativeScene::new(2030).unwrap();s.command(r#"{"op":"text","id":41,"text":"Aé中"}"#).unwrap();
 assert_eq!(s.text_run_hit(1,41,3,1,1,1).unwrap(),4);
 assert_eq!(s.text_run_clip(1,41,8,3,0,1,1,1).unwrap(),vec![[41,3,4,2,0,2,1,1,1]]);
 assert_eq!(s.text_run_source(1,41).unwrap(),"Aé中");
 assert_eq!(s.text_run_layout(1,41,3,1).unwrap(),vec![[41,0,1,0,0,1,1],[41,1,3,1,0,1,1],[41,3,4,0,1,2,1]]);
 let mut rows=s.text_run_layout(1,41,8,1).unwrap();rows[0][0]=999;assert_eq!(s.text_run_layout(1,41,8,1).unwrap()[0][0],41);
 assert!(s.text_run_source(1,999).is_err());assert!(s.text_run_layout(1,41,0,1).is_err());
}
#[test]
fn text_cluster_identity_boundary(){
 let mut s=NativeScene::new(2030).unwrap();s.command(r#"{"op":"text","id":41,"text":"AéZ"}"#).unwrap();
 let old=s.textClusterSample(41,1).unwrap();assert_eq!(&old[1..3],&[1,3]);
 s.command(r#"{"op":"text","id":41,"text":"AèZ"}"#).unwrap();
 assert_ne!(old[0],s.textClusterSample(41,1).unwrap()[0]);assert!(s.textClusterSample(41,3).is_err());
}
