use nocturne_native::NativeScene;
#[test]
fn complete_metadata_retains_large_unicode_source_and_snapshot() -> Result<(),String> {
 let mut scene=NativeScene::new(8128)?;
 assert_eq!(scene.infoComplete()?,scene.info());
 scene.command(r#"{"op":"pause","paused":true}"#)?;
 let text="🙂".repeat(2048);
 for id in 1..=24 {scene.command(&format!(r#"{{"op":"text","id":{id},"text":"{text}"}}"#))?;}
 for id in 1..=12 {scene.command(&format!(r#"{{"op":"window","id":{id},"title":"Retained {id}","text":"{text}","position":[0,0,16000]}}"#))?;}
 let large_prompt="界".repeat(400001);scene.command(&format!(r#"{{"op":"draft","text":"{large_prompt}","emitWeather":false}}"#))?;
 let before=scene.snapshot()?;
 let bounded=scene.info();
 let complete=scene.infoComplete()?;
 assert!(bounded==r#"{"error":"metadata capacity exceeded"}"#||bounded==complete,"bounded metadata neither complete nor capacity error");
 assert!(complete.contains(&large_prompt),"large prompt source lost");assert!(complete.len()>1048576);
 assert_eq!(complete.matches(&text).count(),36);
 assert_eq!(scene.snapshot()?,before);
 scene.command(r#"{"op":"clear","scope":"text"}"#)?;
 assert_eq!(complete.matches(&text).count(),36);
 Ok(())
}

#[test]
fn complete_metadata_beyond_16mib() -> Result<(),String> {
 let mut scene=NativeScene::new(8128)?;
 let escaped="\\u000b".repeat(2800001);
 scene.command(&format!(r#"{{"op":"draft","text":"{escaped}","emitWeather":false}}"#))?;
 let complete=scene.infoComplete()?;
 assert!(complete.len()>16777216,"metadata did not cross old limit");
 assert!(complete.contains(&format!(r#""text":"{escaped}""#)),"large metadata source lost");
 assert!(complete.contains(r#""caret":2800001"#),"large caret lost");
 println!("Actual complete metadata bytes={} scalars=2800001",complete.len());
 Ok(())
}
