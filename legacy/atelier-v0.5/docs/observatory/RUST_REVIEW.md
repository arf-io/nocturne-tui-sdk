# Rust review: additive Observatory APIs

Cargo/rustc were unavailable in the development environment; dependency/network installation attempts did not supply them. This is a source review and a required CI path, not a claim of successful compilation.

The native converter is allocation-free. L/C/hue use signed int32; packed RGB is nonnegative and invalid input returns -1. The Rust wrapper validates/converts the result into `Result<u32,Error>`. The lightness helper operates on packed RGB. No pointers or borrowed native storage are returned by either API.

Review `bindings/rust/src/studio.rs`, the C declarations in `include/nocturne_studio.h`, and the definitions in `src/ok_color.inc` together. The existing owned frame API and Studio C layout remain unchanged. `build.rs` now observes both `ok_color.inc` and `ok_tables.inc` so changes rebuild the native object rather than leaving stale colors in a cached crate.

`tests/observatory_color.rs` reads the same 320 accepted L/C/hue→RGB fixtures exercised through Python/Go/WASM. The new example is `examples/observatory_palette.rs`. Boundary/invalid-input tests exercise negative and out-of-range values. The C ASan/UBSan test additionally swept 7,128 lightness/chroma/hue combinations and checked output ranges and lightness tolerance.

```sh
cd bindings/rust
cargo test --all-targets
cargo run --example observatory_palette
cargo doc --no-deps
```

CI installs Rust and sets REQUIRE_RUST=1. A missing toolchain fails rather than passing a skipped job. Native cross-compilation, Windows toolchains, Miri and arbitrary embedded/no-std targets are not established by this review. The higher-level Observatory model remains TypeScript; these APIs do not imply a native Rust implementation of that model.
