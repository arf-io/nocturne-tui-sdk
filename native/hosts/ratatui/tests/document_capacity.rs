use nocturne_native::NativeScene;
use nocturne_ratatui::{text_anchor::RetainedTextAnchor, UnicodeDocument};
#[test]
fn whole_document_capacity_and_retained_anchor() {
    let mut s = NativeScene::new(2030).unwrap();
    let text = format!("ABC{}", "Aא́👩‍🔧ב\tZ\n".repeat(7001));
    s.command(
        &serde_json::json!({"op":"draft","text":text,"caret":0,"emitWeather":false}).to_string(),
    )
    .unwrap();
    let before = s.snapshot().unwrap();
    let mut v = UnicodeDocument::new();
    v.presentation(&s, 79, 20, None).unwrap();
    assert_eq!(s.snapshot().unwrap(), before);
    let anchor = RetainedTextAnchor::capture(&s, 0, 0, 1).unwrap();
    s.command(
        &serde_json::json!({"op":"draft","text":format!("X{text}"),"emitWeather":false})
            .to_string(),
    )
    .unwrap();
    assert_eq!(anchor.resolve(&s).unwrap(), Some(2));
    v.presentation(&s, 79, 20, None).unwrap();
    let offset = v.move_offset(&s, 2, "PageDown").unwrap();
    v.follow_caret(&s, offset).unwrap();
    v.scroll_by(-3);
    v.hit(&s, 2, 2).unwrap();
    assert_eq!(s.text_run_source(0, 0).unwrap(), format!("X{text}"));
    s.command(
        &serde_json::json!({"op":"draft","text":format!("XAYC{}",&text[3..]),"emitWeather":false})
            .to_string(),
    )
    .unwrap();
    assert_eq!(anchor.resolve(&s).unwrap(), None);
}
