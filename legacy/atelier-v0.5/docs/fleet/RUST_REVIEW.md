# Rust / Volume III execution and review status

**Local execution: NOT RUN.** No Cargo/rustc binary was found. A rustup bootstrap attempt failed because `sh.rustup.rs` could not resolve from this container. Neither this review nor generated fixtures are substitutes for a successful compilation.

The new native export takes five fixed-width scalar arguments and returns one signed 32-bit value. It adds no pointers, allocations, callbacks, retained references or structs. Its declaration matches C's `uint32_t,uint32_t,int32_t,int32_t,int32_t -> int32_t`. Existing Studio config/node/cell layouts and ABI version are unchanged.

The safe Rust function rejects a negative band and a minimum outside 0..1000 before the FFI call, then converts a negative native result into the existing Error type. C arithmetic multiplies only opacity values 0..1000, so the product fits signed 32-bit. Tween inputs clamp endpoints before interpolation. Position/time boundary tests executed through native C and the other three bindings.

The generated `fleet_fixtures.rs` uses public typed StageKey/NodeKey setters, owned Strings/Vecs and no unsafe code. The two accepted scenes contain no explicit impulse records, avoiding an accidental omitted-event fixture. Their canonical FNV-1a expectations were computed from independently verified native frames; the common corpus additionally includes SHA-256 references. The 96 scalar opacity cases match the Python/Go/WASM corpus. Normal tests do not regenerate these expectations.

`fleet_ink.rs` constructs a scene with the public façade and applies opacity per text row. The core handles all pixels/cells; no Rust-only rendering algorithm was introduced. Existing FFI memory/lifetime reasoning remains documented in `../RUST_REVIEW.md`.

CI runs `cargo test --all-targets` and `cargo doc --no-deps`, including legacy and new fixtures. A release should not be called Rust-verified until that job succeeds on the target toolchain. No remote CI run was dispatched here. Native Windows/cross compilation remain unsupported by the inherited build script; macOS execution is configured but unverified locally.
