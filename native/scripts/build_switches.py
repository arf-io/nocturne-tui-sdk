"""The command-path build switches (native/docs/TDD-STATE-COPY-ELIMINATION-20261102.md section 5.6).

build.py reads two environment switches beside NOCTURNE_COVERAGE and appends their defines to the common flags
of both the native and the WASM build:

  NOCTURNE_COMMAND_FASTPATH=0..3        -DNR_COMMAND_FASTPATH=<n>, overriding the internal.h default for that
                                        build only (a developer convenience; internal.h stays the rollback lever)
  NOCTURNE_SHADOW_CHECK=1|reject|inject -DNR_SHADOW_CHECK=1, plus -DNR_SHADOW_REJECT_AT_COMMIT=1 or
                                        -DNR_SHADOW_INJECT_K=8 (test-only shadow builds)

An unset switch adds nothing. Any other value, the empty string included, is refused before anything compiles.
"""

FASTPATH = 'NOCTURNE_COMMAND_FASTPATH'
SHADOW = 'NOCTURNE_SHADOW_CHECK'
FASTPATH_VALUES = ('0', '1', '2', '3')
SHADOW_DEFINES = {
    '1': ['-DNR_SHADOW_CHECK=1'],
    'reject': ['-DNR_SHADOW_CHECK=1', '-DNR_SHADOW_REJECT_AT_COMMIT=1'],
    'inject': ['-DNR_SHADOW_CHECK=1', '-DNR_SHADOW_INJECT_K=8'],
}


class BuildSwitchError(ValueError):
    """A switch holds a value build.py does not accept."""


def parse(environ):
    """Validate both switches in `environ` (a mapping). Returns {'NOCTURNE_COMMAND_FASTPATH': None|str,
    'NOCTURNE_SHADOW_CHECK': None|str, 'defines': [...]}; raises BuildSwitchError naming the variable."""
    fastpath, shadow = environ.get(FASTPATH), environ.get(SHADOW)
    defines = []
    if fastpath is not None:
        if fastpath not in FASTPATH_VALUES:
            raise BuildSwitchError('%s=%r is not one of %s; unset it to use the internal.h default'
                                   % (FASTPATH, fastpath, ', '.join(FASTPATH_VALUES)))
        defines.append('-DNR_COMMAND_FASTPATH=' + fastpath)
    if shadow is not None:
        if shadow not in SHADOW_DEFINES:
            raise BuildSwitchError('%s=%r is not one of %s; unset it for an ordinary build'
                                   % (SHADOW, shadow, ', '.join(SHADOW_DEFINES)))
        defines.extend(SHADOW_DEFINES[shadow])
    return {FASTPATH: fastpath, SHADOW: shadow, 'defines': defines}


SCHEMA = 'nocturne.native.build-switches.v1'
COVERAGE = 'NOCTURNE_COVERAGE'


def record(environ, wasm):
    """The record of the switches a build applied (dist/build-switches.json). null means unset: for
    NOCTURNE_COMMAND_FASTPATH, that the internal.h default applies. NOCTURNE_COVERAGE is "1" only when build.py
    instruments, as it does only for exactly "1"."""
    parsed = parse(environ)
    return {'schema': SCHEMA, FASTPATH: parsed[FASTPATH], SHADOW: parsed[SHADOW],
            COVERAGE: '1' if environ.get(COVERAGE) == '1' else None,
            'defines': list(parsed['defines']), 'native': True, 'wasm': bool(wasm)}


def write_record(path, content):
    """Write the record atomically: a temporary file in the same directory, flushed to disk, then renamed over
    the target, then the directory entry flushed. A reader sees the old file, no file, or the whole new one."""
    import json, os, tempfile
    from pathlib import Path
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.build-switches.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(json.dumps(content, indent=1, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
