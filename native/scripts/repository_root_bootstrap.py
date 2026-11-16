#!/usr/bin/env python3
"""Keep one uniform repository-root bootstrap in every test module importing ``native.``.

Test modules such as ``native/tests/test_camera_controls.py`` import
``native.bindings...`` and ``native.tests...``; those resolve only when the
repository root (the parent of ``native/``) is on ``sys.path``. A qualification
run supplies it through PYTHONPATH, but a module run on its own from
``native/tests`` (``python -m unittest test_camera_controls``), from the
repository root (``python -m unittest native.tests.test_camera_controls``) or
as a file must import too. Every such module therefore carries BOOTSTRAP,
byte-identical, as its first statement after the module docstring and any
``from __future__`` imports. The line inserts this checkout's root only when
it is absent; it never removes or reorders existing entries.

Detection is syntactic (every ``import native...`` and ``from native... import``
at any nesting depth) over modules directly in ``native/tests``; fixtures are
never edited. ``--check`` (the default, also accepted explicitly) lists modules
whose bootstrap is missing or misplaced, exits 1 and writes nothing; ``--write``
repairs them atomically, preserving bytes elsewhere and file mode, and is
idempotent. The two flags are mutually exclusive. Neither mode executes test code.
"""
from __future__ import annotations
import argparse
import ast
import os
import re
import tempfile
from pathlib import Path

BOOTSTRAP = ("import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); "
             "_REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)"
             "  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py")
TESTS = Path(__file__).resolve().parents[1] / 'tests'


def splitLines(text: str) -> list[str]:
    """Split after each LF only, keeping endings; ast numbers lines the same way.

    ``str.splitlines`` also breaks at U+2028, U+0085, form feed and others,
    which appear inside string literals of the Unicode tests.
    """
    return [line for line in re.split(r'(?<=\n)', text) if line]


def readSource(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b'\xef\xbb\xbf') or b'\r' in data.replace(b'\r\n', b''):
        raise ValueError(f'{path}: byte-order mark or bare CR line ending; edit by hand')
    return data.decode('utf-8')


def importsNative(tree: ast.AST) -> bool:
    """True when any absolute import statement names the top-level ``native`` package."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module == 'native' or node.module.startswith('native.'):
                return True
        elif isinstance(node, ast.Import):
            if any(alias.name == 'native' or alias.name.startswith('native.') for alias in node.names):
                return True
    return False


def insertionLine(tree: ast.Module, lineCount: int, path: Path) -> int:
    """Zero-based line index before which BOOTSTRAP belongs."""
    body, position, previous = tree.body, 0, None
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        previous, position = body[0], 1
    while position < len(body) and isinstance(body[position], ast.ImportFrom) \
            and body[position].module == '__future__':
        previous, position = body[position], position + 1
    if position == len(body):
        return lineCount
    node = body[position]
    start = min([node.lineno] + [decorator.lineno for decorator in getattr(node, 'decorator_list', [])])
    if previous is not None and previous.end_lineno >= start:
        raise ValueError(f'{path}: first statement shares a line with the docstring or a __future__ import')
    return start - 1


def bootstrapped(source: str, path: Path) -> str:
    """Return ``source`` with exactly one BOOTSTRAP at its required position."""
    kept = [line for line in splitLines(source) if line.rstrip('\r\n') != BOOTSTRAP]
    tree = ast.parse(''.join(kept), str(path))
    index = insertionLine(tree, len(kept), path)
    ending = '\r\n' if any(line.endswith('\r\n') for line in kept) else '\n'
    if kept and index == len(kept) and not kept[-1].endswith('\n'):
        kept[-1] += ending
    kept.insert(index, BOOTSTRAP + ending)
    result = ''.join(kept)
    compile(result, str(path), 'exec', dont_inherit=True)
    return result


def candidates(tests: Path = TESTS) -> list[Path]:
    """Python modules directly under ``tests`` that import ``native.`` anywhere."""
    return [path for path in sorted(tests.glob('*.py'))
            if importsNative(ast.parse(readSource(path), str(path)))]


def problems(tests: Path = TESTS) -> list[Path]:
    """Candidates whose current text differs from their bootstrapped form."""
    return [path for path in candidates(tests)
            if bootstrapped(readSource(path), path) != readSource(path)]


def write(path: Path) -> bool:
    """Atomically rewrite ``path`` into bootstrapped form; return whether bytes changed."""
    original = readSource(path)
    updated = bootstrapped(original, path)
    if updated == original:
        return False
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(updated.encode('utf-8'))
        os.chmod(temporary, path.stat().st_mode & 0o7777)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='report drift and write nothing (default)')
    mode.add_argument('--write', action='store_true', help='repair modules in place')
    parser.add_argument('--tests', type=Path, default=TESTS, help='test directory (default: native/tests)')
    args = parser.parse_args(argv)
    found = candidates(args.tests)
    if args.write:
        changed = [path for path in found if write(path)]
        for path in changed:
            print('bootstrapped', path.name)
        print(f'{len(changed)} changed of {len(found)} modules importing native.')
        return 0
    missing = problems(args.tests)
    for path in missing:
        print('missing or misplaced bootstrap:', path.name)
    print(f'{len(missing)} of {len(found)} modules importing native. need the bootstrap')
    return 1 if missing else 0


if __name__ == '__main__':
    raise SystemExit(main())
