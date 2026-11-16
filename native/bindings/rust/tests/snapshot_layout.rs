#[path="support/current_writer.rs"] mod current_writer;
use current_writer::assert_current_snapshot;
use nocturne_native::NativeScene;

fn schema(bytes: &[u8]) -> u32 { u32::from_le_bytes(bytes[12..16].try_into().unwrap()) }

#[test]
fn restores_expanded_contracts7_snapshot_and_promotes_to_union() {
    let bytes = include_bytes!("fixtures/contracts7-expanded-schema03.bin");
    assert_eq!(schema(bytes), 0x20261003);
    let mut scene = NativeScene::new(991).unwrap();
    scene.restore(bytes).unwrap();
    assert!(scene.info().contains("/lab/one"));
    let current=scene.snapshot().unwrap();assert_current_snapshot(&mut scene,&current);
}

#[test]
fn restores_local_intent_snapshot_and_rejects_wrong_layout_pair_atomically() {
    let local = include_bytes!("fixtures/local-intent-schema04.bin");
    let mut scene = NativeScene::new(992).unwrap();
    scene.restore(local).unwrap();
    assert!(scene.info().contains("intentValue"));
    let current=scene.snapshot().unwrap();assert_current_snapshot(&mut scene,&current);
    let before = scene.snapshot().unwrap();
    let mut wrong = include_bytes!("fixtures/contracts7-expanded-schema03.bin").to_vec();
    wrong[12..16].copy_from_slice(&0x20261004u32.to_le_bytes());
    assert!(scene.restore(&wrong).is_err());
    assert_eq!(scene.snapshot().unwrap(), before);
}
