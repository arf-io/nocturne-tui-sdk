use nocturne_native::NativeScene;
#[test]
fn cell_art_exact_color_and_purity(){
 let mut s=NativeScene::new(2030).unwrap();s.command(r#"{"op":"cell-art","id":1,"width":1,"height":1,"x":2,"y":2,"layer":"overlay","cells":[[65,16711680,255]]}"#).unwrap();
 let saved=s.snapshot().unwrap();let frame=s.render().unwrap();let at=(2*frame.width as usize+2)*16;
 for (i,value) in [65,16711680,255].iter().enumerate(){assert_eq!(u32::from_le_bytes(frame.bytes[at+i*4..at+i*4+4].try_into().unwrap()),*value);}
 assert_eq!(s.snapshot().unwrap(),saved);
}
