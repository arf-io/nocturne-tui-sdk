#!/usr/bin/env sh
# Build the native shared library. --wasm also rebuilds the included browser kernel.
set -eu
cd "$(dirname "$0")/.."
WASM=0
case "${1:-}" in
  '') ;;
  --wasm) WASM=1 ;;
  --help|-h) printf 'Usage: sh scripts/build.sh [--wasm]\nNative: C11 compiler. WASM: LLVM Clang with wasm-ld.\n'; exit 0 ;;
  *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
esac
mkdir -p dist
case "$(uname -s)" in
  Darwin) LIB=dist/libnocturne.dylib; SHARED=-dynamiclib ;;
  *) LIB=dist/libnocturne.so; SHARED=-shared ;;
esac
"${CC:-cc}" -std=c11 -O3 -Wall -Wextra -Werror -fPIC "$SHARED" -Iinclude src/nocturne.c -o "$LIB"
printf 'Built %s\n' "$LIB"
if [ "$WASM" = 1 ]; then
  "${CLANG:-clang}" --target=wasm32 -std=c11 -O3 -nostdlib -fno-builtin -Iinclude src/nocturne.c src/wasm.c \
    -Wl,--no-entry -Wl,--export-all -Wl,--initial-memory=6291456 -Wl,--max-memory=16777216 \
    -o dist/nocturne.wasm
  printf 'Built dist/nocturne.wasm\n'
fi
