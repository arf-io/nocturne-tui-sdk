#!/usr/bin/env python3
"""Validate the operator's nullification decisions and record what they strike.

Decisions follow native/contract/NULLIFICATION.schema.json. They come from the interactive review page as
a file (--decisions PATH) or a JSON paste on standard input (--decisions -), or they are the committed
native/contract/NULLIFICATION.json. A file or paste is the complete decision set and replaces the contract;
one that leaves out a committed decision withdraws it, restoring what it struck, and --apply refuses that
unless --allow-removal is given. The plan, with the contract change, is printed before the first write.
Every decision is validated and resolved against INVENTORY.json, native/catalogue.json,
native/port-ledger.json, native/recipes.json and docs/current/images/CAPTURES.json before anything is
written; any problem is reported, with every message, and nothing is written.

The default is a dry run: it prints the plan (what each decision strikes, the Gallery recipes it removes,
warnings, and the file each write would create, update or delete) and writes nothing. --apply holds an
exclusive lock on native/contract and then writes, each file atomically (temporary file, fsync, rename,
directory fsync) and in this order:

  native/evidence/artwork-inventory-20261031/NULLIFIED.json   every decision with everything it strikes
  native/evidence/artwork-inventory-20261031/INVENTORY.md     Nullified columns and "Nullified by the operator"
  docs/current                                               a new ledger; an interim Catalogue.md listing only
                                                             the identities documented before and after; the
                                                             family pages; the final Catalogue.md; the manifest;
                                                             a withdrawn ledger is deleted last
  native/contract/NULLIFICATION.json                          last, and only for --decisions

After every write each link and anchor of the reference pages resolves, so a run killed between two writes
leaves valid pages.

All outputs are functions of the decisions and the repository, so a rerun with the same decisions writes
nothing, and a run killed part way is completed by running it again. Until then build_reference_docs.py
--check reports the reference pages that lag the contract. The Gallery applies the contract when it is
built: rebuild the standalone page (build_gallery.py, or sh build-native.sh) and any HTTP bundle
(build_gallery_site.py) after applying.

Nothing is deleted. The C implementation, tests, fixtures and evidence of a nullified identity stay, the
native core still accepts and renders it, and docs/current/components.json keeps its engine observations.
Deleting a nullified identity from the core is a later, separately qualified step with its own tests and a
new qualification run (native/docs/NULLIFICATION.md). Rerunning assemble_artwork_inventory.py rewrites
INVENTORY.md without the Nullified columns, so apply after it.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import stat
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import nullification as N  # noqa: E402
import build_reference_docs as docs  # noqa: E402

TEMPORARY = '.nullification-tmp'
STUDIES = 'native/examples/gallery_cases.py'
LOCKED = 'native/contract is locked by another apply_nullification.py --apply; nothing was written'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def gallery_library(root):
    """The Gallery's recipe list as build_gallery.py assembles it: native/recipes.json, then the generated studies.

    The examples directory is put on sys.path resolved, so that a linked checkout (a scratch repository) imports the
    case builders, which find their fixtures beside their own files, from where they really are."""
    examples = str((Path(root) / 'native/examples').resolve())
    if examples not in sys.path:
        sys.path.insert(0, examples)
    from gallery_cases import build_cases
    return json.loads((Path(root) / N.RECIPES).read_text(encoding='utf-8')) + build_cases()


def read_paste(stdin):
    """The decisions pasted on standard input: the bytes of a real stream, refused unless they are UTF-8, or the text of
    an in-memory one."""
    buffer = getattr(stdin, 'buffer', None)
    return N.decode(buffer.read(), 'stdin') if buffer is not None else stdin.read()


def contract_change(current, proposed):
    """Decisions added, removed and changed by (scope, key), against the committed contract."""
    def index(document):
        rows = document.get('decisions') if isinstance(document, dict) else None
        return {(row.get('scope'), row.get('key')): row for row in rows or [] if isinstance(row, dict)}
    before, after = index(current), index(proposed)
    def listed(pairs):
        return [{'scope': scope, 'key': key} for scope, key in pairs]
    return {'added': listed(k for k in after if k not in before), 'removed': listed(k for k in before if k not in after),
            'changed': listed(k for k in after if k in before and after[k] != before[k])}


def prepare(root, source, stdin):
    """(plan, ordered [(relative path, bytes or None)]) for the decisions; raises NullificationError before any write."""
    root = Path(root)
    current = N.read_document(root / N.CONTRACT)
    if source is None:
        document, label = current, N.CONTRACT
        contract_bytes = (root / N.CONTRACT).read_bytes()
    else:
        if source == '-':
            document, label = N.parse_document(read_paste(stdin), 'stdin'), 'stdin'
        else:
            path = Path(source).resolve()
            document = N.read_document(path)
            label = path.relative_to(root.resolve()).as_posix() if path.is_relative_to(root.resolve()) else str(path)
        N.validate(document)
        contract_bytes = N.canonical_document(document).encode('utf-8')
    sources = N.Sources(root)
    resolved = N.resolve(document, sources)
    contract_scoped = [row for row in resolved if row['scope'] in N.CONTRACT_SCOPES]
    library = gallery_library(root) if contract_scoped else []
    gallery = N.gallery_effects(library, contract_scoped, sources) if contract_scoped else {}
    struck = {recipe for effect in gallery.values() for recipe in effect['ids']}
    controls = N.fixed_controls((root / N.TEMPLATE).read_text(encoding='utf-8'), library) if struck else {}
    for index, effect in gallery.items():
        row = next(r for r in resolved if r['decision'] == index)
        row['gallery'] = effect
        warned = set(row['strikes'].get('recipes', []))
        row['warnings'] += N.capture_warnings(sources.recipe_captures, [x for x in effect['ids'] if x not in warned])
        row['warnings'] += N.control_warnings(controls, struck, effect['ids'])
    totals = {**N.totals(resolved), 'galleryRecipes': len(struck)}
    contract_sha256 = sha256(contract_bytes)
    inputs = {name: {'path': path, 'sha256': sources.digest(path)} for name, path in (
        ('inventory', N.INVENTORY), ('catalogue', N.CATALOGUE), ('portLedger', N.PORT_LEDGER), ('recipes', N.RECIPES),
        ('captures', N.CAPTURES), ('components', N.COMPONENTS), ('template', N.TEMPLATE))}
    # The Gallery counts include the studies gallery_cases.py generates: their canonical JSON, read only when a decision
    # reaches the Gallery.
    studies = library[len(sources.recipes):] if contract_scoped else None
    inputs['galleryStudies'] = {'generator': STUDIES, 'sha256': None if studies is None else sha256(
        json.dumps(studies, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))}
    record = {'schema': N.RESOLVED_SCHEMA, 'statement': N.STATEMENT, 'contract': {'path': N.CONTRACT, 'sha256': contract_sha256},
              'inputs': inputs, 'totals': totals, 'decisions': resolved}
    files = [(N.NULLIFIED, (json.dumps(record, indent=2, ensure_ascii=False) + '\n').encode('utf-8')),
             (N.INVENTORY_MARKDOWN, N.inventory_markdown((root / N.INVENTORY_MARKDOWN).read_text(encoding='utf-8'), sources.inventory,
                                                         resolved, contract_sha256).encode('utf-8'))]
    # No page may link to a missing page or anchor, and the manifest may list no absent page, at any moment of an
    # interrupted run: build_reference_docs.nullified_docs_writes orders the reference writes (a new ledger first, an
    # interim index, the family pages, the final index and the manifest, a withdrawn ledger last).
    interim = [False] * len(files)
    for name, text, flag in docs.nullified_docs_writes(root / N.DOCS, resolved):
        files.append((N.DOCS + '/' + name, None if text is None else text.encode('utf-8')))
        interim.append(flag)
    if source is not None:
        files.append((N.CONTRACT, contract_bytes))
        interim.append(False)
    writes = actions(root, files)
    for write, flag in zip(writes, interim):
        if flag:
            write['interim'] = True
    files, writes = without_idle_interim(files, writes)
    plan = {'schema': 'nocturne.nullification-plan.v1', 'mode': 'dry-run', 'source': label, 'contract': N.CONTRACT,
            'contractChange': contract_change(current, document) if source is not None else {'added': [], 'removed': [], 'changed': []},
            'totals': totals,
            'decisions': [{'decision': row['decision'], 'scope': row['scope'], 'key': row['key'], 'name': row['name'],
                           'strikes': summary(row), 'gallery': {x: row['gallery'][x] for x in ('recipes', 'byReason', 'capturesLoadingStruckRecipes')}
                           if 'gallery' in row else None, 'warnings': row['warnings']} for row in resolved],
            'writes': writes, 'statement': N.STATEMENT,
            'next': ['Rebuild the Gallery (sh build-native.sh, or build_gallery.py) and any HTTP bundle (build_gallery_site.py) so they omit '
                     'the struck recipes from their library and attract rotation.',
                     'Commit native/contract, the inventory evidence and docs/current together; build_reference_docs.py --check verifies the pages.']}
    return plan, files


def actions(root, files):
    """What each write does to the bytes before it: those on disk, or those an earlier write of the same path (the
    interim index) leaves. create, update, delete or unchanged."""
    state, out = {}, []
    for name, data in files:
        path = Path(root) / name
        before = state[name] if name in state else (path.read_bytes() if path.is_file() else None)
        state[name] = data
        out.append({'path': name, 'action': 'unchanged' if data == before else 'delete' if data is None else
                    'create' if before is None else 'update'})
    return out


def without_idle_interim(files, writes):
    """files and writes without the half of an interim index that does nothing. An interim index equal to the bytes
    before it is dropped; the final index follows. One equal to the final index is that index, written as early as is
    safe, so it loses the interim label and the final write, which would leave it unchanged, is dropped. Each plan then
    lists a path once unless a real interim index precedes the final one, and the bytes written, in their order, are
    the same."""
    dropped = set()
    for position, ((name, data), write) in enumerate(zip(files, writes)):
        if not write.get('interim'):
            continue
        final = next(i for i in range(position + 1, len(files)) if files[i][0] == name)
        if write['action'] == 'unchanged':
            dropped.add(position)
        elif files[final][1] == data:
            del write['interim']
            dropped.add(final)
    return ([x for i, x in enumerate(files) if i not in dropped], [x for i, x in enumerate(writes) if i not in dropped])


def summary(row):
    s = row['strikes']
    if row['scope'] in N.HISTORICAL_SCOPES:
        return {'instances': len(s['instances'])}
    if row['scope'] == 'current-identity':
        return {'catalogue': s['catalogue']['id'], 'portLedger': s['portLedger']['oldId'] if s['portLedger'] else None,
                'recipes': s['recipes'], 'captures': s['captures'], 'docsPages': [x['page'] for x in s['docsPages']]}
    return dict(s)


def temporary(path):
    return path.with_name('.' + path.name + TEMPORARY)


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_atomically(path, data):
    """Replace path with data so that a reader or a kill sees either the old bytes or the new ones."""
    pending = temporary(path)
    with open(pending, 'wb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    if path.exists():
        os.chmod(pending, stat.S_IMODE(path.stat().st_mode))
    os.replace(pending, path)
    fsync_directory(path.parent)


def delete(path):
    path.unlink()
    fsync_directory(path.parent)


@contextlib.contextmanager
def contract_lock(root):
    """An exclusive advisory lock on the native/contract directory; the kernel releases it if the process dies."""
    descriptor = os.open(Path(root) / 'native/contract', os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(LOCKED) from None
        yield
    finally:
        os.close(descriptor)


def text_plan(plan):
    lines = ['Nullification plan (' + plan['mode'] + ') from ' + plan['source'] + ' for ' + plan['contract']]
    t = plan['totals']
    lines.append(str(t['decisions']) + ' decisions: ' + ', '.join(str(n) + ' ' + scope for scope, n in t['byScope'].items()))
    change = plan['contractChange']
    lines.append('Contract change: ' + str(len(change['added'])) + ' added, ' + str(len(change['removed'])) + ' removed, '
                 + str(len(change['changed'])) + ' changed')
    lines += ['  removes ' + row['scope'] + ' ' + N.quote(row['key']) for row in change['removed']]
    if change['removed']:
        lines.append('  --apply withdraws them only with --allow-removal')
    for row in plan['decisions']:
        lines.append('  decision ' + str(row['decision']) + ' ' + row['scope'] + ' ' + N.quote(row['key']) + ' (' + row['name'] + '): '
                     + json.dumps(row['strikes'], ensure_ascii=False))
        if row['gallery']:
            lines.append('    Gallery: ' + str(row['gallery']['recipes']) + ' recipes struck (' + ', '.join(
                reason + ' ' + str(n) for reason, n in row['gallery']['byReason'].items()) + ')')
        lines += ['    warning: ' + warning for warning in row['warnings']]
    lines.append('Totals: ' + str(t['historicalInstances']) + ' historical instances, ' + str(t['historicalDefinitions'])
                 + ' definitions, ' + str(t['historicalVariants']) + ' variants; ' + str(t['currentIdentities']) + ' current identities; '
                 + str(t['recipes']) + ' recipes, ' + str(t['galleryRecipes']) + ' Gallery recipes; ' + str(t['captures']) + ' captures')
    lines.append('Writes:')
    lines += ['  ' + w['action'] + ' ' + w['path'] + (' (interim index: only the identities documented before and after)' if w.get('interim') else '')
              for w in plan['writes'] if not (w.get('interim') and w['action'] == 'unchanged')]
    lines.append(plan['statement'])
    lines += ['Next: ' + x for x in plan['next']]
    return '\n'.join(lines)


def commit(root, files, writes, report=None):
    """Perform the planned writes in order, each atomically, skipping those planned as unchanged, after removing the
    temporary files a killed run left behind. report, if given, receives each 'wrote <path>' or 'deleted <path>' line
    as soon as that write is durable. Returns those lines."""
    root = Path(root)
    for name in sorted({name for name, _ in files}):
        stale = temporary(root / name)
        if stale.exists():
            stale.unlink()
    done = []
    for (name, data), write in zip(files, writes):
        if write['action'] == 'unchanged':
            continue
        if data is None:
            delete(root / name)
            done.append('deleted ' + name)
        else:
            write_atomically(root / name, data)
            done.append('wrote ' + name)
        if report:
            report(done[-1])
    return done


def main(argv=None, stdin=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', type=Path, default=HERE.parents[1], help='repository root (default: this checkout)')
    parser.add_argument('--decisions', help='decisions from the review page: a JSON file, or - for a paste on standard input')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true', help='print the plan and write nothing (the default)')
    mode.add_argument('--apply', action='store_true', help='write the records, the reference pages and the contract')
    parser.add_argument('--json', action='store_true', help='print the plan as JSON')
    parser.add_argument('--allow-removal', action='store_true',
                        help='let --decisions withdraw decisions the committed contract holds, restoring what they struck')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    stdin = sys.stdin if stdin is None else stdin
    with contract_lock(root) if args.apply else contextlib.nullcontext():
        try:
            plan, files = prepare(root, args.decisions, stdin)
        except N.NullificationError as error:
            print(str(error) + '\nnothing was written', file=sys.stderr)
            return 1
        if not args.apply:
            print(json.dumps(plan, indent=2, ensure_ascii=False) if args.json else text_plan(plan) + '\nDry run: nothing was written.')
            return 0
        removed = plan['contractChange']['removed']
        if removed and not args.allow_removal:
            print('\n'.join(['the decisions withdraw ' + str(len(removed)) + ' committed decision' + ('s' if len(removed) > 1 else '') + ':']
                            + ['  ' + row['scope'] + ' ' + N.quote(row['key']) for row in removed]
                            + ['pass --allow-removal to withdraw them', 'nothing was written']), file=sys.stderr)
            return 1
        plan['mode'] = 'apply'
        if not args.json:
            print(text_plan(plan), flush=True)
        done = commit(root, files, plan['writes'], None if args.json else lambda line: print(line, flush=True))
    if args.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print('Applied: ' + str(len(done)) + ' files written or deleted.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
