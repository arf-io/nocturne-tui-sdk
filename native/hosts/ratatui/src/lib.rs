//! Presentation-only adapter. The application owns NativeScene, time and input.
//! Dependency-backed contracts are in tests/adapter_contract.rs.
use nocturne_native::Frame as NativeFrame;
use ratatui::{buffer::Buffer, layout::Rect, style::Color, widgets::Widget};
use unicode_width::UnicodeWidthChar;

/// Blits an owned canonical native frame without sampling or advancing the scene.
/// Unsupported terminal-width scalars display U+FFFD; `frame.bytes` remains intact.
pub struct SceneCells<'a> {
    pub frame: &'a NativeFrame,
}
impl Widget for SceneCells<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        // Preserve the source origin while clipping writes to the actual destination.
        let target = Rect::new(
            area.x,
            area.y,
            u32::from(area.width).min(self.frame.width) as u16,
            u32::from(area.height).min(self.frame.height) as u16,
        )
        .intersection(buf.area);
        for y in target.y..target.bottom() {
            for x in target.x..target.right() {
                // Frame is caller-constructible. Widen before multiplication so a malformed
                // stride cannot wrap into valid-looking bytes or panic in a debug build.
                let cellIndex =
                    u64::from(y - area.y) * u64::from(self.frame.width) + u64::from(x - area.x);
                let Ok(offset) = usize::try_from(cellIndex * 16) else {
                    return;
                };
                let Some(end) = offset.checked_add(16) else {
                    return;
                };
                let Some(bytes) = self.frame.bytes.get(offset..end) else {
                    return;
                };
                let word = |n: usize| u32::from_le_bytes(bytes[n..n + 4].try_into().unwrap());
                let symbol = char::from_u32(word(0))
                    .filter(|c| !c.is_control() && c.width() == Some(1))
                    .unwrap_or('\u{fffd}');
                let rgb = |v: u32| Color::Rgb((v >> 16) as u8, (v >> 8) as u8, v as u8);
                let mut encoded = [0u8; 4];
                buf[(x, y)]
                    .set_symbol(symbol.encode_utf8(&mut encoded))
                    .set_fg(rgb(word(4)))
                    .set_bg(rgb(word(8)));
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn glyph_color_and_ownership() {
        let bytes = [b'A' as u32, 0xabcdef, 0x112233, 7]
            .iter()
            .flat_map(|x| x.to_le_bytes())
            .collect();
        let native = NativeFrame {
            width: 1,
            height: 1,
            bytes,
        };
        let before = native.clone();
        let area = Rect::new(2, 3, 1, 1);
        let mut buf = Buffer::empty(area);
        SceneCells { frame: &native }.render(area, &mut buf);
        assert_eq!(buf[(2, 3)].symbol(), "A");
        assert_eq!(buf[(2, 3)].fg, Color::Rgb(0xab, 0xcd, 0xef));
        assert_eq!(native, before);
    }
}

/// Owned presentation of retained prompt source. Unicode decisions remain native.
#[derive(Debug, Clone)]
pub struct DocumentCell {
    pub column: u32,
    pub row: u32,
    pub width: u32,
    pub source: [u32; 2],
    pub symbol: String,
    pub selected: bool,
}
#[derive(Debug, Clone)]
pub struct DocumentFrame {
    pub cells: Vec<DocumentCell>,
    pub columns: u32,
    pub rows: u32,
}
impl Widget for &DocumentFrame {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let target=area.intersection(buf.area);
        for cell in &self.cells {
            let x=u32::from(area.x)+cell.column;
            let y=u32::from(area.y)+cell.row;
            if cell.width==0 || x<u32::from(target.x) || y<u32::from(target.y)
                || x+cell.width>u32::from(target.right()) || y>=u32::from(target.bottom()) {continue}
            buf[(x as u16,y as u16)].set_symbol(&cell.symbol)
                .set_fg(Color::Rgb(228,218,204))
                .set_bg(if cell.selected {Color::Rgb(67,99,127)} else {Color::Rgb(11,18,27)});
            for continuation in 1..cell.width {
                buf[((x+continuation) as u16,y as u16)].reset();
            }
        }
    }
}
/// Viewport state is host-owned and never written into the native document.
pub struct UnicodeDocument {
    pub scroll: u32,
    pub max_scroll: u32,
    columns: u32,
    rows: u32,
 preferred:Option<u32>,
 last_caret:Option<(String,u32,u32,u32)>,
}
impl Default for UnicodeDocument {fn default()->Self {Self::new()}}
impl UnicodeDocument {
    pub fn new()->Self {Self{scroll:0,max_scroll:0,columns:1,rows:1,preferred:None,last_caret:None}}
    pub fn presentation(&mut self,scene:&nocturne_native::NativeScene,columns:u32,rows:u32,selection:Option<[u32;2]>)->Result<DocumentFrame,String> {
        self.columns=columns.max(1);self.rows=rows.saturating_sub(1);
        let text=scene.text_run_source(0,0)?;
        let scalars:Vec<char>=text.chars().collect();
        let layout=scene.document_layout(&text,self.columns,2,1)?;
        let bottom=layout.iter().map(|r|r[3]).max().unwrap_or(0);
        self.max_scroll=bottom.saturating_add(1).saturating_sub(self.rows);
        self.scroll=self.scroll.min(self.max_scroll);
        let mut cells=Vec::new();
        for r in layout {
            if r[3]<self.scroll || r[3]-self.scroll>=self.rows || r[4]==0 || r[2]+r[4]>self.columns {continue}
            let mut cluster=scalars[r[0] as usize..r[1] as usize].to_vec();
            if let Some(first)=cluster.first_mut(){*first=char::from_u32(r[6]).ok_or("invalid native mirror")?}
            let symbol=if cluster.first()==Some(&'\t'){" ".repeat(r[4] as usize)}else{cluster.into_iter().filter(|c|!c.is_control()).collect()};
            let selected=selection.is_some_and(|[a,b]|r[0]<a.max(b)&&r[1]>a.min(b));
            cells.push(DocumentCell{column:r[2],row:r[3]-self.scroll+1,width:r[4],source:[r[0],r[1]],symbol,selected});
        }
        Ok(DocumentFrame{cells,columns:self.columns,rows})
    }
    pub fn hit(&self,scene:&nocturne_native::NativeScene,column:u32,row:u32)->Result<u32,String> {
        if row==0{return Err("document header has no source offset".into())}
        let text=scene.text_run_source(0,0)?;
        scene.document_hit(&text,self.columns,column,row.saturating_sub(1).saturating_add(self.scroll),2,1)
    }
    pub fn scroll_by(&mut self,delta:i32) {
        self.scroll=(i64::from(self.scroll)+i64::from(delta)).clamp(0,i64::from(self.max_scroll)) as u32;
    }
}

