//! Deterministic terminal-cell materials. No terminal I/O and no internal clock.
//! The C kernel is compiled by build.rs. This facade has no Cargo dependencies.
#![allow(non_snake_case)]
use std::{error::Error as StdError, fmt};
mod keys;
pub use keys::Key;

/// One terminal cell: Unicode scalar, packed foreground/background RGB, flags.
#[repr(C)]
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Cell { pub glyph: u32, pub fg: u32, pub bg: u32, pub flags: u32 }

#[repr(C)]
#[derive(Clone)]
struct Config {
    values: [i32; 64],
    palette: [u32; 8],
    starPalette: [u32; 8],
    glyphs: [u32; 32],
}

extern "C" {
    fn nsDefaultConfig(config: *mut Config);
    fn nsAbiVersion() -> u32;
    fn nsConfigSize() -> u32;
    fn nsCellSize() -> u32;
    fn nsRender(config: *const Config, motionMs: u64, text: *const u32,
        textLength: u32, cells: *mut Cell, capacity: u32) -> i32;
}

/// Configuration, ABI, or render failure. No partial frame is returned.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Error(pub String);
impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { fmt::Display::fmt(&self.0, f) }
}
impl StdError for Error {}

/// Owned row-major cells. Existing frames are not changed by later renders.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Frame { pub width: usize, pub height: usize, pub cells: Vec<Cell> }
impl Frame {
    /// Produce canonical little-endian bytes for hashing or replay fixtures.
    /// Inputs: none. Output: 16 bytes per cell. Errors: allocation failure follows
    /// the Rust allocator's normal behavior. Example: `let bytes = frame.toBytes();`
    pub fn toBytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(self.cells.len() * 16);
        for cell in &self.cells {
            for word in [cell.glyph, cell.fg, cell.bg, cell.flags] {
                bytes.extend_from_slice(&word.to_le_bytes());
            }
        }
        bytes
    }
}

/// A mutable configuration with a pure render operation.
#[derive(Clone)]
pub struct Surface { config: Config }
impl Surface {
    /// Create native defaults and check the linked ABI. Returns an error for a
    /// version/layout mismatch. Example: `let surface = Surface::new()?;`
    pub fn new() -> Result<Self, Error> {
        let mut config = Config { values: [0; 64], palette: [0; 8], starPalette: [0; 8], glyphs: [0; 32] };
        // SAFETY: C functions use no retained pointers. Config has the declared C layout.
        unsafe {
            if nsAbiVersion() != 1 || nsConfigSize() as usize != std::mem::size_of::<Config>()
                || nsCellSize() as usize != std::mem::size_of::<Cell>() {
                return Err(Error("Nocturne ABI mismatch".into()));
            }
            nsDefaultConfig(&mut config);
        }
        Ok(Self { config })
    }

    /// Set an integer property, with validation before mutation. Returns an error
    /// for out-of-range values. Example: `surface.set(Key::Width, 100)?;`
    pub fn set(&mut self, key: Key, value: i32) -> Result<(), Error> {
        let index = key as usize;
        let (minimum, maximum) = keys::RANGES[index];
        if value < minimum || value > maximum {
            return Err(Error(format!("{key:?}: expected {minimum}..{maximum}")));
        }
        self.config.values[index] = value;
        Ok(())
    }

    /// Set 1..8 gradient colors, each packed 0xRRGGBB. Invalid colors or lengths
    /// return an error without mutation. Example: `surface.setPalette(&[0x654f72,0x356a6a])?;`
    pub fn setPalette(&mut self, colors: &[u32]) -> Result<(), Error> {
        Self::validatePalette(colors)?;
        self.config.palette[..colors.len()].copy_from_slice(colors);
        self.set(Key::PaletteCount, colors.len() as i32)
    }

    /// Set 1..8 peak star colors, packed 0xRRGGBB. Returns an error on invalid input.
    /// Example: `surface.setStarPalette(&[0xb6a4c4,0x9fb9b0])?;`
    pub fn setStarPalette(&mut self, colors: &[u32]) -> Result<(), Error> {
        Self::validatePalette(colors)?;
        self.config.starPalette[..colors.len()].copy_from_slice(colors);
        self.set(Key::StarPaletteCount, colors.len() as i32)
    }

    fn validatePalette(colors: &[u32]) -> Result<(), Error> {
        if colors.is_empty() || colors.len() > 8 || colors.iter().any(|c| *c > 0xffffff) {
            return Err(Error("Expected 1..8 packed RGB colors".into()));
        }
        Ok(())
    }

    /// Set 1..32 custom star characters. The demo kernel substitutes unsupported
    /// or unsafe glyphs. Returns an error for an invalid length.
    /// Example: `surface.setGlyphs(&['.', '·', '⠁'])?;`
    pub fn setGlyphs(&mut self, glyphs: &[char]) -> Result<(), Error> {
        if glyphs.is_empty() || glyphs.len() > 32 {
            return Err(Error("Expected 1..32 custom characters".into()));
        }
        for (index, glyph) in glyphs.iter().enumerate() { self.config.glyphs[index] = *glyph as u32; }
        self.set(Key::GlyphCount, glyphs.len() as i32)?;
        self.set(Key::GlyphSet, 4)
    }

    /// Render cells at explicit integer milliseconds. Text and data may change at
    /// the same timestamp, independently of the host's decorative motion clock.
    /// Text is limited to 512 code points. Returns an error on invalid text length
    /// or a native renderer failure. Example: `let frame=surface.render(5000,"now")?;`
    pub fn render(&self, motionMs: u64, text: &str) -> Result<Frame, Error> {
        let points: Vec<u32> = text.chars().map(|c| c as u32).collect();
        if points.len() > 512 { return Err(Error("Text exceeds 512 code points".into())); }
        let width = self.config.values[Key::Width as usize] as usize;
        let height = self.config.values[Key::Height as usize] as usize;
        let mut cells = vec![Cell::default(); width * height];
        // SAFETY: buffers are live, correctly aligned, non-overlapping, sized by
        // validated dimensions, and retained only for this synchronous call.
        let count = unsafe {
            nsRender(&self.config, motionMs, points.as_ptr(), points.len() as u32,
                cells.as_mut_ptr(), cells.len() as u32)
        };
        if count < 0 { return Err(Error(format!("Renderer error {count}"))); }
        Ok(Frame { width, height, cells })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn replayIsStable() {
        let mut surface = Surface::new().unwrap();
        surface.set(Key::Effect,5).unwrap();
        let frame = surface.render(5000,"same").unwrap();
        let _ = surface.render(77000,"other").unwrap();
        assert_eq!(frame,surface.render(5000,"same").unwrap());
    }
    #[test]
    fn invalidDimensionsFail() {
        let mut surface = Surface::new().unwrap();
        assert!(surface.set(Key::Width,-1).is_err());
        assert!(surface.set(Key::Width,513).is_err());
    }
    #[test]
    fn dataUpdatesWithFrozenMotion() {
        let mut surface = Surface::new().unwrap();
        surface.set(Key::Layout,1).unwrap();
        assert_ne!(surface.render(6000,"a").unwrap(),surface.render(6000,"b").unwrap());
    }
    #[test]
    fn emptySurfaceIsValid() {
        let mut surface = Surface::new().unwrap();
        surface.set(Key::Width,0).unwrap();
        assert!(surface.render(0,"").unwrap().cells.is_empty());
    }
}

/// Additive material, scene, hit-test, and composition API.
pub mod studio;
