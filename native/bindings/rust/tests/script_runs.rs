use nocturne_native::{NativeScene,ScriptRun};

#[test]
fn owned_script_runs_use_unicode_scalar_offsets() {
 let scene=NativeScene::new(2030).unwrap();
 let expected=vec![ScriptRun{start:0,end:3,script:"Latn".into()},ScriptRun{start:3,end:10,script:"Arab".into()}];
 let mut rows=scene.script_runs("a\u{301} العربية").unwrap();assert_eq!(rows,expected);
 assert_eq!(scene.script_runs("アー").unwrap(),vec![ScriptRun{start:0,end:2,script:"Kana".into()}]);
 assert_eq!(rows,expected);rows[0].script="Zyyy".into();assert_eq!(scene.script_runs("a\u{301} العربية").unwrap(),expected);
 assert_eq!(scene.script_runs("👩\u{200d}🔧").unwrap(),vec![ScriptRun{start:0,end:3,script:"Zyyy".into()}]);
 assert!(scene.script_runs("").unwrap().is_empty());assert!(scene.script_runs(&"a".repeat(2049)).is_err());
}
#[test]
fn font_lines_preserve_paragraph_base() {
 let scene=NativeScene::new(2030).unwrap();let mut rows=scene.bidi_lines("אב ab ",&[3,6],2).unwrap();
 assert_eq!(rows.iter().map(|r|r[0]).collect::<Vec<_>>(),vec![2,1,0,5,3,4]);
 assert_eq!(rows.iter().map(|r|r[5]).collect::<Vec<_>>(),vec![1,1,1,1,2,2]);
 rows[0][0]=999;assert_eq!(scene.bidi_lines("אב ab ",&[3,6],2).unwrap()[0][0],2);
 assert!(scene.bidi_lines("a\u{301}b",&[1,3],2).is_err());assert!(scene.bidi_lines("a\nb",&[3],2).is_err());
}
