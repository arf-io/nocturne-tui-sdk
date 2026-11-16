//! Real C-ABI selector parity, with no new crate dependency or selector implementation.
#![allow(non_snake_case)]
use nocturne_native::NativeScene;

const UNRELATED: &str = r#"{"id":1,"event":"/parity/unrelated","messageId":40,"actionId":3,"messageSequence":1,"atUs":100000,"value":7}"#;
const MATCHING: &str = r#"{"id":2,"event":"/parity/approved","messageId":600,"actionId":9,"messageSequence":2,"atUs":200000,"value":7}"#;

// The binding deliberately returns JSON text without serde. These helpers only
// delimit metadata values; they never select an intent or evaluate a condition.
// Scoping a field to its containing object prevents nested source fields from
// accidentally satisfying assertions about the trigger itself.
fn valueEnd(text: &str) -> usize {
    let mut depth = 0;
    let mut quoted = false;
    let mut escaped = false;
    for (index, byte) in text.bytes().enumerate() {
        if quoted {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                quoted = false;
                if depth == 0 {
                    return index + 1;
                }
            }
            continue;
        }
        match byte {
            b'"' => quoted = true,
            b'{' | b'[' => depth += 1,
            b'}' | b']' => {
                if depth == 0 {
                    return index;
                }
                depth -= 1;
                if depth == 0 {
                    return index + 1;
                }
            }
            b',' if depth == 0 => return index,
            _ => {}
        }
    }
    assert!(!quoted && depth == 0, "incomplete metadata: {text}");
    text.len()
}

fn field<'a>(object: &'a str, name: &str) -> &'a str {
    let mut rest = object
        .trim()
        .strip_prefix('{')
        .expect("metadata object")
        .trim_start();
    let key = format!("\"{name}\"");
    while !rest.starts_with('}') {
        assert!(rest.starts_with('"'), "metadata key: {rest}");
        let end = valueEnd(rest);
        let foundKey = &rest[..end];
        rest = rest[end..]
            .trim_start()
            .strip_prefix(':')
            .expect("metadata colon")
            .trim_start();
        let end = valueEnd(rest);
        assert!(end > 0, "missing metadata value");
        let value = rest[..end].trim_end();
        if foundKey == key {
            return value;
        }
        rest = rest[end..].trim_start();
        if rest.starts_with('}') {
            break;
        }
        rest = rest
            .strip_prefix(',')
            .expect("metadata separator")
            .trim_start();
    }
    panic!("missing metadata field {name}: {object}");
}

fn items(array: &str) -> Vec<&str> {
    let mut rest = array
        .trim()
        .strip_prefix('[')
        .expect("metadata array")
        .trim_start();
    let mut values = Vec::new();
    while !rest.starts_with(']') {
        let end = valueEnd(rest);
        assert!(end > 0, "missing array element");
        values.push(rest[..end].trim_end());
        rest = rest[end..].trim_start();
        if !rest.starts_with(']') {
            rest = rest
                .strip_prefix(',')
                .expect("array separator")
                .trim_start();
        }
    }
    assert_eq!(rest, "]", "unexpected trailing array data");
    values
}

fn checkIntent(actual: &str, expected: &str) {
    for name in [
        "id",
        "event",
        "messageId",
        "actionId",
        "messageSequence",
        "atUs",
    ] {
        assert_eq!(field(actual, name), field(expected, name), "intent {name}");
    }
    // Numeric JSON spelling is not provenance: C writes 7.000000, WASM may write 7.
    assert_eq!(numberField(actual, "value"), numberField(expected, "value"));
}

fn numberField(object: &str, name: &str) -> f64 {
    field(object, name).parse().expect("numeric metadata value")
}

