#!/usr/bin/env sh
# Full core regression + Studio acceptance. No fixture generation or network.
# Set REQUIRE_RUST=1 in CI so a missing Rust toolchain FAILS, never silently skips.
set -eu
cd "$(dirname "$0")/.."
mkdir -p dist/studio
sh scripts/check.sh >dist/studio/core-tests.txt 2>&1 || { cat dist/studio/core-tests.txt; exit 1; }
cat dist/studio/core-tests.txt
node tests/studio-parity.mjs >dist/studio/wasm-tests.json
cat dist/studio/wasm-tests.json
"${CC:-cc}" -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -Iinclude tests/studio_safety.c -o /tmp/nocturne-studio-safety
/tmp/nocturne-studio-safety >dist/studio/sanitizers.txt
cat dist/studio/sanitizers.txt
if command -v cargo >/dev/null 2>&1; then
 (cd bindings/rust && cargo test --all-targets && cargo doc --no-deps) >dist/studio/rust-tests.txt 2>&1 || { cat dist/studio/rust-tests.txt; exit 1; }
 cat dist/studio/rust-tests.txt
else
 printf 'NOT RUN: cargo/rustc unavailable. Review docs/RUST_REVIEW.md. CI requires Rust.\n' | tee dist/studio/rust-tests.txt
 if [ "${REQUIRE_RUST:-0}" = "1" ]; then exit 1; fi
fi
python3 scripts/build_studio_gallery.py
python3 scripts/check_studio_tty.py
