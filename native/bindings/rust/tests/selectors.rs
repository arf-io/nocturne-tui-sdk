//! Direct C-ABI regression checks; no serde or external crate is required.
#![allow(non_snake_case)]
#[path="support/current_writer.rs"] mod current_writer;
use current_writer::assert_current_snapshot;
use nocturne_native::NativeScene;

const BUTTON: &str = r#"{"op":"widget","id":1,"kind":"button","x":8,"y":8,"width":30,"height":3,"text":"Style me","material":1,"alpha":0.2}"#;
const REGISTER: &str = r#"{"op":"state-register","id":1,"path":"/rust/control","role":"control","target":{"family":"widget","id":1}}"#;

#[test]
fn overlayRestoresCurrentAuthoredStyle() -> Result<(), String> {
    let mut scene=NativeScene::new(2030)?;
    let mut reference=NativeScene::new(2030)?;
    scene.command(BUTTON)?;reference.command(BUTTON)?;
    scene.command(REGISTER)?;
    scene.command(r#"{"op":"style-rule","id":1,"selector":{"family":"widget","role":"control"},"style":{"material":2,"alpha":0.8}}"#)?;
    assert_ne!(scene.render()?.bytes,reference.render()?.bytes);
    let authored=r#"{"op":"widget","id":1,"material":3,"alpha":0.4}"#;
    scene.command(authored)?;reference.command(authored)?;
    scene.command(r#"{"op":"remove-style-rule","id":1}"#)?;
    assert_eq!(scene.render()?.bytes,reference.render()?.bytes);
    Ok(())
}
#[test]
fn mappedAppearancePreservesSnapshotAndRejectsInvalidReplacement() -> Result<(), String> {
    let mut scene=NativeScene::new(2030)?;
    scene.command(BUTTON)?;scene.command(REGISTER)?;
    scene.command(r#"{"op":"define","path":"/load","value":25}"#)?;
    scene.command(r#"{"op":"style-rule","id":1,"selector":{"family":"widget"},"style":{"alpha":{"path":"/load","inputMin":0,"inputMax":100,"outputMin":0.1,"outputMax":0.9}}}"#)?;
    let before=scene.snapshot()?;
    for _ in 0..8 { scene.render()?; assert!(scene.info().contains("registeredStates")); }
    assert_eq!(before,scene.snapshot()?);
    assert!(scene.command(r#"{"op":"style-rule","id":1,"selector":{"family":"widget"},"style":{"alpha":{"path":"/load","inputMin":1,"inputMax":1,"outputMin":0,"outputMax":1}}}"#).is_err());
    assert_eq!(before,scene.snapshot()?);
    Ok(())
}
#[test]
fn pointerStateSurvivesSnapshotReplay() -> Result<(), String> {
    let mut scene=NativeScene::new(2030)?;
    scene.command(BUTTON)?;scene.command(REGISTER)?;
    scene.command(r#"{"op":"pointer","phase":"move","x":12,"y":9}"#)?;
    let before=scene.snapshot()?;
    assert_current_snapshot(&mut scene,&before);
    scene.command(r#"{"op":"pointer","phase":"cancel","x":-1,"y":-1}"#)?;
    assert_ne!(before,scene.snapshot()?);
    scene.restore(&before)?;
    assert_eq!(before,scene.snapshot()?);
    Ok(())
}
