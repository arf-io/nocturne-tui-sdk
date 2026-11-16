use nocturne_native::NativeScene;
#[test]
fn owned_source_trails_and_rejection() {
    let mut s=NativeScene::new(2030).unwrap();
    s.command(r#"{"op":"text","id":41,"text":"N","effect":"text/comet-stitch","phase":"hide","trailLength":8,"durationMs":1000,"variation":0,"staggerMs":0,"wind":2}"#).unwrap();
    s.advanceTo(250000).unwrap();
    let main=s.textSample(41,0).unwrap();
    let mut trail=s.textTrailSample(41,0,7).unwrap();
    assert_eq!(trail[0],main[2]);assert_eq!(trail[1],78);assert_eq!(trail[2],8);
    assert!((trail[3] as i64-main[3] as i64+157286).abs()<100);
    assert!(trail[5]>0);let original=trail;trail[0]=0;
    assert_eq!(s.textTrailSample(41,0,7).unwrap(),original);
    assert!(s.textTrailSample(41,0,8).is_err());assert!(s.textTrailSample(41,1,0).is_err());
    s.advanceTo(2000000).unwrap();assert!(s.textTrailSample(41,0,0).is_err());
}
