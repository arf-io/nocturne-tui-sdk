//! Print a constant-L OKLCh palette through the shared fixed-point C core.
use nocturne_surfaces::studio::oklchColor;
fn main(){
 for h in (0..360).step_by(6){
  let c=oklchColor(700,2000,h*1000).expect("valid fixed values");
  print!("\x1b[48;2;{};{};{}m ",c>>16,(c>>8)&255,c&255);
 }
 println!("\x1b[0m");
}
