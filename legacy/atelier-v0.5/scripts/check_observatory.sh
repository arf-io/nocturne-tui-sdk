#!/usr/bin/env sh
# Full legacy regression, then new material/interaction/transport tests.
# CI must set REQUIRE_RUST=1 and REQUIRE_PTY=1. No fixture acceptance here.
set -eu
cd "$(dirname "$0")/.."
mkdir -p dist/observatory
sh scripts/check_fleet.sh >dist/observatory/legacy-regression.txt 2>&1 || { cat dist/observatory/legacy-regression.txt; exit 1; }
python3 scripts/build_observatory_gallery.py
node tests/observatory/contracts.mjs >dist/observatory/contracts.txt
node tests/observatory/rendering.mjs >dist/observatory/rendering-tests.txt
node tests/observatory/lifecycle.mjs >dist/observatory/lifecycle-tests.txt
node tests/observatory/skin_core.mjs >dist/observatory/skin-tests.txt
node tests/observatory/pty_headless.mjs >dist/observatory/headless-tests.txt 2>&1
python3 -m unittest discover -s tests/observatory -p 'test_*.py' -v >dist/observatory/host-unit-tests.txt 2>&1
"${CC:-cc}" -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-sanitize-recover=all -Iinclude src/nocturne.c tests/observatory/color_safety.c -o /tmp/nocturne-color-safety
/tmp/nocturne-color-safety >dist/observatory/color-safety.txt
python3 scripts/check_observatory_tty.py
cat dist/observatory/contracts.txt dist/observatory/rendering-tests.txt dist/observatory/lifecycle-tests.txt dist/observatory/skin-tests.txt dist/observatory/headless-tests.txt dist/observatory/color-safety.txt
printf '\nBrowser and synthetic-audio lifecycle tests: python3 scripts/check_observatory_browser.py && python3 scripts/check_observatory_media.py\n'
