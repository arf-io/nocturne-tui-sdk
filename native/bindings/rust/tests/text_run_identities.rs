use nocturne_native::NativeScene;
#[test]
fn persistent_source_clusters_and_owned_results(){
 let mut scene=NativeScene::new(7).unwrap();scene.command(r#"{"op":"draft","text":"A e\u0301 Z","emitWeather":false}"#).unwrap();let old=scene.text_run_clusters(0,0).unwrap();assert_eq!(old.len(),5);
 scene.command(r#"{"op":"draft","text":"A X e\u0301 Z","emitWeather":false}"#).unwrap();let mut rows=scene.text_run_clusters(0,0).unwrap();assert_eq!(rows.len(),7);assert_eq!(rows[0][0],old[0][0]);assert_eq!(rows[6][0],old[4][0]);assert_eq!(rows[4][0],old[2][0]);
 let before=scene.snapshot().unwrap();rows[0][0]=99;assert_ne!(scene.text_run_clusters(0,0).unwrap()[0][0],99);assert_eq!(scene.snapshot().unwrap(),before);
}
