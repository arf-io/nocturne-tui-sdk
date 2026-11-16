#[path = "../examples/support/mod.rs"]
mod support;
use nocturne_native::NativeScene;
#[test]
fn modalPasteIsAtomicAndUnicodePasteIsAcceptedAfterRelease() -> Result<(), String> {
    let mut scene = NativeScene::new(2030)?;
    scene.command(r#"{"op":"key","key":"F1"}"#)?;
    let before = scene.snapshot()?;
    scene.command(&support::pasteCommand("X"))?;
    assert_eq!(before, scene.snapshot()?);
    scene.command(r#"{"op":"key","key":"F1"}"#)?;
    scene.command(&support::pasteCommand("é\n日本"))?;
    assert!(scene.info().contains("é\\n日本"));
    Ok(())
}
