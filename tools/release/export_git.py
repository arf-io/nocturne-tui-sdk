#!/usr/bin/env python3
"""Export an exact committed tree and a verified union of every named Git ref.

This source-integrity operation works for unqualified candidates. It neither runs
nor waives the strict SDK/runtime gates in native/scripts/package_contracts.py.
Only real Git objects are exported; working-tree changes are never substituted.
"""
from pathlib import Path, PurePosixPath
import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import zlib

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY / 'native/scripts'))
from release_identity import COMMIT_PATTERN, loadReleaseIdentity

FONTS = {'.ttf', '.otf', '.woff', '.woff2', '.tdf', '.flf', '.pfb', '.pfa', '.fon', '.fnt'}
CACHES = {'.git', '.venv', 'node_modules', 'target', '__pycache__', '.pytest_cache',
          '.mypy_cache', '.ruff_cache', '.nocturne-tools', '.cargo', '.npm'}
CREDENTIAL_NAMES = {'.env', '.netrc', '.npmrc', '.pypirc', 'id_rsa', 'id_ed25519',
                    'id_dsa', 'credentials.json', 'credentials', 'service-account.json'}
COMPILER_NAMES = {'rustc', 'rustdoc', 'cargo', 'clang', 'clang++', 'wasm-ld', 'lld', 'go'}
PRIVATE_KEY = re.compile(br'(?m)^-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----\r?$')
ARCHIVE_NAME = re.compile(r'(?i)^(?:rust(?:c|doc|fmt|-std|-src)?-|cargo-|clang\+?\+?[-_]|'
                          r'llvm[-_]|go[0-9]+\.|aetherial|fleet[-_]offline|account[-_]archive)')
