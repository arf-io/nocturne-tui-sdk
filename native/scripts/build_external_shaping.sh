#!/bin/sh
# Invoke only inside a combined build gate. No global installation or Homebrew edits.
set -eu
if [ "$#" -ne 2 ]; then
 echo 'Usage: build_external_shaping.sh EXTRACTED_HARFBUZZ_SOURCE EXTERNAL_PREFIX' >&2
 exit 2
fi
shaping_source=$1
shaping_prefix=$2
case "$shaping_source" in /*) ;; *) echo 'Source must be absolute' >&2;exit 2;; esac
case "$shaping_prefix" in /*) ;; *) echo 'Prefix must be absolute' >&2;exit 2;; esac
shaping_repo=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
case "$shaping_prefix" in "$shaping_repo"|"$shaping_repo"/*) echo 'Dependency prefix must be outside SDK checkout' >&2;exit 2;; esac
[ -f "$shaping_source/CMakeLists.txt" ] || { echo 'Missing extracted HarfBuzz source' >&2;exit 2; }
cmake -S "$shaping_source" -B "$shaping_prefix/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$shaping_prefix" -DBUILD_SHARED_LIBS=ON -DHB_BUILD_SUBSET=OFF -DHB_BUILD_UTILS=OFF -DHB_HAVE_CORETEXT=OFF -DHB_HAVE_FREETYPE=OFF -DHB_HAVE_GLIB=OFF -DHB_HAVE_ICU=OFF -DHB_HAVE_CAIRO=OFF -DHB_HAVE_GRAPHITE2=OFF
cmake --build "$shaping_prefix/build" --parallel 4
cmake --install "$shaping_prefix/build"
