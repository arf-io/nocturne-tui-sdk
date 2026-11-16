use nocturne_native::NativeScene;
#[test]
fn document_capacity() {
    let s = NativeScene::new(2030).unwrap();
    for text in ["", "AאבB", "א́👩‍🔧ב\tA\nב"] {
        for direction in 0..3 {
            assert_eq!(
                s.document_layout(text, 7, direction, 1).unwrap(),
                s.bidi_layout(text, 7, direction, 1).unwrap()
            );
            for offset in s.document_boundaries(text).unwrap() {
                for affinity in 0..2 {
                    assert_eq!(
                        s.document_caret(text, 7, offset, affinity, direction, 1)
                            .unwrap(),
                        s.bidi_caret(text, 7, offset, affinity, direction, 1)
                            .unwrap()
                    );
                }
            }
            for (x, y) in [(0, 0), (3, 0), (0, 3)] {
                assert_eq!(
                    s.document_hit(text, 7, x, y, direction, 1).unwrap(),
                    s.bidi_hit(text, 7, x, y, direction, 1).unwrap()
                );
            }
        }
    }
    for text in ["אב".repeat(2501), "Aא́👩‍🔧ב\tZ\n".repeat(7001)] {
        assert!(s.document_layout(&text, 79, 2, 1).unwrap().len() > 2048);
    }
    assert!(s.document_caret("é", 8, 1, 1, 2, 1).is_err());
}
