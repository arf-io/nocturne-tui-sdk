use nocturne_native::NativeScene;
use nocturne_ratatui::UnicodeDocument;
use ratatui::{buffer::Buffer,layout::Rect,widgets::Widget};

#[test]
fn clusters_mapping_and_owned_render() {
 let mut scene=NativeScene::new(2030).unwrap();
 scene.command(r#"{"op":"paste","text":"א́👩‍🔧ב"}"#).unwrap();
 let before=scene.snapshot();
 let mut document=UnicodeDocument::new();
 let frame=document.presentation(&scene,20,8,None).unwrap();
 let mut buf=Buffer::empty(Rect::new(2,3,20,8));
 (&frame).render(Rect::new(2,3,20,8),&mut buf);
 assert_eq!(buf[(2,4)].symbol(),"ב");
 assert_eq!(buf[(3,4)].symbol(),"👩‍🔧");
 assert_eq!(buf[(5,4)].symbol(),"א́");
 assert_eq!(before,scene.snapshot());
 assert_eq!(document.hit(&scene,0,1).unwrap(),6);
}

#[test]
fn viewport_clipping_preserves_neighbors_and_source() {
 let mut scene=NativeScene::new(2030).unwrap();
 scene.command(r#"{"op":"paste","text":"👩‍🔧"}"#).unwrap();
 let mut document=UnicodeDocument::new();
 let frame=document.presentation(&scene,1,2,None).unwrap();
 let mut buf=Buffer::empty(Rect::new(0,0,4,4));buf[(1,1)].set_symbol("X");
 (&frame).render(Rect::new(0,0,1,2),&mut buf);
 assert_eq!(buf[(0,1)].symbol()," ");assert_eq!(buf[(1,1)].symbol(),"X");
 assert_eq!(scene.text_run_source(0,0).unwrap(),"👩‍🔧");
}

#[test]
fn navigation_preserves_column_and_scroll_follows_only_changes() {
 let mut scene=NativeScene::new(2030).unwrap();scene.command(r#"{"op":"paste","text":"ABCDE\nX\nABCDE"}"#).unwrap();
 let mut view=UnicodeDocument::new();view.presentation(&scene,20,3,None).unwrap();
 assert_eq!(view.move_offset(&scene,4,"ArrowDown").unwrap(),7);
 assert_eq!(view.move_offset(&scene,7,"ArrowDown").unwrap(),12);
 view.follow_caret(&scene,12).unwrap();assert_eq!(view.scroll,1);
 view.scroll_by(-1);view.follow_caret(&scene,12).unwrap();assert_eq!(view.scroll,0);
 view.follow_caret(&scene,13).unwrap();assert_eq!(view.scroll,1);
}
