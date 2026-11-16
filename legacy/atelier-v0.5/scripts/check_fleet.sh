#!/usr/bin/env sh
# All previous suites + Pearl Fleet. Reference acceptance is always separate.
# REQUIRE_RUST=1 is mandatory in CI and fails on missing Rust; no silent success.
set -eu
cd "$(dirname "$0")/.."
mkdir -p dist/fleet
sh scripts/check_studio.sh >dist/fleet/regression.txt 2>&1 || { cat dist/fleet/regression.txt; exit 1; }
cat dist/fleet/regression.txt
node tests/fleet/contract.mjs >dist/fleet/contracts.txt
node tests/fleet/robustness.mjs >dist/fleet/robustness.txt
node tests/fleet/input.mjs >dist/fleet/input-tests.json
node tests/fleet/parity.mjs >dist/fleet/wasm-parity.json
"${CC:-cc}" -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-sanitize-recover=all -Iinclude src/nocturne.c tests/fleet/fade_safety.c -o /tmp/nocturne-fleet-safety
/tmp/nocturne-fleet-safety >dist/fleet/sanitizer-tests.txt
python3 scripts/build_fleet_gallery.py
python3 scripts/check_fleet_tty.py
cat dist/fleet/contracts.txt dist/fleet/robustness.txt dist/fleet/wasm-parity.json dist/fleet/sanitizer-tests.txt