ARCHIVE_SUFFIXES = ('.tar', '.tar.gz', '.tar.xz', '.tgz', '.zip', '.7z', '.zst')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fileRecord(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return {'name': path.name, 'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


class Git:
    """Read Git objects and retain actual command exits and output hashes."""
    def __init__(self, root):
        self.root = Path(root)
        self.commands = []
        self.environment = dict(os.environ, GIT_NO_REPLACE_OBJECTS='1')

    def run(self, *arguments, root=None):
        command = ['git', '--no-replace-objects', *map(str, arguments)]
        result = subprocess.run(command, cwd=root or self.root, env=self.environment,
                                capture_output=True, timeout=240)
        self.commands.append({'command': command, 'cwd': str(root or self.root),
                              'exitCode': result.returncode,
                              'stdoutSha256': digest(result.stdout),
                              'stderrSha256': digest(result.stderr),
                              'stderr': result.stderr.decode('utf-8', 'replace')})
        if result.returncode:
            raise ValueError('Git command failed: ' + ' '.join(command) + ': ' +
                             result.stderr.decode('utf-8', 'replace').strip())
        return result.stdout

    def refs(self, root=None):
        lines = self.run('for-each-ref', '--format=%(objectname) %(refname)', root=root)
        return dict(sorted((line.split(' ', 1)[1], line.split(' ', 1)[0])
                           for line in lines.decode('utf-8').splitlines()))


class BlobReader:
    """One real cat-file process; blob data is streamed without checkout filters."""
    def __init__(self, root):
        self.errors = tempfile.TemporaryFile()
        self.process = subprocess.Popen(['git', '--no-replace-objects', 'cat-file', '--batch'],
                                        cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.errors,
                                        env=dict(os.environ, GIT_NO_REPLACE_OBJECTS='1'))

    def __enter__(self):
        return self

    def read(self, oid):
        self.process.stdin.write(oid.encode('ascii') + b'\n')
        self.process.stdin.flush()
        header = self.process.stdout.readline().split()
        if len(header) != 3 or header[0].decode('ascii') != oid or header[1] != b'blob':
            raise ValueError('Git object is not the expected blob: ' + oid)
        size = int(header[2])
        data = self.process.stdout.read(size)
        if len(data) != size or self.process.stdout.read(1) != b'\n':
            raise ValueError('Incomplete Git blob: ' + oid)
        return data

    def __exit__(self, errorType, error, traceback):
        self.process.stdin.close()
        self.process.stdout.close()
        code = self.process.wait(timeout=30)
        self.exitCode = code
        self.errors.seek(0)
        diagnostic = self.errors.read().decode('utf-8', 'replace')
        self.errors.close()
        if code and error is None:
            raise ValueError('Git cat-file failed: ' + diagnostic)


def validatePath(name, mode):
    """Fail on disallowed paths instead of silently dropping tracked content."""
    path = PurePosixPath(name)
    if (not name or name.startswith('/') or '\\' in name or
            any(ord(char) < 32 or ord(char) == 127 for char in name) or
            any(part in ('', '.', '..') for part in name.split('/'))):
        raise ValueError('Unsafe Git path: ' + repr(name))
    if mode == '120000':
        raise ValueError('Source symlink cannot be safely exported: ' + name)
    if mode not in ('100644', '100755'):
        raise ValueError('Unsupported Git mode (including submodules): ' + mode + ' ' + name)
    lowered = path.name.lower()
    parts = {part.lower() for part in path.parts}
    prohibitedArchive = ARCHIVE_NAME.match(path.name) and lowered.endswith(ARCHIVE_SUFFIXES)
    compiler = lowered in COMPILER_NAMES and ('bin' in parts or len(path.parts) == 1)
    if (path.suffix.lower() in FONTS or parts.intersection(CACHES) or
            lowered in CREDENTIAL_NAMES or prohibitedArchive or compiler):
        raise ValueError('Export contains disallowed tracked content: ' + name)


def treeEntries(git, tree):
    result = {}
    for raw in git.run('ls-tree', '-r', '-z', '--full-tree', tree).split(b'\0'):
        if not raw:
            continue
        header, rawName = raw.split(b'\t', 1)
        mode, kind, oid = header.decode('ascii').split()
        name = rawName.decode('utf-8', 'strict')
        validatePath(name, mode)
        if kind != 'blob':
            raise ValueError('Unsupported non-blob tree entry: ' + name)
        if name in result:
            raise ValueError('Duplicate Git path: ' + name)
        result[name] = {'gitMode': mode, 'gitBlob': oid}
    return dict(sorted(result.items()))


def auditHistory(git, selected):
    """Audit all reachable trees, including files deleted from the selected tree."""
    trees = sorted(set(git.run('log', '--all', 'HEAD', '--format=%T').decode().splitlines()))
    objects = {}
    pathVersions = set()
    for tree in trees:
        for name, entry in treeEntries(git, tree).items():
            objects.setdefault(entry['gitBlob'], name)
            pathVersions.add((name, entry['gitBlob']))
    with BlobReader(git.root) as reader:
        total = 0
        for oid, name in sorted(objects.items()):
            data = reader.read(oid)
            total += len(data)
            if PRIVATE_KEY.search(data):
                raise ValueError('Reachable history contains a private key envelope: ' + name)
    commits = set(git.run('rev-list', '--all', 'HEAD').decode().splitlines())
    if selected not in commits:
        raise ValueError('Selected commit must be reachable from a retained ref or HEAD')
    return {'reachableCommits': len(commits), 'uniqueTrees': len(trees),
            'uniqueBlobsInspected': len(objects), 'distinctPathBlobPairs': len(pathVersions),
            'blobBytesInspected': total, 'blobReadCommand': ['git', '--no-replace-objects', 'cat-file', '--batch'],
            'blobReaderExitCode': reader.exitCode,
            'policy': 'No prohibited filenames, caches, compiler archives, symlinks, submodules, '
                      'or private-key envelopes in any reachable tree. This is a bounded content '
                      'policy, not a general secret-scanning certification.'}


def tarInfo(name, mode, epoch, size=0, directory=False):
    info = tarfile.TarInfo('nocturne/' + name if name else 'nocturne')
    info.mode = mode
    info.uid = info.gid = 0
    info.uname = info.gname = ''
    info.mtime = epoch
    info.size = size
    info.type = tarfile.DIRTYPE if directory else tarfile.REGTYPE
    return info


def writeSource(root, entries, epoch, archive, document, release):
    """Write deterministic tar and complete UTF-8 source text from exact Git blobs."""
    directories = {''}
    for name in entries:
        parent = PurePosixPath(name).parent
        while str(parent) != '.':
            directories.add(str(parent))
            parent = parent.parent
    manifest = {}
    with archive.open('xb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb',
                                                compresslevel=9, mtime=0) as compressed, \
            tarfile.open(fileobj=compressed, mode='w|', format=tarfile.PAX_FORMAT) as tar, \
            document.open('x', encoding='utf-8', newline='\n') as text, BlobReader(root) as reader:
        text.write('# Nocturne ' + release['build'] + ': exact committed source contents\n\n')
        text.write('Source commit: ' + release['sourceCommit'] + '\n\n')
        text.write('Source baseline: ' + release['sourceBaseline'] + '\n\n')
        text.write('Every UTF-8 text blob appears in full. Binary blobs are identified by '
                   'Git object ID, size, and SHA-256 and remain complete in the source tarball. '
                   'Exporting source does not execute runtime qualification.\n')
        for name in sorted(directories):
            tar.addfile(tarInfo(name, 0o755, epoch, directory=True))
        for name, entry in sorted(entries.items()):
            data = reader.read(entry['gitBlob'])
            manifest[name] = {**entry, 'bytes': len(data), 'sha256': digest(data)}
            tar.addfile(tarInfo(name, int(entry['gitMode'][-3:], 8), epoch, len(data)), io.BytesIO(data))
            text.write('\n## ' + name + '\n\n')
            text.write('Git blob: ' + entry['gitBlob'] + '; bytes: ' + str(len(data)) +
                       '; SHA-256: ' + digest(data) + '.\n\n')
            try:
                if b'\0' in data:
                    raise UnicodeError('Binary NUL')
                content = data.decode('utf-8')
            except UnicodeError:
                text.write('Binary payload; complete bytes are in the tarball.\n')
                continue
            runs = re.findall('(?m)^[ \t]*(' + chr(96) + '+)', content)
            fence = chr(96) * max(4, max(map(len, runs), default=0) + 1)
            text.write(fence + '\n' + content + '\n' + fence + '\n')
    return manifest


def verifyFresh(git, bundle, archive, expectedRefs, entries, selected, tree, epoch):
    """Restore the union bundle and source tar into independent empty directories."""
    with tempfile.TemporaryDirectory(prefix='nocturne-export-verify-') as temporary:
        base = Path(temporary)
        bare = base / 'history.git'
        git.run('init', '--bare', '--quiet', str(bare), root=base)
        git.run('bundle', 'verify', str(bundle), root=bare)
        git.run('fetch', '--no-tags', str(bundle), 'refs/*:refs/*', root=bare)
        restored = git.refs(root=bare)
        if restored != expectedRefs:
            raise ValueError('Fresh union restore did not preserve every named ref')
        # A detached HEAD can be the only reference to the exact selected commit.
        git.run('fetch', '--no-tags', str(bundle), 'HEAD', root=bare)
        git.run('fsck', '--full', '--strict', root=bare)
        actualTree = git.run('rev-parse', selected + '^{tree}', root=bare).decode().strip()
        if actualTree != tree:
            raise ValueError('Fresh union restore changed the selected source tree')
        restoredGit = Git(bare)
        restoredEntries = treeEntries(restoredGit, tree)
        git.commands.extend(restoredGit.commands)
        if restoredEntries != entries:
            raise ValueError('Fresh union restore changed selected source entries')
        extraction = base / 'source'
        extraction.mkdir()
        expectedDirectories = {'nocturne'}
        for name in entries:
            parent = PurePosixPath('nocturne/' + name).parent
            while str(parent) != '.':
                expectedDirectories.add(str(parent))
                parent = parent.parent
        seen = set()
        with tarfile.open(archive, 'r:gz') as tar, BlobReader(bare) as reader:
            for member in tar:
                name = member.name
                if name in seen:
                    raise ValueError('Duplicate tar member: ' + name)
                seen.add(name)
                if (member.uid, member.gid, member.uname, member.gname, member.mtime) != (0, 0, '', '', epoch):
                    raise ValueError('Noncanonical tar metadata: ' + name)
                if member.isdir():
                    if name not in expectedDirectories or member.mode != 0o755:
                        raise ValueError('Unexpected tar directory: ' + name)
                    (extraction / name).mkdir(parents=True, exist_ok=False)
                    continue
                relative = name.removeprefix('nocturne/')
                if not name.startswith('nocturne/') or relative not in entries or not member.isfile():
                    raise ValueError('Unexpected or unsafe tar member: ' + name)
                entry = entries[relative]
                expected = reader.read(entry['gitBlob'])
                actual = tar.extractfile(member).read()
                if actual != expected or member.mode != int(entry['gitMode'][-3:], 8):
                    raise ValueError('Tar differs from freshly restored Git bytes/mode: ' + name)
                path = extraction / name
                path.write_bytes(actual)
                path.chmod(member.mode)
                if path.read_bytes() != expected or path.stat().st_mode & 0o777 != member.mode:
                    raise ValueError('Fresh source extraction differs: ' + name)
        if seen != expectedDirectories | {'nocturne/' + name for name in entries}:
            raise ValueError('Tar does not contain exactly the selected Git tree')
        return {'freshBundleRestoreVerified': True, 'freshTarExtractionVerified': True,
                'restoredNamedRefCount': len(restored), 'exactTreeFiles': len(entries),
                'runtimeBuildExecuted': False}


def exportGit(root, commit, output):
    """Export a full SHA to a new external directory and return its honest receipt.

    Inputs: repository root, exact 40-character commit SHA, and nonexistent output
    directory. Outputs: deterministic source tar.gz, full source contents, a union
    bundle, refs/tree manifests, and verification JSON. Errors fail closed; no
    references or source files are rewritten. Existing output is never overwritten.
    Example: exportGit(Path.cwd(), exactCommit, Path('/tmp/new-source-export')).
    """
    root, output = Path(root).resolve(), Path(output).resolve()
    if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
        raise ValueError('Export requires an exact full commit SHA')
    if output.is_relative_to(root):
        raise ValueError('Export output must be outside the source repository')
    if output.exists():
        raise ValueError('Export requires a new output directory')
    git = Git(root)
    top = git.run('rev-parse', '--show-toplevel').decode().strip()
    if Path(top).resolve() != root:
        raise ValueError('Export root must be the repository top-level worktree')
    selected = git.run('rev-parse', '--verify', commit + '^{commit}').decode().strip()
    if selected != commit:
        raise ValueError('Export commit must directly identify the exact commit object')
    release = loadReleaseIdentity(root, commit, requireWorktreeMatch=False)
    refs = git.refs()
    for name in refs:
        # Non-commit refs require an additional object-content policy; refuse
        # rather than preserve an object the reachable-tree audit cannot inspect.
        try:
            git.run('rev-parse', '--verify', name + '^{commit}')
        except ValueError as error:
            raise ValueError('Named ref does not peel to an auditable commit: ' + name) from error
    head = git.run('rev-parse', 'HEAD').decode().strip()
    # A full clone cannot prove an undisclosed earlier history closure.
    if git.run('rev-parse', '--is-shallow-repository').strip() != b'false':
        raise ValueError('A shallow repository cannot supply complete union history')
    audit = auditHistory(git, selected)
    tree = git.run('rev-parse', selected + '^{tree}').decode().strip()
    entries = treeEntries(git, tree)
    epoch = int(git.run('show', '-s', '--format=%ct', selected).strip())
    prefix = release['artifactPrefix'] + '-' + selected[:12]
    output.mkdir(parents=True)
    archive = output / (prefix + '-Source.tar.gz')
    bundle = output / (prefix + '-History.bundle')
    document = output / (prefix + '-Full-Source.md')
    files = writeSource(root, entries, epoch, archive, document, release)
    git.run('-c', 'pack.threads=1', 'bundle', 'create', str(bundle), '--all')
    bundleHeads = dict((line.split(' ', 1)[1], line.split(' ', 1)[0]) for line in
                       git.run('bundle', 'list-heads', str(bundle)).decode().splitlines())
    if {name: bundleHeads.get(name) for name in refs} != refs or bundleHeads.get('HEAD') != head:
        raise ValueError('Union bundle does not retain the complete named-ref snapshot and HEAD')
    integrity = verifyFresh(git, bundle, archive, refs, entries, selected, tree, epoch)
    if git.refs() != refs or git.run('rev-parse', 'HEAD').decode().strip() != head:
        raise ValueError('Source refs changed during export; repeat once commits are frozen')
    treeManifest = output / 'SOURCE-TREE.json'
    treeManifest.write_text(json.dumps({'sourceCommit': selected, 'sourceTree': tree, 'files': files},
                                       indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    refsManifest = output / 'NAMED-REFS.json'
    refsManifest.write_text(json.dumps({'HEAD': head, 'namedRefs': refs}, indent=2) + '\n')
    toolIdentity = {'gitVersion': git.run('--version').decode().strip(),
                    'pythonVersion': sys.version, 'zlibRuntimeVersion': zlib.ZLIB_RUNTIME_VERSION,
                    'exporterScriptSha256': fileRecord(Path(__file__).resolve())['sha256']}
    result = {
        'toolIdentity': toolIdentity,
        'schema': 'nocturne.git-source-export.v1', 'status': 'SOURCE_HISTORY_VERIFIED',
        'build': release['build'], 'sourceCommit': selected, 'sourceTree': tree,
        'sourceBaseline': release['sourceBaseline'], 'commitTimestamp': epoch,
        'sourceBytes': 'Exact committed Git blobs; working-tree edits and untracked files are not inputs.',
        'runtimeQualification': {'status': 'NOT_ASSESSED_BY_EXPORTER',
                                 'declaredFullRC4Qualified': release['fullRC4Qualified'],
                                 'declaredState': release['state'], 'declaredScope': release['scope'],
                                 'verificationPath': release['verification'],
                                 'reason': 'This verifies source and history integrity only. The SDK '
                                           'packager still requires a completed matching four-runtime pass.'},
        'reproducibility': {'tar': 'Sorted full Git tree, canonical modes/owners, commit mtime, gzip mtime 0 '
                                  'and empty filename. No export-ignore, export-subst, or checkout filters.',
                            'history': 'All named refs and HEAD preserve exact object IDs. Bundle byte '
                                       'identity across Git versions is not claimed.'},
        'namedRefs': refs, 'bundleHEAD': head, 'files': files, 'historyAudit': audit,
        'integrity': integrity, 'commands': git.commands,
        'artifacts': {'sourceTar': fileRecord(archive), 'historyBundle': fileRecord(bundle),
                      'sourceContents': fileRecord(document), 'treeManifest': fileRecord(treeManifest),
                      'refsManifest': fileRecord(refsManifest)},
    }
    receipt = output / 'EXPORT-VERIFICATION.json'
    receipt.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (output / 'SHA256SUMS.txt').write_text(''.join(
        fileRecord(path)['sha256'] + '  ' + path.name + '\n'
        for path in sorted(output.iterdir()) if path.is_file()), encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=REPOSITORY)
    parser.add_argument('--commit', required=True, help='Exact final 40-character commit SHA')
    parser.add_argument('--output', type=Path, required=True, help='New directory outside source')
    arguments = parser.parse_args()
    try:
        result = exportGit(arguments.root, arguments.commit, arguments.output)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('Source export refused: ' + str(error), file=sys.stderr)
        return 2
    print(json.dumps({'status': result['status'], 'sourceCommit': result['sourceCommit'],
                      'namedRefs': len(result['namedRefs']), 'files': len(result['files']),
                      'runtimeQualification': result['runtimeQualification']['status'],
                      'artifacts': result['artifacts']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
