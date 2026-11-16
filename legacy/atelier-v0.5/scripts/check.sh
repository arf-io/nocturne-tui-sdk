#!/usr/bin/env sh
# Repeat the core/binding suite. No network requests or fixture regeneration.
set -eu
cd "$(dirname "$0")/.."
sh scripts/build.sh --wasm
if python3 -m unittest discover -s tests -p 'test_*.py' -v >dist/python-tests.txt 2>&1; then
  cat dist/python-tests.txt
else
  cat dist/python-tests.txt
  exit 1
fi
tsc -p tsconfig.json
node tests/wasm-parity.mjs > dist/wasm-tests.json
cat dist/wasm-tests.json
(cd bindings/go && go test ./... -v) > dist/go-tests.txt
cat dist/go-tests.txt
"${CC:-cc}" -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -Iinclude src/nocturne.c tests/native_safety.c -o /tmp/nocturne-safety
/tmp/nocturne-safety > dist/sanitizer-tests.txt
cat dist/sanitizer-tests.txt
if command -v cargo >/dev/null 2>&1; then
  (cd bindings/rust && cargo test && cargo run --example snapshot >/dev/null)
else
  printf '\nNOT RUN: Rust facade, because cargo is unavailable.\n'
fi
python3 scripts/build_gallery.py
