# Rust façade review

**Source reviewed; compilation and Rust tests NOT RUN locally.** No cargo/rustc existed in the runtime, and toolchain retrieval attempts failed. The C renderer compiled/tested independently; that does not prove the Rust binding compiles.

## Checks performed

1. `repr(C)` integer records have expected sizes704/128/32/16bytes. `Studio::new()` checks ABI version and sizes. C repeats content validation before drawing.
2. FFI calls are synchronous; no pointers survive calls. Owned packed vectors and output storage remain live and aligned. Empty vectors are never dereferenced at count zero.
3. Scene counts are bounded before narrowing. Private config keeps dimensions≤512×256; output allocation has≤131072cells. Rust strings become valid Unicode scalars; the native glyph profile still narrows supported rendering.
4. Numeric data is bounded±1,000,000. Private node/config words and typed enum keys prevent arbitrary indexing. Range-invalid setters do not commit.
5. u64 timestamps split/reassemble unsigned bit patterns, not signed time arithmetic. Common fixtures fit JavaScript's safe-integer range.
6. Hit results are decoded after successful native validation, with bounded indexes. Positive stable IDs are host-owned semantics.
7. The legacy Frame exposes fields, so the Studio compositor checks dimensions AND exact cell count. Destination cloning prevents overlapping source/destination native buffers. Offset/alpha limits are native-validated.
8. Tween validates easing. Native widened arithmetic handles extreme scalar values; C sanitizer checks exercise boundary arithmetic.
9. Native render calls are reentrant; Rust does not use the WASM scratch exports. Immutable rendering obeys normal ownership; application mutation still needs synchronization.
10. `build.rs` invokes cc/ar directly, checks statuses, tracks every included header/source, and rejects unsupported cross-target/Windows builds. No Cargo build dependencies are hidden.
11. Existing crate Error/Frame API use, edition2021 syntax and generated enum/range lengths were checked manually. Generated includes have ordinary comment headers, avoiding misplaced inner doc comments.

## Supplied executable checks

Six Studio unit tests cover owned replay, all kinds, disabled hit blocking, invalid/empty geometry, compositor/tween and immediate data/impulses. Generated integration source evaluates **72 fixed reference frames** from the same accepted Python/Go/WASM corpus. Existing v1 tests/examples remain.

```sh
cd bindings/rust
cargo test --all-targets
cargo doc --no-deps
cargo run --example studio
```

`REQUIRE_RUST=1 sh scripts/check_studio.sh` fails if Cargo is missing. Linux CI installs stable Rust and runs tests/docs; macOS CI runs all targets. Neither workflow executed remotely here. `dist/studio/rust-tests.txt` explicitly says NOT RUN.

Compiler/platform/version issues remain possible until actual execution. Native Windows, cross compilation, independent Cargo publishing and framework adapters require separate work. Copying only bindings/rust loses the sibling C source. Manual review does not replace compiling and running these tests.
