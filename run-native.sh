#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$HERE/native-env.sh"
exec "$PYTHON" "$HERE/native/examples/terminal.py" "$@"
