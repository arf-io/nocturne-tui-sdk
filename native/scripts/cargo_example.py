"""Build named Cargo examples without assuming their target directory.

Cargo supplies the actual executable through compiler-artifact messages. All callers
inherit the explicitly activated compiler and use offline, locked resolution.
"""
from __future__ import annotations
import datetime
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
from typing import Mapping


def cargoEnvironment(sourceRoot: Path, environment: Mapping[str,str]) -> dict[str,str]:
    """Keep a caller cache parent, isolate products by canonical source root."""
    result=dict(environment)
    target=result.get('CARGO_TARGET_DIR')
    if not target:return result
    parent=Path(result.get('NOCTURNE_CARGO_TARGET_PARENT',target)).resolve()
    identity=hashlib.sha256(str(Path(sourceRoot).resolve()).encode()).hexdigest()
    result['NOCTURNE_CARGO_TARGET_PARENT']=str(parent)
    result['CARGO_TARGET_DIR']=str(parent/'nocturne-sources'/identity)
    return result

def manifestSourceRoot(manifest: Path) -> Path:
    try:
        result=subprocess.run(['git','-C',str(manifest.parent),'rev-parse','--show-toplevel'],capture_output=True,text=True)
        if result.returncode==0:return Path(result.stdout.strip()).resolve()
    except FileNotFoundError:pass
    return manifest.parent.resolve()

def executableFromMessages(text: str, example: str) -> Path:
    """Select one named example executable from completed Cargo JSON output.

    Inputs: Cargo stdout and exact example target name. Output: absolute Path.
    Raises ValueError for missing or conflicting executable identities. Repeated
    records for the same executable are harmless. Binary targets do not qualify.
    """
    paths = set()
    for line in text.splitlines():
        if not line.startswith('{'):
            continue
        row = json.loads(line)
        target = row.get('target', {})
        if (row.get('reason') == 'compiler-artifact' and target.get('name') == example
                and 'example' in target.get('kind', []) and row.get('executable')):
            paths.add(Path(row['executable']).resolve())
    if len(paths) != 1:
        raise ValueError(f'Cargo did not identify exactly one executable for example {example!r}')
    return paths.pop()


def buildExample(manifest: Path, example: str, log: Path, *, release: bool = False,
                 env: Mapping[str, str] | None = None, timeout: float = 180) -> Path:
    """Compile the real locked example and return Cargo's verified output path.

    Does not run the example: callers must execute the returned path and check exit.
    Writes build output and a sibling JSON receipt (including exact argv/exit/hash).
    Preserves the existing lock. OSError, TimeoutExpired, CalledProcessError or
    ValueError propagate; no stale executable is returned after a failed build.

    Example: path = buildExample(Path('Cargo.toml'), 'snapshot', Path('/tmp/build.log'))
    """
    manifest, log = manifest.resolve(), log.resolve()
    childEnv = cargoEnvironment(manifestSourceRoot(manifest),os.environ if env is None else env)
    childEnv['CARGO_NET_OFFLINE'] = 'true'
    argv = ['cargo', 'build', '--offline', '--locked', '--manifest-path', str(manifest),
            '--example', example, '--message-format=json-render-diagnostics']
    if release:
        argv.append('--release')
    log.parent.mkdir(parents=True, exist_ok=True)
    receipt = log.with_suffix('.json')
    record = {'argv': argv, 'cwd': str(manifest.parent), 'status': 'RUNNING',
              'startedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'timeoutSeconds': timeout,
              'environment': {k: childEnv[k] for k in ('PATH','RUSTC','RUSTDOC','CARGO_HOME',
                              'CARGO_TARGET_DIR','CARGO_NET_OFFLINE','CC','AR') if k in childEnv}}
    receipt.write_text(json.dumps(record, indent=2)+'\n')
    process = None
    def stopChildGroup():
        # Each build owns its process group. Killing only Cargo leaves build.rs
        # programs alive; they may retain files and locks after a timeout.
        if process is not None:
            try:
                if os.name == 'posix':
                    os.killpg(process.pid, signal.SIGKILL)
                elif process.poll() is None:
                    process.kill()
            except ProcessLookupError:
                pass
            record['exitCode'] = process.wait(timeout=5)
    try:
        with log.open('w') as stream:
            process = subprocess.Popen(argv, cwd=manifest.parent, env=childEnv, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=os.name == 'posix')
            record['childPid'] = process.pid
            code = process.wait(timeout=timeout)
        record['exitCode'] = code
        if code:
            raise subprocess.CalledProcessError(code, argv)
        output = executableFromMessages(log.read_text(), example)
        if not output.is_file() or not os.access(output, os.X_OK):
            raise ValueError(f'Cargo output is missing or not executable: {output}')
        record.update(status='PASS', executable=str(output),
                      executableSha256=hashlib.sha256(output.read_bytes()).hexdigest())
        return output
    except subprocess.TimeoutExpired as error:
        stopChildGroup()
        record.update(status='TIMEOUT', reason=str(error))
        raise
    except BaseException as error:
        if process is not None and process.poll() is None:
            stopChildGroup()
        record.update(status='INTERRUPTED' if isinstance(error, KeyboardInterrupt) else 'FAIL', reason=str(error))
        raise
    finally:
        record['finishedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record['logSha256'] = hashlib.sha256(log.read_bytes()).hexdigest() if log.exists() else None
        receipt.write_text(json.dumps(record, indent=2)+'\n')
