use nocturne_native::NativeScene;
#[test]
fn owned_field_sampler_and_rejection(){
 let mut s=NativeScene::new(42).unwrap();s.command(r#"{"op":"field","x":10,"y":5,"width":3,"speed":0,"strength":0.7,"continuous":true,"frequency":0,"phase":90}"#).unwrap();
 let before=s.snapshot().unwrap();let mut row=s.field_sample(1,10.,5.).unwrap().unwrap();assert!((row[0]-0.42).abs()<2e-6);assert_eq!(&row[2..],&[10.,5.]);row[0]=-99.;assert!(s.field_sample(1,10.,5.).unwrap().unwrap()[0]>0.);assert_eq!(before,s.snapshot().unwrap());assert!(s.field_sample(0,0.,0.).is_err());assert!(s.field_sample(1,f64::NAN,0.).is_err());assert!(s.field_sample(999,0.,0.).unwrap().is_none());
}
