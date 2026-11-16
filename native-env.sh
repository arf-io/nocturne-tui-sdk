#!/bin/sh
# Source only from an SDK launcher. Does not modify a user's shell startup files.
SDK_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PATH="$SDK_ROOT/.nocturne-tools/node/bin:$SDK_ROOT/node_modules/.bin:$HOME/.cargo/bin:/opt/homebrew/opt/rustup/bin:/usr/local/opt/rustup/bin:$PATH"
export PATH
if [ -n "${PYTHON:-}" ]; then :
elif [ -x "$SDK_ROOT/.venv/bin/python3" ]; then PYTHON="$SDK_ROOT/.venv/bin/python3"
else PYTHON=python3
fi
export PYTHON
