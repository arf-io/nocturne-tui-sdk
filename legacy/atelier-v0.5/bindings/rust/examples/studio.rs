//! Snapshot host. Application frameworks should draw Frame.cells into their buffer.
use nocturne_surfaces::studio::{Studio,StageKey,Node,NodeKind,NodeKey,Impulse};
use std::io::{self,Write};
fn main()->Result<(),Box<dyn std::error::Error>>{
 let mut studio=Studio::new()?;studio.set(StageKey::Width,80)?;studio.set(StageKey::Height,24)?;studio.set(StageKey::Pattern,3)?;studio.set(StageKey::FocusMode,1)?;studio.set(StageKey::FocusY,12*256)?;
 let mut node=Node::new(NodeKind::Progress,5,12,65,2)?;node.set(NodeKey::Value,670);node.set(NodeKey::ColorAnimation,2);
 let frame=studio.render(2500,&[node],&[Impulse::ripple(20,12,1700)?])?;let mut out=io::BufWriter::new(io::stdout().lock());
 for y in 0..frame.height{write!(out,"\x1b[{};1H",y+1)?;for c in &frame.cells[y*frame.width..(y+1)*frame.width]{write!(out,"\x1b[38;2;{};{};{}m\x1b[48;2;{};{};{}m{}",c.fg>>16,c.fg>>8&255,c.fg&255,c.bg>>16,c.bg>>8&255,c.bg&255,char::from_u32(c.glyph).unwrap_or('?'))?;}}
 writeln!(out,"\x1b[0m")?;out.flush()?;Ok(())
}
