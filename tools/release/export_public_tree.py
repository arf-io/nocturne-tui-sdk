#!/usr/bin/env python3
"""Stage the public Nocturne source tree from this repository's tracked files.

The public tree is the SDK as a user builds it: the C core, the bindings and hosts, examples, tests, scripts, the
Gallery template and contracts, the current documentation, the qualification tools, and the original series of
explorations (legacy/ editions, the root edition pages, the Continuity bindings and the Studio sources) that the
Gallery's provenance gate pins. It leaves out the private record: handoffs, evidence, recovery notes, delivery
changelogs and internal audits, which stay in the private repository's history.

The synthetic test-fixture Gallery entries are left out too (operator decision 2026-11-14). The fixture generators are
the modules whose every entry in the provenance census is synthetic. The export drops each such module and its scene
data, the never-shipped test harness, and every test or check script that imports a removed module, reads removed data or
selects fixture entries from the Gallery library. A retained file that imports a removed module, or names a removed script,
stops the export. The report ships with the tree and carries what the public build needs to tell a tree that left the
fixtures out from a source tree that lost them: the number of fixture generators and a hash of their names (never the names),
the count of exclusions by reason, and the excluded paths a qualification plan can name. Each exclusion, with the generators'
names and the reason for every one, is written beside the tree (OUTPUT.exclusions.json), never inside it.

The output is a plain directory (no git history). A scan lists every remaining occurrence of internal host names,
workstation paths, account names and the names of other private projects (in the bytes of each file, and inside .gz and .zip
files) in a review file beside the tree (OUTPUT.private-strings.json, never inside it). A .gz is scanned as its header text
and its decompressed content, and a .zip as its names, comments and members, never as compressed bytes, where a short word
matches by chance. The pattern is data in
private_strings.json beside this tool, private-only like the prose-lint phrase list: the export refuses to run without it,
and --strict fails the export after the tree and the review files are written when any file matches (privateStringFiles).
legacy/ holds the historical originals, preserved byte for byte and pinned by hash, so it cannot be rewritten. Under legacy/ only,
the one string the data file lists as "legacyAllowed" (an upstream attribution) is not counted as a hit; every other match there
still is. The review file records each spared file and the number of matches spared (legacyExempt).
PUBLIC-TREE-REPORT.json ships with the tree, which reads it, and is kept free of
those strings and of every fixture generator's name. Without a LICENSE file the export stops unless --stage is given (staging for review only, never for
publication).

Gallery's case builder (native/examples/gallery_cases.py) calls each fixture generator through a fixture_study line. The
export drops those lines from the copy it stages, so the tree names no fixture generator there; any other mention of one in
that file stops the export.

The prose of the staged tree (Markdown and the HTML text of documentation pages) is checked by prose_lint.py for internal
process words and filler; legacy/ is exempt there (historical originals, preserved byte-for-byte, listed in the phrase list). The
report carries the count per file and the total (proseLint); the matched phrases are written
beside the tree (OUTPUT.prose-lint.json), never inside it. --strict makes a non-zero total fail the export after the tree
and the review files are written.

Usage: export_public_tree.py --output NEW_DIRECTORY [--stage] [--strict] [--source CHECKOUT]
"""
from pathlib import Path
import argparse, ast, gzip, hashlib, json, re, shutil, subprocess, sys, zipfile, zlib

ROOT = Path(__file__).resolve().parents[2]
PREFIXES = ('src/', 'include/', 'native/src/', 'native/include/', 'native/freestanding/', 'native/unicode/',
            'native/bindings/', 'native/hosts/', 'native/examples/', 'native/tests/', 'native/scripts/', 'native/web/',
            'native/contract/', 'docs/current/', 'tools/ci/', 'tools/qualification/', 'tools/release/', 'legacy/',
            'bindings/continuity/', 'integrations/', '.github/workflows/', '.forgejo/workflows/')
NAMES = {'README.md', 'CHANGELOG.md', 'CREDITS.md', 'RELEASE.json', 'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'build-native.sh',
         'run-native.sh', 'native-env.sh', 'qualify-native.sh', 'tools/bootstrap.py', 'tools/requirements-qualification.txt',
         'native/build.sh', 'native/run.sh', 'native/qualify.sh', 'native/recipes.json', 'native/palettes.json',
         'native/catalogue.json', 'native/port-ledger.json', 'native/.gitignore', '.gitignore',
         'Nocturne-Black-Hole.html', 'Nocturne-Continuity.html', 'Nocturne-Gallery.html', 'Nocturne-Kinetic.html',
         'Nocturne-Observatory.html', 'Nocturne-Pearl-Fleet.html', 'Nocturne-RC3.html', 'Nocturne-Restoration.html',
         'Nocturne-Studio.html', 'Nocturne-Workbench.html', 'Nocturne-Workbench-Docs.html'}
