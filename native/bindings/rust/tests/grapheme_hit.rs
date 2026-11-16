use nocturne_native::NativeScene;
#[test]
fn grapheme_hit_boundaries(){
 let s=NativeScene::new(2030).unwrap();
 for (text,cols,x,y,want) in [("é中",8,1,0,2),("👩‍🔧A",8,1,0,3),("A\r\n",8,0,1,3),("",1,0,0,0)]{assert_eq!(s.grapheme_hit(text,cols,x,y,1).unwrap(),want);}
 assert!(s.grapheme_hit("A",0,0,0,1).is_err());assert!(s.grapheme_hit("A",1,0,0,0).is_err());
}
