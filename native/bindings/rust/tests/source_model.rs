use nocturne_native::NativeScene;
#[test]fn original_model_owned_storage(){
 let data=include_bytes!("../../../tests/fixtures/source-model/model-records.bin");
 let mut a=NativeScene::new(2030).unwrap();let mut b=NativeScene::new(2030).unwrap();
 a.set_model_records(data).unwrap();assert_eq!(a.model_records().unwrap(),data);
 let text="A🙂אב".repeat(14001);a.command(&format!("{{\"op\":\"input\",\"text\":\"{}\"}}",text)).unwrap();
 let snapshot=a.snapshot().unwrap();b.restore(&snapshot).unwrap();assert_eq!(b.model_records().unwrap(),data);
 let mut bad=data.to_vec();bad[39]=1;assert!(a.set_model_records(&bad).is_err());assert_eq!(a.snapshot().unwrap(),snapshot);
 a.set_model_records(&[]).unwrap();assert!(a.model_records().unwrap().is_empty());assert_eq!(b.model_records().unwrap(),data);
}
