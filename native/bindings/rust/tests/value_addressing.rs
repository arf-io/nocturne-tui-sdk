use nocturne_native::NativeScene;
#[test]
fn camera_projection_binding_and_atomic_rejection(){
 let mut s=NativeScene::new(42).unwrap();
 s.command(r#"{"op":"define","path":"/projection","value":60,"binding":{"family":"camera","field":"fov"}}"#).unwrap();
 s.command(r#"{"op":"set","path":"/projection","value":50}"#).unwrap();
 assert!(s.info().contains("\"fov\":50"));let saved=s.snapshot().unwrap();
 assert!(s.command(r#"{"op":"set","path":"/projection","value":151}"#).is_err());assert_eq!(s.snapshot().unwrap(),saved);
}

#[test]
fn hsl_lightness_uses_correct_channel(){
 let mut s=NativeScene::new(42).unwrap();
 for command in [r#"{"op":"material","id":2,"space":"hsl","channels":{"h":0,"s":1,"l":0.5},"alpha":1}"#,r#"{"op":"widget","id":1,"kind":"text","x":2,"y":2,"height":1,"text":"A","alpha":0,"material":2}"#,r#"{"op":"define","path":"/light","value":0.25,"binding":{"family":"material","id":2,"field":"lightness"}}"#]{s.command(command).unwrap();}
 let f=s.render().unwrap();let at=(2*f.width as usize+2)*16+4;assert_eq!(u32::from_le_bytes(f.bytes[at..at+4].try_into().unwrap()),0x800000);
}
