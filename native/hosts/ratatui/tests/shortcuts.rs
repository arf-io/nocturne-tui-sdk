use nocturne_ratatui::shortcuts::ShortcutProfile;
use nocturne_native::NativeScene;
use ratatui::crossterm::event::{KeyCode,KeyEvent,KeyModifiers};
#[test]
fn negotiated_events_reservations_hints_and_native_ownership(){
 let reserved=["Ctrl+q","F1","F6"].map(str::to_string);
 let p=ShortcutProfile::new(&reserved).unwrap();
 assert!(p.hints.contains("Quit: Alt+q"));assert!(p.hints.contains("Help: F7"));
 assert_eq!(p.action(KeyEvent::new(KeyCode::Char('q'),KeyModifiers::ALT)),Some(1));
 assert_eq!(p.action(KeyEvent::new(KeyCode::Char('q'),KeyModifiers::CONTROL)),None);
 assert!(p.managed(KeyEvent::new(KeyCode::Char('q'),KeyModifiers::CONTROL)));
 assert_eq!(p.action(KeyEvent::new(KeyCode::F(7),KeyModifiers::NONE)),Some(2));
 assert_eq!(p.action(KeyEvent::new(KeyCode::F(8),KeyModifiers::NONE)),Some(3));
 let mut scene=NativeScene::new(7).unwrap();scene.command(r#"{"op":"draft","text":"retained e\u0301","emitWeather":false}"#).unwrap();let before=scene.snapshot().unwrap();
 ShortcutProfile::new(&reserved).unwrap();assert_eq!(scene.snapshot().unwrap(),before);
 if p.action(KeyEvent::new(KeyCode::F(7),KeyModifiers::NONE))==Some(2){scene.command(r#"{"op":"key","key":"F1"}"#).unwrap();}
 assert_eq!(scene.text_run_source(0,0).unwrap(),"retained é");assert!(scene.info().contains("\"inputOwner\":\"modal\"")||scene.info().contains("\"inputOwner\":\"help\""));
}
#[test]
fn unassigned_and_unknown_reservations_are_explicit(){
 let p=ShortcutProfile::new(&["Ctrl+q".into(),"Alt+q".into()]).unwrap();assert!(p.hints.contains("Quit: unassigned"));assert!(p.rows.iter().any(|r|r==&[1,0,0,0]));
 assert!(ShortcutProfile::new(&["Ctrl+c".into()]).is_err());
}
