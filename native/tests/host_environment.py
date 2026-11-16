"""Host-dependent inputs for native tests: from the environment, never one workstation's paths.

External executables resolve the way native/scripts/build.py and qualify.py
resolve them. Node: ``NODE``, then ``node`` on PATH (qualify.py runs ``node``
from PATH). The WASM compiler and linker: ``toolchain.discover()``, the exact
function build.py uses (``WASM_CC``/``WASM_CLANG`` and ``WASM_LD``, its
existence-checked LLVM directories, then PATH). An absent tool raises
ToolUnavailable, an AssertionError whose message starts with ``BLOCKED:``, so
the calling test fails with that reason instead of a FileNotFoundError, a skip
or a pass.

Diagnostic records for failing comparisons go to ``NOCTURNE_TEST_FAILURE_DIR``,
else ``native/evidence/test-failures`` of this checkout, which is outside the
qualification source fingerprint and never staged.
"""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from native.scripts.toolchain import discover

NATIVE = Path(__file__).resolve().parents[1]
FAILURE_DIRECTORY_VARIABLE = 'NOCTURNE_TEST_FAILURE_DIR'


class ToolUnavailable(AssertionError):
    """A required external executable is absent: the check is BLOCKED, not passed."""


def node_executable(environment=None):
    """Absolute path of Node: ``NODE`` (a path or a name on PATH), else ``node`` on PATH."""
    environment = os.environ if environment is None else environment
    search = environment.get('PATH')  # as qualify.py toolExecutables: absent PATH means the OS default
    explicit = environment.get('NODE')
    if explicit:
        found = shutil.which(explicit, path=search)
        if not found:
            raise ToolUnavailable(f'BLOCKED: node not available: NODE={explicit!r} is not an executable')
        return found
    found = shutil.which('node', path=search)
    if not found:
        raise ToolUnavailable('BLOCKED: node not available: set NODE or put node on PATH')
    return found


def wasm_toolchain():
    """(clang, wasm-ld) exactly as native/scripts/build.py discovers them."""
    try:
        tools = discover()
    except RuntimeError as error:  # an explicit CC/WASM_CC/WASM_CLANG/WASM_LD that is not executable
        raise ToolUnavailable(f'BLOCKED: clang and wasm-ld not available as build.py discovers them: {error}') from error
    if not tools['wasmCC']:
        raise ToolUnavailable('BLOCKED: clang not available: set WASM_CC or WASM_CLANG, or put clang on PATH')
    if not tools['wasmLD']:
        raise ToolUnavailable('BLOCKED: wasm-ld not available: set WASM_LD or put wasm-ld on PATH')
    return tools['wasmCC'], tools['wasmLD']


def failure_directory(environment=None):
    environment = os.environ if environment is None else environment
    return Path(environment.get(FAILURE_DIRECTORY_VARIABLE) or NATIVE / 'evidence/test-failures')


def failure_record(name, record, environment=None):
    """Write ``record`` as JSON for a failing comparison; return and print where it went.

    The file appears whole (temporary file, then rename). An unwritable location
    is reported, never raised, so the comparison's own assertion stays the failure.
    """
    if not name or Path(name).name != name or name in ('.', '..'):
        raise ValueError(f'failure record name must be a plain file name: {name!r}')
    directory = failure_directory(environment)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.' + name + '.', dir=directory)
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                json.dump(record, stream)
            os.replace(temporary, directory / name)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
    except OSError as error:
        message = f'failure record {name} not written to {directory}: {error}'
    else:
        message = f'failure record written: {directory / name}'
    print(message, file=sys.stderr)
    return message
