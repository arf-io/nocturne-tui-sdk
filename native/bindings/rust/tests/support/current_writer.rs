use nocturne_native::NativeScene;
fn number(info:&str,key:&str)->u64 {
 let marker=format!("\"{}\":",key);let tail=info.split_once(&marker).expect("published contract field").1;
 tail.chars().take_while(|c|c.is_ascii_digit()).collect::<String>().parse().expect("numeric contract field")
}
pub fn assert_current_snapshot(scene:&mut NativeScene,bytes:&[u8]) {
 let info=scene.infoComplete().expect("complete contract");assert!(bytes.len()>=32);assert_eq!(&bytes[..8],b"NRRC4SRC");
 let word=|at:usize|u32::from_le_bytes(bytes[at..at+4].try_into().unwrap()) as u64;
 assert!(number(&info,"snapshotSchema")>0);assert_eq!(word(8),number(&info,"abiVersion"));assert_eq!(word(12),number(&info,"snapshotSchema"));assert_eq!(word(28),number(&info,"sourceSchema"));assert_eq!(bytes.len() as u64,number(&info,"snapshotCapacityBytes"));assert_eq!(word(16),bytes.len() as u64-24);
 eprintln!("validated writer schema={:x} bytes={}",word(12),bytes.len());
}
