//! Same 320 accepted scalar colors as Python, Go and WASM, no extra dependencies.
use nocturne_surfaces::studio::{oklchColor,oklchLightness};
#[test]
fn shared_color_corpus(){
 let corpus=include_str!("../../../tests/observatory/color-fixtures.csv");
 for line in corpus.lines().skip(1){
  let v:Vec<i32>=line.split(',').map(|x|x.parse().expect("numeric fixture")).collect();
  let color=oklchColor(v[0],v[1],v[2]).expect("valid fixture");
  assert_eq!(color,v[3] as u32,"{}",line);
  assert_eq!(oklchLightness(color).unwrap(),v[4]);
 }
}
