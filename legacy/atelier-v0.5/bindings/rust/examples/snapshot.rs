//! Render an ANSI snapshot without configuring raw mode or owning the terminal.
use nocturne_surfaces::{Key,Surface};
fn main() -> Result<(),Box<dyn std::error::Error>> {
    let mut surface=Surface::new()?;
    surface.set(Key::Width,80)?;
    surface.set(Key::Height,24)?;
    surface.set(Key::Layout,1)?;
    surface.set(Key::Effect,3)?;
    let frame=surface.render(6000,"hello from Rust")?;
    for row in frame.cells.chunks(frame.width) {
        for cell in row {
            print!("\x1b[38;2;{};{};{}m\x1b[48;2;{};{};{}m{}",
                cell.fg>>16,(cell.fg>>8)&255,cell.fg&255,
                cell.bg>>16,(cell.bg>>8)&255,cell.bg&255,
                char::from_u32(cell.glyph).unwrap_or('?'));
        }
        println!("\x1b[0m");
    }
    Ok(())
}
