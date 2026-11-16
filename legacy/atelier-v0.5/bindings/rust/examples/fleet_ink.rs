//! Host-neutral text arrival and horizon fade using the shared integer helper.
use nocturne_surfaces::studio::{Studio,StageKey,Node,NodeKind,NodeKey,fleetInkOpacity};
fn main()->Result<(),Box<dyn std::error::Error>>{
 let mut stage=Studio::new()?;
 stage.set(StageKey::Width,80)?;stage.set(StageKey::Height,24)?;
 let mut nodes=Vec::new();
 for row in 0..10 {
  let mut text=Node::new(NodeKind::Text,3,4+row,70,1)?;
  text.text=format!("Agent message / row {row} / arrival + gentle top fade");
  text.set(NodeKey::FgOpacity,fleetInkOpacity(520,520,row*256,6*256,760)?);
  nodes.push(text);
 }
 let frame=stage.render(2000,&nodes,&[])?;
 println!("Rendered {} owned cells. Place them in your host's buffer.",frame.cells.len());
 Ok(())
}
