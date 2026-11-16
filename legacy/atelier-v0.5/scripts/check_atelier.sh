#!/usr/bin/env sh
# Complete earlier regression, then Spatial Atelier contracts and actual hosts.
# CI/release must use REQUIRE_RUST=1 REQUIRE_PTY=1. Never accept fixtures here.
set -eu
cd "$(dirname "$0")/.."
mkdir -p dist/atelier
sh scripts/check_observatory.sh >dist/atelier/legacy-check.txt 2>&1 || { cat dist/atelier/legacy-check.txt; exit 1; }
tsc -p tsconfig.json
node scripts/build_atelier_schema.mjs
python3 scripts/build_atelier_gallery.py
node --test tests/atelier/contracts.mjs tests/atelier/settings.mjs >dist/atelier/contracts.txt
node --test tests/atelier/rendering.mjs >dist/atelier/rendering-tests.txt
python3 scripts/check_atelier_tty.py >dist/atelier/tty-tests.txt 2>&1
node examples/atelier_embed.mjs >dist/atelier/embed.ans
cat dist/atelier/contracts.txt dist/atelier/rendering-tests.txt dist/atelier/tty-tests.txt
printf '\nBrowser: python3 scripts/check_atelier_browser.py\n'
