//! Full-document queries reuse the existing native paragraph engine.
use super::{nrGraphemeBreaks, NativeScene};
extern "C" {
    fn nrDocumentBidiClusterLayout(
        text: *const u32,
        count: u32,
        ambiguous: u32,
        columns: u32,
        direction: u32,
        out: *mut u32,
        capacity: u32,
        scratch: *mut u32,
        scratch_words: u64,
    ) -> i32;
}
fn words(count: usize, multiplier: usize) -> Result<Vec<u32>, String> {
    let size = count
        .checked_mul(multiplier)
        .ok_or("document allocation addressability")?;
    let mut v = Vec::new();
    v.try_reserve_exact(size).map_err(|e| e.to_string())?;
    v.resize(size, 0);
    Ok(v)
}
fn scalars(text: &str) -> Result<Vec<u32>, String> {
    let count = text.chars().count();
    if count > i32::MAX as usize {
        return Err("native scalar addressability".into());
    };
    let mut v = Vec::new();
    v.try_reserve_exact(count).map_err(|e| e.to_string())?;
    v.extend(text.chars().map(|c| c as u32));
    Ok(v)
}
fn edge(text: &[u32], row: &[u32; 7], end: usize) -> [u32; 3] {
    let newline = matches!(
        text[row[0] as usize],
        10 | 11 | 12 | 13 | 0x85 | 0x2028 | 0x2029
    );
    let x = if newline {
        if end == 1 {
            0
        } else {
            row[2]
        }
    } else {
        row[2]
            + if (row[5] & 1 == 1 && end == 0) || (row[5] & 1 == 0 && end == 1) {
                row[4]
            } else {
                0
            }
    };
    [x, row[3] + u32::from(end == 1 && newline), row[5]]
}
impl NativeScene {
    /// Whole-paragraph bidi layout using disjoint caller-owned growing workspace.
    pub fn document_layout(
        &self,
        text: &str,
        columns: u32,
        direction: u32,
        ambiguous: u32,
    ) -> Result<Vec<[u32; 7]>, String> {
        if direction > 2 || columns == 0 || (ambiguous != 1 && ambiguous != 2) {
            return Err("invalid document policy".into());
        };
        let source = scalars(text)?;
        let count = source.len();
        let mut output = words(count.max(1), 7)?;
        let mut scratch = words(
            count
                .checked_add(1)
                .ok_or("document allocation addressability")?,
            40,
        )?;
        let n = unsafe {
            nrDocumentBidiClusterLayout(
                source.as_ptr(),
                count as u32,
                ambiguous,
                columns,
                direction,
                output.as_mut_ptr(),
                count as u32,
                scratch.as_mut_ptr(),
                scratch.len() as u64,
            )
        };
        if n < 0 {
            return Err("invalid document layout".into());
        };
        let mut rows = Vec::new();
        rows.try_reserve_exact(n as usize)
            .map_err(|e| e.to_string())?;
        rows.extend(
            output[..n as usize * 7]
                .chunks_exact(7)
                .map(|r| [r[0], r[1], r[2], r[3], r[4], r[5], r[6]]),
        );
        Ok(rows)
    }
    /// Boundaries retain clusters hidden from visual output by bidi X9.
    pub fn document_boundaries(&self, text: &str) -> Result<Vec<u32>, String> {
        let source = scalars(text)?;
        let mut output = words(
            source
                .len()
                .checked_add(1)
                .ok_or("document allocation addressability")?,
            1,
        )?;
        let n = unsafe {
            nrGraphemeBreaks(
                source.as_ptr(),
                source.len() as u32,
                output.as_mut_ptr(),
                output.len() as u32,
            )
        };
        if n < 0 {
            return Err("invalid Unicode".into());
        };
        output.truncate(n as usize);
        Ok(output)
    }
    pub fn document_hit(
        &self,
        text: &str,
        columns: u32,
        column: u32,
        row: u32,
        direction: u32,
        ambiguous: u32,
    ) -> Result<u32, String> {
        let rows = self.document_layout(text, columns, direction, ambiguous)?;
        let source = scalars(text)?;
        let mut selected = 0;
        let mut best = (u64::MAX, u64::MAX, u32::MAX);
        for value in rows {
            for end in 0..2 {
                let e = edge(&source, &value, end);
                let key = (
                    u64::from(e[1].abs_diff(row)),
                    u64::from(e[0].abs_diff(column)),
                    u32::MAX - value[end],
                );
                if key < best {
                    best = key;
                    selected = value[end];
                }
            }
        }
        Ok(selected)
    }
    pub fn document_caret(
        &self,
        text: &str,
        columns: u32,
        offset: u32,
        affinity: u32,
        direction: u32,
        ambiguous: u32,
    ) -> Result<[u32; 3], String> {
        let rows = self.document_layout(text, columns, direction, ambiguous)?;
        if affinity > 1 || !self.document_boundaries(text)?.contains(&offset) {
            return Err("invalid caret offset or affinity".into());
        };
        let source = scalars(text)?;
        let mut chosen = [0, 0, u32::from(direction == 1)];
        let mut found = false;
        for value in &rows {
            for end in 0..2 {
                if value[end] == offset {
                    chosen = edge(&source, value, end);
                    found = true;
                    if end == usize::from(affinity == 0) {
                        return Ok(chosen);
                    }
                }
            }
        }
        if !rows.is_empty() && !found {
            return Err("invalid Unicode or caret boundary".into());
        };
        Ok(chosen)
    }
}