impl UnicodeDocument {
    fn caret(&self,scene:&nocturne_native::NativeScene,text:&str,offset:u32)->Result<[u32;3],String>{
        let boundary=scene.document_boundaries(text)?.into_iter().filter(|b|*b<=offset).max().unwrap_or(0);
        scene.document_caret(text,self.columns,boundary,1,2,1)
    }
    pub fn follow_caret(&mut self,scene:&nocturne_native::NativeScene,offset:u32)->Result<(),String>{
        let text=scene.text_run_source(0,0)?;
        let signature=(text.clone(),offset,self.columns,self.rows);
        if self.last_caret.as_ref()==Some(&signature){return Ok(())}
        if self.last_caret.as_ref().is_some_and(|last|last.0!=text){self.preferred=None}
        let y=self.caret(scene,&text,offset)?[1];
        self.max_scroll=self.max_scroll.max(y.saturating_add(1).saturating_sub(self.rows));
        if y<self.scroll{self.scroll=y}else if y>=self.scroll.saturating_add(self.rows.max(1)){self.scroll=y.saturating_add(1).saturating_sub(self.rows.max(1))}
        self.scroll=self.scroll.min(self.max_scroll);self.last_caret=Some(signature);Ok(())
    }
    pub fn reset_column(&mut self){self.preferred=None}
    pub fn move_offset(&mut self,scene:&nocturne_native::NativeScene,offset:u32,key:&str)->Result<u32,String>{
        let text=scene.text_run_source(0,0)?;let c=self.caret(scene,&text,offset)?;
        let(mut x,mut y)=(i64::from(c[0]),i64::from(c[1]));
        match key {
            "ArrowUp"|"ArrowDown"|"PageUp"|"PageDown"=>{
                x=i64::from(*self.preferred.get_or_insert(c[0]));
                let step=if key.starts_with("Page"){i64::from(self.rows.max(1))}else{1};
                y+=if key.ends_with("Up"){-step}else{step};
            },
            "ArrowLeft"=>{self.preferred=None;x-=1},"ArrowRight"=>{self.preferred=None;x+=1},
            "Home"=>{self.preferred=None;x=0},"End"=>{self.preferred=None;x=i64::from(self.columns)},
            _=>return Err("unsupported visual movement".into()),
        }
        scene.document_hit(&text,self.columns,x.max(0) as u32,y.max(0) as u32,2,1)
    }
}

pub mod shortcuts;

pub mod text_anchor;