HARNESS = 'native/Nocturne-Test-Harness.html'
EXCLUDE = re.compile(r'(^|/)(evidence|handoffs?|recovery)(/|$)|native/web/reference-host\.html$|(^|/)Nocturne-Test-Harness\.html$')
PRIVATE_STRINGS = Path(__file__).with_name('private_strings.json')
LEGACY = 'legacy/'

CENSUS = 'native/evidence/provenance-census-20261114/PROVENANCE-CENSUS.json'
EXAMPLES = 'native/examples/'
# Python imports resolve against the importer's own directory, then these.
PY_ROOTS = ('native/examples', 'native/scripts', 'native/tests', 'native/bindings/python', 'tools/ci', 'tools/qualification')
# Only a test or check script leaves with a module it imports; any other file that imports one must be repaired by hand.
CASCADE = re.compile(r'^(native/tests/[^/]+|native/scripts/check_[^/]+\.py|native/bindings/typescript/[^/]+\.test\.mjs|tools/ci/(test|check)_[^/]+\.py)$')
# Files that name excluded scripts on purpose: the qualification plan (in a public tree it drops the steps whose files the
# report lists) and this tool (it names the private-only test it removes).
PLAN_FILES = {'native/scripts/qualify.py', 'native/scripts/resource_ownership_plan.py', 'native/scripts/rc2_release_plan.py',
              'tools/release/export_public_tree.py'}
CHECKS = 'native/scripts/check_'
HARNESS_NAME = 'Nocturne-Test-Harness.html'
# What marks a file as drawing on the Gallery library, where a fixture entry id or feature it names is a selection.
GALLERY_REFS = ('build_gallery', 'gallery_cases', 'nativeLab', HARNESS_NAME)
LITERAL = re.compile(r"""['\"]([A-Za-z0-9_-]{6,})['\"]""")
CODE = ('.py', '.sh', '.mjs', '.js', '.ts', '.go', '.rs', '.yml', '.yaml')
GALLERY_CASES = 'native/examples/gallery_cases.py'
FIXTURE_STUDY = re.compile(r"^\s*(\w+)=fixture_study\('(\w+)'\)\s*$")
PRIVATE_ONLY = {'native/tests/test_public_tree_fixtures.py':
                'checks this export against git history and the provenance census, which the public tree does not carry',
                'native/tests/test_rc2_release_plan.py':
                'asserts the exact private qualification plan, which the public tree filters by its report',
                'native/tests/test_nullification_private.py':
                'needs the artwork inventory, the mechanism document and the fixture Gallery entries, which the public tree does not carry',
                'native/tests/test_public_prose_lint.py': 'tests the export it belongs to, which needs the census; it plants the internal names it looks for',
                'tools/release/prose_lint.py': 'lints the tree before publication; its phrase list names the internal hosts and accounts',
                'tools/release/prose_lint_phrases.json': 'names the internal hosts and accounts the public prose must not carry',
                'tools/release/private_strings.json': 'is the pattern of private strings the tree must not carry, so it spells them',
                'native/tests/test_public_tree_private_strings.py': 'tests the export it belongs to, which needs the census, and reads the private pattern file',
                'native/examples/tdf_specimens.json': 'pre-rendered cells of a wordmark; the Gallery withholds them, and the TheDraw fonts that would re-render them are not distributed',
                'native/bindings/typescript/cargo-wrapper-lock.test.mjs': 'asserts the lock message of a private build wrapper that a public tree does not have'}


def tracked():
    out = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z'], capture_output=True, check=True).stdout
    return [p for p in out.decode().split('\0') if p]


def select(paths):
    return sorted(p for p in paths if (p in NAMES or p.startswith(PREFIXES)) and not EXCLUDE.search(p))


