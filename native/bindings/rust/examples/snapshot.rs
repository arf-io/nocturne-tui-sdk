use nocturne_native::NativeScene;
fn main()->Result<(),Box<dyn std::error::Error>>{let mut s=NativeScene::new(2030)?;s.command(r#"{"op":"emitter","id":1,"effect":"weather/autumn-drift","count":40}"#)?;s.advanceTo(900000)?;let f=s.render()?;std::fs::write("preview.cells",f.bytes)?;println!("{}",s.info());Ok(())}
