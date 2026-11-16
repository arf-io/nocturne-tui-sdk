#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$HERE/native-env.sh"
"$PYTHON" "$HERE/native/scripts/build.py" "$@"
case " $* " in *" --native-only "*) ;; *) "$PYTHON" "$HERE/native/scripts/build_gallery.py";; esac
