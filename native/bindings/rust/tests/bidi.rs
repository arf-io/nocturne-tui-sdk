use nocturne_native::NativeScene;
#[test]
fn bidi_owned_visual_mapping(){
 let s=NativeScene::new(2030).unwrap();
 let mut rows=s.bidi_visual("א12ב",0).unwrap();assert_eq!(rows,vec![[3,1,1,0x5d1],[1,3,2,49],[2,3,2,50],[0,1,1,0x5d0]]);
 rows[0][0]=99;assert_eq!(s.bidi_visual("א12ב",0).unwrap()[0][0],3);assert!(s.bidi_visual("A",3).is_err());assert!(s.bidi_visual(&"A".repeat(2049),0).is_err());assert!(s.bidi_visual("",0).unwrap().is_empty());
}

#[test]
fn bidi_cluster_layout(){let s=NativeScene::new(2030).unwrap();assert_eq!(s.bidi_layout("א́ב",8,2,1).unwrap(),vec![[2,3,0,0,1,1,0x5d1],[0,2,1,0,1,1,0x5d0]]);assert!(s.bidi_layout("A",0,2,1).is_err());}

#[test]
fn bidi_caret_affinity(){let s=NativeScene::new(2030).unwrap();assert_eq!(s.bidi_hit("א́ב",8,0,0,2,1).unwrap(),3);assert_eq!(s.bidi_caret("AאבB",8,1,1,2,1).unwrap(),[3,0,1]);assert!(s.bidi_caret("א́ב",8,1,1,2,1).is_err());}