def fixture_generators(paths):
    """The generators whose every census entry is synthetic, each mapped to its one module: ({name: (path, entries)}, the
    ids of their entries, the ids of every other entry). A generator with no module at native/examples/NAME.py stops the export."""
    census = json.loads((ROOT / CENSUS).read_text())
    present, found = set(paths), {}
    for name, classes in sorted(census['byGenerator'].items()):
        if {c for c, n in classes.items() if n} != {'synthetic'}:
            continue
        path = EXAMPLES + name + '.py'
        if path not in present:
            raise SystemExit(f'Fixture generator {name} has no module {path}; map it before exporting')
        found[name] = (path, sum(classes.values()))
    entries = census['entries']
    return found, {e['id'] for e in entries if e['generator'] in found}, {e['id'] for e in entries if e['generator'] not in found}


def imports(path, by_path, by_stem):
    """The selected Python files `path` imports: import statements and importlib.import_module of a literal name."""
    try:
        tree = ast.parse((ROOT / path).read_text(encoding='utf-8'))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return set()
    dotted = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            dotted.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                dotted.add(node.module)
                dotted.update(node.module + '.' + a.name for a in node.names)
            else:
                dotted.update(a.name for a in node.names)
        elif (isinstance(node, ast.Call) and getattr(node.func, 'attr', getattr(node.func, 'id', '')) == 'import_module'
              and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            dotted.add(node.args[0].value)
    here, hit = str(Path(path).parent), set()
    for name in dotted:
        if name.replace('.', '/') + '.py' in by_path:
            hit.add(name.replace('.', '/') + '.py')
        for candidate in by_stem.get(name.split('.')[0], ()):
            if str(Path(candidate).parent) == here or str(Path(candidate).parent) in PY_ROOTS:
                hit.add(candidate)
    return hit


def owned_prefixes(fixture_ids, kept_ids):
    """Entry-id prefixes (ending in a hyphen) that only fixture entries carry: a check that selects Gallery entries by one is
    a check of fixtures."""
    def prefixes(entry):
        return {entry[:i + 1] for i, c in enumerate(entry) if c == '-'}
    kept = set().union(*(prefixes(i) for i in kept_ids)) | set(kept_ids)
    return set().union(*(prefixes(i) for i in fixture_ids)) - kept


def fixture_labels(fixture_ids, kept_ids):
    """What a test or check names when it picks fixture entries out of the Gallery library: the entry ids and the features
    only fixtures demonstrate (hyphenated, so a bare word such as "input" is never one)."""
    probe = ('import json,sys;sys.path.insert(0,sys.argv[1]);import gallery_cases\n'
             'print(json.dumps([[c["id"],c.get("demonstrates",{}).get("feature")] for c in gallery_cases.build_cases()]))')
    out = subprocess.run([sys.executable, '-c', probe, str(ROOT / 'native/examples')], capture_output=True, check=True, text=True).stdout
    rows = json.loads(out)
    shared = {f for i, f in rows if i in kept_ids}
    return set(fixture_ids) | {f for i, f in rows if i in fixture_ids and f and '-' in f and f not in shared}


def fixture_data(paths, ids):
    """Scene data under native/examples whose every case is a fixture entry: a JSON list of cases, each with an id."""
    found = {}
    for path in paths:
        if path.startswith(EXAMPLES) and path.endswith('.json'):
            try:
                cases = json.loads((ROOT / path).read_text(encoding='utf-8'))
            except (ValueError, OSError):
                continue
            named = [c.get('id') for c in cases if isinstance(c, dict)] if isinstance(cases, list) else []
            if named and len(named) == len(cases) and all(n in ids for n in named):
                found[path] = len(named)
    return found


def shipped_exclusions(listed, fixtures):
    """The exclusions the shipped report lists: those no fixture generator's name appears in, which are the only ones a shipped
    qualification plan can name. An entry whose path carries a generator's name is counted (excludedByReason) and left to the
    private exclusion file; one whose detail or cause carries a name is listed with that text made generic."""
    named = re.compile('|'.join(map(re.escape, sorted(fixtures)))) if fixtures else None
    kept = []
    for entry in listed:
        if entry['reason'] == 'fixtureGenerator' or (named and named.search(entry['path'])):
            continue
        entry = dict(entry)
        if named and named.search(entry['detail']):
            entry['detail'] = 'refers to an excluded fixture generator'
        if named and named.search(entry.get('cause', '')):
            del entry['cause']
        kept.append(entry)
    return kept


def exclusions(paths):
    """Split the selected paths: (kept, excluded, fixtures). `excluded` maps path -> {reason, detail[, cause]}."""
    fixtures, ids, kept_ids = fixture_generators(paths)
    labels = fixture_labels(ids, kept_ids)
    owned = owned_prefixes(ids, kept_ids) | labels
    excluded = {path: {'reason': 'fixtureGenerator', 'detail': f'every one of its {n} census entries is synthetic ({name})'}
                for name, (path, n) in fixtures.items()}
    excluded.update({p: {'reason': 'privateOnly', 'detail': why} for p, why in PRIVATE_ONLY.items() if p in paths})
    excluded.update({p: {'reason': 'fixtureData', 'detail': f'{n} cases, every one a fixture entry'} for p, n in fixture_data(paths, ids).items()})
    text = {p: (ROOT / p).read_text(encoding='utf-8', errors='replace') for p in paths if p.endswith(CODE)}
    py = [p for p in paths if p.endswith('.py')]
    by_path, by_stem = set(py), {}
    for p in py:
        by_stem.setdefault(Path(p).stem, []).append(p)
    graph = {p: imports(p, by_path, by_stem) for p in py}

    def naming(names):
        return re.compile(r'(?<![\w.-])(' + '|'.join(re.escape(n) for n in sorted(names)) + r')(?![\w])')

    stuck, changed = {}, True
    while changed:
        changed = False
        stuck = {}
        gone = {e for e, why in excluded.items() if why['reason'] != 'privateOnly'}
        pattern = naming({Path(e).name for e in gone if e.endswith(('.py', '.json'))})
        for p in text:
            if p in excluded or p in PLAN_FILES:
                continue
            hit = sorted(graph.get(p, set()) & gone - {p})
            selects = []
            if CASCADE.match(p):
                literals = set(LITERAL.findall(text[p]))
                if p.startswith(CHECKS) and HARNESS_NAME in text[p]:
                    selects = sorted(literals & owned)
                elif any(ref in text[p] for ref in GALLERY_REFS):
                    selects = sorted(literals & labels)
            named = sorted(set(pattern.findall(text[p])) - {Path(p).name})
            if not hit and not named and not selects:
                continue
            if CASCADE.match(p):
                excluded[p] = ({'reason': 'importsExcludedModule', 'detail': 'imports ' + ', '.join(hit), 'cause': hit[0]} if hit else
                               {'reason': 'readsExcludedFile', 'detail': 'names ' + ', '.join(named), 'cause': named[0]} if named else
                               {'reason': 'selectsFixtureEntries', 'detail': 'selects fixture Gallery entries by ' + ', '.join(selects), 'cause': selects[0]})
                changed = True
                continue
            users = sorted(q for q in py if p in graph[q])
            if hit and p.startswith(EXAMPLES) and users and all(u in excluded for u in users):
                excluded[p] = {'reason': 'fixtureHelper', 'detail': 'imports excluded modules and is imported only by excluded modules: '
                               + ', '.join(Path(u).stem for u in users), 'cause': hit[0]}
                changed = True
            else:
                stuck[p] = hit or named or selects
    if stuck:
        raise SystemExit('Retained files import or name excluded fixture files; make each tolerate the absence or exclude it by rule:\n'
                         + '\n'.join(f'  {p}: {", ".join(h)}' for p, h in sorted(stuck.items())))
    return [p for p in paths if p not in excluded], excluded, fixtures


def strip_fixture_studies(text, fixtures):
    """gallery_cases.py without the lines that build the fixture generators: each `build_X=fixture_study('name')` and the
    `cases.extend(build_X())` after it. A fixture generator named anywhere else in the file stops the export."""
    lines, kept, skip = text.split('\n'), [], None
    for line in lines:
        if skip is not None:
            if line.strip() != f'cases.extend({skip}())':
                raise SystemExit(f'{GALLERY_CASES}: the fixture_study line for {skip} is not followed by cases.extend({skip}())')
            skip = None
            continue
        found = FIXTURE_STUDY.match(line)
        if found and found.group(2) in fixtures:
            skip = found.group(1)
            continue
        kept.append(line)
    if skip is not None:
        raise SystemExit(f'{GALLERY_CASES}: the fixture_study line for {skip} ends the file')
    stripped = '\n'.join(kept)
    left = sorted({m.group(1) for m in re.finditer(r'(?<![\w-])(' + '|'.join(map(re.escape, sorted(fixtures))) + r')(?![\w-])', stripped)}) if fixtures else []
    if left:
        raise SystemExit(f'{GALLERY_CASES} still names fixture generators after the fixture_study lines are dropped: {", ".join(left)}')
    return stripped


_private = None


def load_private_strings():
    """(the compiled pattern of private strings, the compiled legacy allowance), read from private_strings.json beside this tool the
    first time either is needed. The file is private-only (the public tree leaves it out), so a copy of this tool without it
    refuses to run. The allowance is optional; without it nothing under legacy/ is spared."""
    global _private
    if _private is None:
        try:
            data = json.loads(PRIVATE_STRINGS.read_text(encoding='utf-8'))
            pattern, allowed = data['pattern'], data.get('legacyAllowed', '(?!)')
            if not isinstance(pattern, str) or not pattern:
                raise ValueError('"pattern" must be a non-empty string')
            if not isinstance(allowed, str) or not allowed:
                raise ValueError('"legacyAllowed" must be a non-empty string when present')
            _private = re.compile(pattern.encode('utf-8'), re.I), re.compile(allowed.encode('utf-8'), re.I)
        except (OSError, ValueError, KeyError, TypeError, re.error) as e:
            raise SystemExit(f'The export is refusing to run: the private-string pattern {PRIVATE_STRINGS} is missing or unusable ({e}). '
                             'The file is private-only, and a tree cannot be checked without it.') from None
    return _private


def private_pattern():
    return load_private_strings()[0]


def legacy_allowance():
    return load_private_strings()[1]


def gzip_header_text(data):
    """The text fields of a gzip header (extra field, file name, comment), where a name can be written without being compressed."""
    flags, pos, found = data[3], 10, []
    if flags & 4:
        size = int.from_bytes(data[pos:pos + 2], 'little')
        found.append(data[pos + 2:pos + 2 + size])
        pos += 2 + size
    for bit in (8, 16):
        if flags & bit:
            end = data.index(0, pos)
            found.append(data[pos:end])
            pos = end + 1
    return found


def payloads(path):
    """The byte strings of one file to scan. A .gz is scanned as its header text and what it decompresses to; a .zip as its
    names, comments and members: a private string compressed inside a fixture is still in the tree, while the compressed bytes
    themselves are noise that a short word can match by chance. A file that is not a readable archive is scanned as it is."""
    data = path.read_bytes()
    try:
        if path.suffix in ('.gz', '.tgz'):
            found = [*gzip_header_text(data), gzip.decompress(data)]
        elif path.suffix == '.zip':
            found = []
            with zipfile.ZipFile(path) as z:
                found.append(z.comment)
                for info in z.infolist():
                    found.extend((info.filename.encode('utf-8'), info.comment, info.extra, z.read(info)))
        else:
            found = [data]
    except (OSError, EOFError, ValueError, IndexError, zlib.error, zipfile.BadZipFile):
        found = [data]
    yield from found


def scan(root, files):
    """({file: sorted private strings it holds}, {file: how many matches of the legacy allowance it carries}), over the bytes of
    every file so that no file is skipped for how it decodes. Under legacy/ the one string private_strings.json lists as allowed
    is not a hit (the originals are preserved byte for byte); anything else the pattern matches there still is."""
    pattern, allowed, hits, exempt = private_pattern(), legacy_allowance(), {}, {}
    for rel in files:
        found, spared = set(), 0
        for data in payloads(root / rel):
            if rel.startswith(LEGACY):
                data, spared_now = allowed.subn(b'\0', data)
                spared += spared_now
            found.update(m.group(0).decode('utf-8', 'replace').lower() for m in pattern.finditer(data))
        if found:
            hits[rel] = sorted(found)
        if spared:
            exempt[rel] = spared
    return hits, exempt


def main():
    global ROOT
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--stage', action='store_true', help='allow a tree without LICENSE, for review only')
    p.add_argument('--strict', action='store_true', help='fail when the prose lint finds anything or a private string is in any file (the tree is still written)')
    p.add_argument('--source', type=Path, default=ROOT, help='export from this checkout instead of the one this tool is in')
    a = p.parse_args()
    ROOT = a.source.resolve()
    private_pattern()
    if a.output.exists():
        p.error(f'{a.output} exists; give a new directory')
    selected = select(tracked())
    files, excluded, fixtures = exclusions(selected)
    if not any(f in files for f in ('LICENSE', 'LICENSE.md', 'LICENSE.txt')) and not a.stage:
        raise SystemExit('No LICENSE file: the operator must choose the license before a public tree is produced (use --stage to review)')
    for rel in files:
        target = a.output / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel == GALLERY_CASES:
            target.write_text(strip_fixture_studies((ROOT / rel).read_text(encoding='utf-8'), set(fixtures)), encoding='utf-8')
            shutil.copystat(ROOT / rel, target)
        else:
            shutil.copy2(ROOT / rel, target)
    hits, exempt = scan(a.output, files)
    import prose_lint  # imported here: the public tree leaves the lint out, and this file ships in it
    lint = prose_lint.lint_tree(a.output, files)
    lint_review = a.output.with_name(a.output.name + '.prose-lint.json')
    review = a.output.with_name(a.output.name + '.private-strings.json')
    size = sum((a.output / f).stat().st_size for f in files)
    listed = [{'path': path, **why} for path, why in sorted(excluded.items())]
    listed.append({'path': HARNESS, 'reason': 'testHarness',
                   'detail': 'generated by build_gallery.py with every study and no admission; a test artefact, never shipped'})
    by_reason = {}
    for entry in listed:
        by_reason[entry['reason']] = by_reason.get(entry['reason'], 0) + 1
    shipped = shipped_exclusions(listed, fixtures)
    names = sorted(fixtures)
    report = {'schema': 'nocturne.public-tree.v3', 'files': len(files), 'bytes': size,
              'license': next((f for f in files if f.startswith('LICENSE')), None), 'stagedOnly': a.stage,
              'selectedFiles': len(selected), 'selectedBytes': sum((ROOT / f).stat().st_size for f in selected),
              'fixtureSource': CENSUS,
              'fixtureGenerators': {'count': len(names), 'sha256': hashlib.sha256(''.join(n + '\n' for n in names).encode()).hexdigest()},
              'fixtureEntries': sum(n for _, n in fixtures.values()),
              'excludedByReason': dict(sorted(by_reason.items())), 'excludedListed': len(shipped),
              'excludedNotListed': len(listed) - len(shipped), 'excluded': shipped,
              'privateStringFiles': len(hits), 'proseLint': {'total': lint['total'], 'files': lint['files']}}
    text = json.dumps(report, indent=1) + '\n'
    if private_pattern().search(text.encode('utf-8')):
        raise SystemExit('The report itself names a private string; it ships with the tree and must stay clean')
    if names and re.search('|'.join(map(re.escape, names)), text):
        raise SystemExit('The report itself names a fixture generator; it ships with the tree and must stay clean')
    (a.output / 'PUBLIC-TREE-REPORT.json').write_text(text)
    # The matched strings are for the operator's review only: beside the tree, never in it.
    review.write_text(json.dumps({'schema': 'nocturne.public-tree-private-strings.v1', 'privateStrings': hits, 'legacyExempt': exempt}, indent=1) + '\n')
    # Every exclusion, and the generators' names the shipped report leaves out, are for the operator's review as well.
    exclusions_review = a.output.with_name(a.output.name + '.exclusions.json')
    exclusions_review.write_text(json.dumps({'schema': 'nocturne.public-tree-exclusions.v1', 'fixtureGenerators': names,
                                             'excluded': listed}, indent=1) + '\n')
    # The phrases found are internal words by definition: they too stay beside the tree.
    lint_review.write_text(json.dumps({'schema': 'nocturne.public-tree-prose-lint.v1', 'total': lint['total'], 'exemptFiles': lint['exemptFiles'], 'findings': lint['findings']}, indent=1) + '\n')
    print(json.dumps({**{k: v for k, v in report.items() if k not in ('excluded', 'proseLint')},
                      'proseLint': {'total': lint['total'], 'files': len(lint['files'])}, 'privateStringsFile': str(review), 'exclusionsFile': str(exclusions_review),
                      'proseLintFile': str(lint_review)}))
    failures = []
    if a.strict and hits:
        failures.append(f'{len(hits)} files carry a private string (--strict); see {review}\n' + '\n'.join(f'  {path}' for path in sorted(hits)[:10]))
    if a.strict and lint['total']:
        worst = sorted(lint['files'].items(), key=lambda kv: (-kv[1], kv[0]))[:10]
        failures.append(f'prose lint found {lint["total"]} phrases in {len(lint["files"])} files (--strict); see {lint_review}\n'
                        + '\n'.join(f'  {n:5d}  {path}' for path, n in worst))
    if failures:
        raise SystemExit('\n'.join(failures))


if __name__ == '__main__':
    main()
