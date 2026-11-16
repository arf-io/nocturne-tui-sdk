//! Small standard-library-only serialization helpers for the qualification fixture.
#![allow(non_snake_case)]

/// Encode one string as JSON, escaping quotes, slashes and all U+0000..001F controls.
/// Input is retained UTF-8; output is one quoted JSON string. No normalization occurs.
/// Example: jsonString("é\n") returns a quoted string with an escaped newline.
pub fn jsonString(value: &str) -> String {
    let mut out = String::from("\"");
    for ch in value.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            ch if ch <= '\u{1f}' => out.push_str(&format!("\\u{:04x}", ch as u32)),
            ch => out.push(ch),
        }
    }
    out.push('"');
    out
}

/// Construct an input transaction without interpreting user text as JSON syntax.
/// NativeScene remains responsible for capacity and command validation.
pub fn inputCommand(text: &str) -> String {
    format!("{{\"op\":\"input\",\"text\":{}}}", jsonString(text))
}

/// Data-only paste respects authoritative modal/reader/Vim ownership in C.
pub fn pasteCommand(text: &str) -> String {
    format!("{{\"op\":\"paste\",\"text\":{}}}", jsonString(text))
}

/// Construct an explicit native key transaction; unsupported keys reject in C.
pub fn keyCommand(key: &str, ctrl: bool, shift: bool, alt: bool) -> String {
    format!(
        "{{\"op\":\"key\",\"key\":{},\"ctrl\":{ctrl},\"shift\":{shift},\"alt\":{alt}}}",
        jsonString(key)
    )
}

/// Return an FNV-1a diagnostic fingerprint of copied frame bytes, not a security hash.
/// Artifact/command provenance is separately recorded with SHA-256 by the Python gate.
pub fn frameHash(bytes: &[u8]) -> u64 {
    bytes.iter().fold(0xcbf29ce484222325u64, |hash, byte| {
        (hash ^ u64::from(*byte)).wrapping_mul(0x100000001b3)
    })
}

/// Author a native resize only when the clamped viewport changes.
/// Reissuing resize clears native hover/pressed ownership, so paint alone must not do it.
/// Returns one JSON command or None; previous records the fixture's submitted size.
pub fn resizeCommand(width: u16, height: u16, previous: &mut Option<(u16, u16)>) -> Option<String> {
    let current = (width.max(1), height.max(1));
    if *previous == Some(current) {
        return None;
    }
    *previous = Some(current);
    Some(format!(
        "{{\"op\":\"resize\",\"width\":{},\"height\":{}}}",
        current.0, current.1
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quoteEscapesEveryJsonControl() {
        assert_eq!(
            jsonString("\"\\\n\r\t\u{8}\u{c}\0"),
            "\"\\\"\\\\\\n\\r\\t\\u0008\\u000c\\u0000\""
        );
    }

    #[test]
    fn quotePreservesUnicodeWithoutSlicingBytes() {
        assert_eq!(jsonString("é ⣿ 界 👩"), "\"é ⣿ 界 👩\"");
        assert_eq!(jsonString(""), "\"\"");
    }

    #[test]
    fn textCannotEscapeItsCommand() {
        assert_eq!(
            inputCommand("\"},\"op\":\"reset"),
            "{\"op\":\"input\",\"text\":\"\\\"},\\\"op\\\":\\\"reset\"}"
        );
    }

    #[test]
    fn keyIncludesExplicitModifierBooleans() {
        assert_eq!(
            keyCommand("Home", true, false, true),
            "{\"op\":\"key\",\"key\":\"Home\",\"ctrl\":true,\"shift\":false,\"alt\":true}"
        );
    }

    #[test]
    fn unchangedViewportDoesNotClearNativePointerStateWithAnotherResize() {
        let mut previous = None;
        assert!(resizeCommand(80, 24, &mut previous).is_some());
        assert!(resizeCommand(80, 24, &mut previous).is_none());
        assert_eq!(
            resizeCommand(100, 30, &mut previous),
            Some("{\"op\":\"resize\",\"width\":100,\"height\":30}".to_string())
        );
        assert!(resizeCommand(100, 30, &mut previous).is_none());
    }

    #[test]
    fn viewportPreservesTinyAndLargeTerminalDimensions() {
        let mut previous = None;
        assert_eq!(
            resizeCommand(1, 1, &mut previous),
            Some("{\"op\":\"resize\",\"width\":1,\"height\":1}".to_string())
        );
        assert_eq!(
            resizeCommand(65535, 65535, &mut previous),
            Some("{\"op\":\"resize\",\"width\":65535,\"height\":65535}".to_string())
        );
    }

    #[test]
    fn fingerprintDependsOnEveryByteAndOrder() {
        assert_eq!(frameHash(&[]), 0xcbf29ce484222325);
        assert_ne!(frameHash(&[1, 2]), frameHash(&[2, 1]));
        assert_ne!(frameHash(&[1]), frameHash(&[1, 0]));
    }
}

pub fn clipboardCommand(scene:&nocturne_native::NativeScene,buffer:&mut String,action:&str)->Result<Option<String>,String>{
    if action=="paste"{return Ok(if buffer.is_empty(){None}else{Some(pasteCommand(buffer))});}
    let Some(text)=scene.selected_text()? else{return Ok(None)};
    *buffer=text;
    Ok(if action=="cut"{Some(keyCommand("Delete",false,false,false))}else{None})
}
