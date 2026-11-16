use nocturne_native::NativeScene;

#[test]
fn generated_window_document_source_reads_full_empty_and_missing() {
    let mut scene = NativeScene::new(2030).unwrap();
    scene.command(r#"{"op":"window","id":1,"title":"Window","text":"initial"}"#).unwrap();
    let text = format!("{}Z", "x".repeat(4095));
    scene.command(&format!(r#"{{"op":"window-content","id":1,"text":{}}}"#, serde_json_string(&text))).unwrap();
    assert_eq!(text.chars().count(), 4096);
    assert_eq!(scene.text_run_source(2, 1).unwrap(), text);
    scene.command(r#"{"op":"window-content","id":1,"text":""}"#).unwrap();
    assert_eq!(scene.text_run_source(2, 1).unwrap(), "");
    assert!(scene.text_run_source(2, 65535).is_err());
}

fn serde_json_string(text: &str) -> String {
    format!("\"{}\"", text.replace('\\', "\\\\").replace('"', "\\\"").replace('\n', "\\n"))
}