fn checkState(scene: &mut NativeScene, fired: bool) {
    let info = scene.info();
    let queue = items(field(&info, "intents"));
    assert_eq!(
        queue.len(),
        2,
        "neither intent may be implicitly acknowledged"
    );
    checkIntent(queue[0], UNRELATED);
    checkIntent(queue[1], MATCHING);
    let rules = items(field(&info, "triggers"));
    assert_eq!(rules.len(), 1);
    let rule = rules[0];
    assert_eq!(field(rule, "id"), "11");
    assert_eq!(field(rule, "conditionNodes"), "3");
    assert_eq!(field(rule, "event"), r#""/parity/approved""#);
    assert_eq!(field(rule, "valueSource"), r#""constant""#);
    assert_eq!(field(rule, "pendingIntent"), "0");
    let values = field(&info, "values");
    assert_eq!(
        numberField(values, "/parity/enabled"),
        if fired { 1.0 } else { 0.0 }
    );
    // Constant increment 3 is distinct from copying or adding payload value 7.
    assert_eq!(
        numberField(values, "/parity/out"),
        if fired { 13.0 } else { 10.0 }
    );
    assert_eq!(field(rule, "fireCount"), if fired { "1" } else { "0" });
    assert_eq!(field(rule, "lastIntent"), if fired { "2" } else { "0" });
    assert_eq!(
        field(rule, "lastFireUs"),
        if fired { "300000" } else { "0" }
    );
    if fired {
        assert_eq!(field(rule, "intentCandidate"), "null");
        checkIntent(field(rule, "lastIntentSource"), MATCHING);
    } else {
        checkIntent(field(rule, "intentCandidate"), MATCHING);
        assert_eq!(field(rule, "lastIntentSource"), "null");
    }
}

fn checkPure(scene: &mut NativeScene, fired: bool) -> Result<(), String> {
    let before = scene.snapshot()?;
    for _ in 0..3 {
        checkState(scene, fired);
        assert_eq!(
            before,
            scene.snapshot()?,
            "info mutated authoritative state"
        );
        assert!(!scene.render()?.bytes.is_empty());
        assert_eq!(
            before,
            scene.snapshot()?,
            "render mutated authoritative state"
        );
    }
    checkState(scene, fired);
    Ok(())
}

#[test]
fn intentValueSelectorUsesOldestMatchingRetainedIntent() -> Result<(), String> {
    let mut scene = NativeScene::new(2030)?;
    scene.command(r#"{"op":"define","path":"/parity/enabled","value":0}"#)?;
    scene.command(r#"{"op":"define","path":"/parity/out","value":10}"#)?;
    scene.command(r#"{"op":"trigger","id":11,"event":"/parity/approved","when":{"all":[{"path":"/parity/enabled","comparison":"equal","value":1},{"intentValue":{"comparison":"at-least","value":7}}]},"target":"/parity/out","action":"increment","value":3}"#)?;
    let initial = scene.info();
    let rules = items(field(&initial, "triggers"));
    assert_eq!(rules.len(), 1);
    assert_eq!(field(rules[0], "intentCandidate"), "null");
    assert!(items(field(&initial, "intents")).is_empty());
    scene.advanceTo(100000)?;
    scene.command(r#"{"op":"status","id":40,"area":0,"text":"Unrelated","durationMs":0,"actions":[{"id":3,"label":"Confirm","event":"/parity/unrelated","value":7}]}"#)?;
    scene.command(r#"{"op":"notification-action","id":40,"actionId":3}"#)?;
    scene.advanceTo(200000)?;
    scene.command(r#"{"op":"status","id":600,"area":0,"text":"Matching","durationMs":0,"actions":[{"id":9,"label":"Confirm","event":"/parity/approved","value":7}]}"#)?;
    scene.command(r#"{"op":"notification-action","id":600,"actionId":9}"#)?;
    checkPure(&mut scene, false)?;
    scene.advanceTo(300000)?;
    checkPure(&mut scene, false)?;
    scene.command(r#"{"op":"set","path":"/parity/enabled","value":1}"#)?;
    checkPure(&mut scene, true)?;
    scene.command(r#"{"op":"set","path":"/parity/enabled","value":1}"#)?;
    scene.advanceTo(400000)?;
    checkPure(&mut scene, true)?;
    Ok(())
}
