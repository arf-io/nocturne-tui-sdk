use nocturne_native::negotiate_shortcuts;
#[test]
fn shortcut_capabilities_reserved_conflicts_and_owned_results(){
 let candidates=[[10,113,2],[10,115,2],[20,113,2],[30,120,8]];let host=[[113,2,0],[115,2,0],[120,8,1]];
 let mut rows=negotiate_shortcuts(&[10,20,30],&candidates,&host).unwrap();assert_eq!(rows,[[10,115,2,1],[20,113,2,1],[30,0,0,0]]);
 rows[0][0]=99;assert_eq!(candidates[0][0],10);assert!(negotiate_shortcuts(&[1,1],&[],&[]).is_err());assert_eq!(negotiate_shortcuts(&[],&[],&[]).unwrap().len(),0);
}
