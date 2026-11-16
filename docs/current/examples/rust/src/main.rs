use nocturne_native::NativeScene;
fn main() -> Result<(), Box<dyn std::error::Error>> {
 let mut scene=NativeScene::new(2030)?;
 scene.command(include_str!("../../panel.json"))?;
 scene.advanceTo(500_000)?;
 let frame=scene.render()?;
 let checkpoint=scene.snapshot()?;
 scene.restore(&checkpoint)?;
 println!("{} {} {}",frame.width,frame.height,frame.bytes.len());
 Ok(())
}
