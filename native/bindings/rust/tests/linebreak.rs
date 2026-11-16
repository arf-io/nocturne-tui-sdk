use nocturne_native::NativeScene;
#[test]
fn owned_scalar_line_break_references(){
 let scene=NativeScene::new(2030).unwrap();let before=scene.snapshot().unwrap();
 for (source,expected) in [("hello world",vec![6,11]),("A\r\nB",vec![3,4]),("",vec![0]),("你好",vec![1,2]),("1,234.5",vec![7]),("A\u{2060}B",vec![3]),("🇦🇧🇨🇩",vec![2,4]),("👩‍🚀",vec![3])]{let mut row=scene.line_breaks(source).unwrap();assert_eq!(row,expected);row[0]=999;assert_eq!(scene.line_breaks(source).unwrap(),expected);}
 let expected=vec![[2,0],[5,1],[7,1],[8,1]];let mut details=scene.line_break_details("A B\r\nC\u{2028}D").unwrap();assert_eq!(details,expected);details[0][0]=999;assert_eq!(scene.line_break_details("A B\r\nC\u{2028}D").unwrap(),expected);assert_eq!(scene.line_break_details("").unwrap(),vec![[0,1]]);assert!(scene.line_break_details(&"A".repeat(2049)).is_err());
 assert!(scene.line_breaks(&"A".repeat(2049)).is_err());assert_eq!(scene.snapshot().unwrap(),before);
}
