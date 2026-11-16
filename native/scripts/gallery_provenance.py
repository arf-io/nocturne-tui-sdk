#!/usr/bin/env python3
"""Gallery provenance: which Gallery entries are original Nocturne artwork, and the admission gate built on it.

The Gallery admits only artwork whose provenance resolves to the original series of explorations
(0.1 .. 0.9.0-rc.3). native/contract/GALLERY-ADMISSION.json is the committed admission ledger: the pinned
original corpus, the admitted entry ids with their evidence, and the operator's decisions on RC4-era work.
native/scripts/build_gallery.py admits only the ledger's ids (it needs no legacy files, so a packaged SDK builds the
same Gallery). native/tests/test_gallery_admission.py recomputes the ledger from the repository and fails on any
drift, so an entry without provenance cannot enter the Gallery and the corpus cannot be edited to make a claim resolve.

Every entry the Gallery ships (native/recipes.json plus every study of native/examples/gallery_cases.py) is
put in exactly one class, by rules that read only repository bytes:

  original            A verified claim to an original exploration (0.1 .. 0.9.0-rc.3), shown on its own.
  original-framed     The same verified original, wrapped in the invented "application" frame
                      (application() of examples/screen_backdrop.py or the catalogue application backdrop); its isolated twin
                      carries the original.
  unresolved-claim    Claims an original source, but the claim does not resolve against the original corpus.
  rc4-authored        A composition authored in the RC4 era (2026-09-23 onward) whose subject has no original
                      source; operator review.
  synthetic           No provenance claim at all: a contract, semantics or parameter fixture rendered as a
                      screen. Not artwork of the original series.

A claim resolves when one of these holds:
  - sourceIdentity / demonstrates.effect / catalogueEffect is a native/port-ledger.json newId or oldId whose
    source file exists with the recorded SHA-256 and contains the old identity's leaf name (case-insensitive);
  - originalEffect / originalScene / originalScenic is a token present in an original-corpus file;
  - provenance.htmlSha256 is the SHA-256 of an original-corpus file (git history included);
  - the generator is a declared source route (SOURCE_ROUTES) whose original token is present in its edition.

The original corpus is legacy/ (editions and the Atelier v0.5 SDK snapshot), the root edition pages, the
Continuity bindings and root src/*.inc, plus the exact 0.9.0-rc.2 Workbench Docs page from git history
(legacy/editions/0.9-rc.2-Nocturne-Workbench-Docs.html, extracted byte-for-byte from 4e5e31cb, SHA-256 375c4468...).

Usage:
  gallery_provenance.py --write-ledger                 # recompute native/contract/GALLERY-ADMISSION.json
  gallery_provenance.py --check                        # exit 1 if the committed ledger differs from the recomputation
  gallery_provenance.py --census CENSUS.json --output DIR   # review report with render measures (census from
                                                            # render_gallery_census.py); writes only into DIR
"""
from pathlib import Path
import argparse, collections, hashlib, importlib, json, re, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / 'native'
CLAIM_FIELDS = ('provenance', 'sourceIdentity', 'originalScene', 'originalEffect', 'originalScenic')
ROOT_EDITIONS = ['Nocturne-Black-Hole.html', 'Nocturne-Continuity.html', 'Nocturne-Gallery.html', 'Nocturne-Kinetic.html',
                 'Nocturne-Observatory.html', 'Nocturne-Pearl-Fleet.html', 'Nocturne-RC3.html', 'Nocturne-Restoration.html',
                 'Nocturne-Studio.html', 'Nocturne-Workbench.html', 'Nocturne-Workbench-Docs.html']
# Generators that recreate an original family without a per-study claim field: edition file and the token that
# must be present in it. The profile of each study (demonstrates.profile) must also be present in that file.
SOURCE_ROUTES = {
    'atelier_studies': ('legacy/editions/0.5-atelier-Nocturne-Spatial-Atelier.html', 'embers'),
    'kinetic_studies': ('legacy/editions/0.5-kinetic-Nocturne-Kinetic.html', 'embers'),
    'observatory_studies': ('legacy/editions/0.4-Nocturne-Observatory.html', 'ripples'),
    'world_shell_source_studies': ('legacy/editions/0.7-Nocturne-Black-Hole.html', 'nova'),
    'world_shell_studies': ('legacy/editions/0.7-Nocturne-Black-Hole.html', 'fibonacci'),
    'world_nova_optics_studies': ('legacy/editions/0.7-Nocturne-Black-Hole.html', 'nova'),
    'studio_nova_studies': ('src/studio.inc', 'NOVA'),
    'corona_studies': ('bindings/continuity/observatory.js', 'nova'),
    'thermal_studies': ('bindings/continuity/effect-catalog.js', 'embers'),
}
# Native recipes whose subject is a ported original effect are composed in RC4 around that effect; the rest are
# RC4 showcase compositions.
# Edition keywords in a provenance release string -> substrings of the original-corpus file names of that edition.
EDITIONS = {
    'v0.1': ('0.1-Nocturne-Gallery', 'Gallery-v0.1'),
    'studio': ('Studio', 'src/'),
    'pearl': ('Pearl-Fleet', 'src/'),
    'atelier': ('atelier',),
    'observatory': ('Observatory', 'Workbench'),
    'workbench': ('Workbench',), 'rc2': ('Workbench',), '0.9.0-rc.2': ('Workbench',),
    'black hole': ('Black-Hole',),
    'continuity': ('Continuity', 'bindings/continuity'),
    'kinetic': ('Kinetic',),
    'restoration': ('Restoration',),
}
EDITION_WORDS = {'workbench', 'black', 'hole', 'pearl', 'studio', 'fleet', 'observatory', 'atelier', 'kinetic', 'continuity',
                 'restoration', 'spatial', 'rc2', 'nocturne', 'gallery', 'original'}
# Words too common to evidence anything on their own.
GENERIC = {'original', 'through', 'current', 'native', 'actual', 'assembled', 'model', 'composition', 'with', 'from', 'scene',
           'layers', 'host', 'composer', 'world', 'painter', 'controls', 'window', 'text', 'later', 'revision', 'source', 'stage',
           'source-stage', 'components', 'complete', 'application', 'renderer', 'ingress', 'modal', 'retained', 'layer',
           'nocturne', 'gallery', 'primitives', 'rule', 'analytical', 'sky', 'eight', 'restore', 'clear', 'retain', 'active',
           'stack', 'context', 'widgets', 'weather', 'subfont', 'nondismissible', 'dismissible', 'box', 'boxes'}


def original_corpus():
    files = {}
    for path in sorted((ROOT / 'legacy').rglob('*')):
        if path.is_file() and path.suffix in ('.html', '.js', '.ts', '.json', '.c', '.h', '.inc', '.md', '.py', '.go', '.rs'):
            files[str(path.relative_to(ROOT))] = path.read_bytes()
    for name in ROOT_EDITIONS:
        files[name] = (ROOT / name).read_bytes()
    for path in (sorted((ROOT / 'bindings/continuity').glob('*.js')) + sorted((ROOT / 'src').glob('*.inc'))
                 + sorted(p for p in (ROOT / 'native/tests/fixtures/first-prompt-v01').rglob('*') if p.is_file())):
        files[str(path.relative_to(ROOT))] = path.read_bytes()
    # The exact 0.9.0-rc.2 Workbench Docs page (SHA-256 375c4468...) is legacy/editions/0.9-rc.2-Nocturne-Workbench-Docs.html,
    # extracted byte-for-byte from 4e5e31cb:Nocturne-Workbench-Docs.html, so the corpus needs no git history.
    return files


class Resolver:
    def __init__(self):
        self.corpus = original_corpus()
        self.hashes = {hashlib.sha256(b).hexdigest(): name for name, b in self.corpus.items()}
        self.lower = {name: b.decode('utf-8', 'replace').lower() for name, b in self.corpus.items()}
        ledger = json.loads((NATIVE / 'port-ledger.json').read_text())['entries']
        self.ledger = {}
        for e in ledger:
            src = ROOT / e['source']['path']
            ok = src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest() == e['source']['sha256']
            leaf = re.split(r'[/.]', e['oldId'])[-1].lower()
            text = src.read_text(errors='replace').lower() if src.is_file() else ''
            ok = ok and any(form in text for form in (leaf, leaf[:-1] if leaf.endswith('s') else leaf))
            row = {'newId': e['newId'], 'oldId': e['oldId'], 'source': e['source']['path'], 'verified': bool(ok)}
            self.ledger[e['newId']] = row
            self.ledger[e['oldId']] = row

    @staticmethod
    def forms(word):
        t = str(word).lower()
        return {t, t.replace('-', ' '), t.replace('-', ''), t.replace('-', '_')}

    def token(self, word):
        forms = self.forms(word)
        return sorted(name for name, text in self.lower.items() if any(f in text for f in forms))

    def edition_files(self, text):
        t = text.lower()
        keys = [k for k in EDITIONS if k in t]
        return sorted({n for k in keys for n in self.lower if any(p in n for p in EDITIONS[k])})

    def provenance(self, prov, entry):
        """A provenance object resolves by bytes (htmlSha256/sourceSha256 of an original-corpus file, every
        componentSources path at its SHA-256, a sourceObjectSha256 or kernelSha256 of a preserved original file); the study's own
        family/preset/profile word must then be present in the matched file. Without byte evidence, a
        component-specific word (not a generic or edition word) must be present in the files of the edition the
        claim names."""
        demo = entry.get('demonstrates') or {}
        subject = next((demo[k] for k in ('family', 'preset', 'profile') if k in demo), None)
        notes, matched = [], []
        for field in ('htmlSha256', 'sourceSha256', 'sourceObjectSha256', 'kernelSha256'):
            sha = prov.get(field)
            if sha:
                if sha not in self.hashes:
                    return False, [f"{field} {sha[:12]} matches no original-corpus file"]
                matched.append(self.hashes[sha])
                notes.append(f"{field} {sha[:12]} = {self.hashes[sha]}")
        for src in prov.get('componentSources') or []:
            if 'htmlSha256' in src:
                if src['htmlSha256'] not in self.hashes:
                    return False, [f"componentSources '{src.get('component')}' htmlSha256 {src['htmlSha256'][:12]} matches no original-corpus file"]
                matched.append(self.hashes[src['htmlSha256']])
                notes.append(f"componentSources '{src.get('component')}' = {self.hashes[src['htmlSha256']]}")
                continue
            path = ROOT / src['path']
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != src['sha256']:
                return False, [f"componentSources {src['path']} absent or not at {src['sha256'][:12]}"]
            matched.append(src['path'])
            notes.append(f"componentSources {src['path']} at {src['sha256'][:12]}")
        if notes:
            # A source commit is history, not bytes: it never resolves a claim alone (a public tree has no history).
            matched.extend(self.edition_files(prov.get('release', '')))
        if notes:
            if subject is not None and matched:
                texts = [self.lower.get(m) or (ROOT / m).read_text(errors='replace').lower() for m in matched]
                if not any(f in t for t in texts for f in self.forms(subject)):
                    return False, notes + [f"subject '{subject}' absent from {matched[0]}"]
                notes.append(f"subject '{subject}' present in {matched[0]}")
            return True, notes
        text = (prov.get('release', '') + ' ' + prov.get('component', '')).strip()
        files = self.edition_files(text) or list(self.lower)
        words = [w for w in re.findall(r'[A-Za-z][A-Za-z0-9-]{3,}', prov.get('component', '')) if w.lower() not in GENERIC | EDITION_WORDS]
        hits = [w for w in words if any(f in self.lower[n] for n in files for f in self.forms(w))]
        if hits:
            return True, [f"provenance '{text}': specific words {hits[:4]} present in the named edition ({len(files)} files)"]
        return False, [f"provenance '{text}' names nothing specific that the named edition contains"]

    def identity(self, ident):
        row = self.ledger.get(ident)
        return row if row and row['verified'] else None

    def claim(self, entry, generator):
        """(claimed, resolved, evidence list)."""
        evidence, claimed, failures = [], False, []
        if 'sourceIdentity' in entry:
            claimed = True
            row = self.identity(entry['sourceIdentity'])
            (evidence if row else failures).append(f"sourceIdentity {entry['sourceIdentity']}" + (f" -> {row['source']}" if row else ' not in verified ledger'))
        for field in ('originalEffect', 'originalScene', 'originalScenic'):
            if field in entry:
                claimed = True
                files = self.token(entry[field])
                (evidence if files else failures).append(f"{field} '{entry[field]}' " + (f"in {len(files)} original files (e.g. {files[0]})" if files else 'absent from original corpus'))
        prov = entry.get('provenance')
        if isinstance(prov, dict):
            claimed = True
            ok, notes = self.provenance(prov, entry)
            (evidence if ok else failures).extend(notes)
        if generator in SOURCE_ROUTES:
            claimed = True
            path, tok = SOURCE_ROUTES[generator]
            profile = (entry.get('demonstrates') or {}).get('profile')
            text = self.lower.get(path) or (ROOT / path).read_text(errors='replace').lower()
            ok = tok.lower() in text and (profile is None or str(profile).lower() in text)
            (evidence if ok else failures).append(f"source route {generator}: {path} " + ('contains' if ok else 'lacks') + f" '{tok}'" + (f" and profile '{profile}'" if profile else ''))
        subject = (entry.get('demonstrates') or {}).get('effect') or entry.get('catalogueEffect')
        if subject and not claimed and str(entry.get('id', '')).startswith('study-'):
            claimed = True
            row = self.identity(subject)
            (evidence if row else failures).append(f"catalogue effect {subject}" + (f" <- {row['oldId']} ({row['source']})" if row else ' has no verified port-ledger source'))
        return claimed, claimed and not failures and bool(evidence), evidence + ['FAIL: ' + f for f in failures]


def framed(entry):
    """The invented application frame: window 90 titled "Application / ..." (gallery_cases catalogue backdrop and
    application() of examples/screen_backdrop.py). An original scene whose mode is "application" is not framed by this."""
    return any(c.get('op') == 'window' and c.get('id') == 90 and str(c.get('title', '')).startswith('Application /')
               for c in entry.get('commands', []))


def library():
    sys.path.insert(0, str(NATIVE / 'examples'))
    import gallery_cases
    src = (NATIVE / 'examples/gallery_cases.py').read_text()
    generator = {}
    # A fixture generator is imported through gallery_cases.fixture_study, which yields nothing in the public tree that
    # leaves it out; every other generator must import.
    for plain, function, _, fixture in dict.fromkeys(re.findall(
            r"^ (?:from (\w+) import (build_\w+)|(build_\w+)=fixture_study\('(\w+)'\))", src, re.M)):
        module = plain or fixture
        builder = getattr(importlib.import_module(module), function) if plain else gallery_cases.fixture_study(fixture)
        for case in builder():
            generator.setdefault(case['id'], module)
    cases = gallery_cases.build_cases()
    for case in cases:
        if case['id'] not in generator:
            generator[case['id']] = 'gallery_cases.catalogue' if case['id'].startswith('study-') else 'gallery_cases.inline'
    recipes = json.loads((NATIVE / 'recipes.json').read_text())
    for r in recipes:
        generator[r['id']] = 'native/recipes.json'
    return recipes + cases, generator


def recipe_effects(entry):
    return sorted(set(re.findall(r'"effect": "([^"]+)"', json.dumps(entry.get('commands', [])))))


# Original artwork withheld from the public Gallery, with the reason. The TDF specimens are pre-rendered cells of a
# wordmark; the TheDraw fonts that would re-render them with other text are third-party files Nocturne does not
# distribute.
WITHHELD = {'tdf_gallery_studies': 'pre-rendered wordmark cells; the TheDraw fonts needed to re-render them are not distributed'}


def classify(entry, generator, resolver):
    if generator in WITHHELD:
        return 'withheld', [WITHHELD[generator]]
    if generator == 'native/recipes.json':
        effects = recipe_effects(entry)
        verified = [e for e in effects if resolver.identity(e)]
        unverified = [e for e in effects if not resolver.identity(e)]
        if verified and not unverified:
            return 'rc4-authored', [f"RC4 composition around ported original effects {verified}"]
        if unverified:
            return 'unresolved-claim', [f"named as an original effect but {unverified} has no port-ledger source in the originals"]
        return 'rc4-authored', ['RC4 showcase composition with no original source']
    claimed, ok, evidence = resolver.claim(entry, generator)
    if not claimed:
        return 'synthetic', ['no provenance claim']
    if not ok:
        return 'unresolved-claim', evidence
    if framed(entry):
        return 'original-framed', evidence
    if placeholder(entry):
        return 'original-placeholder', evidence
    if substitute(entry):
        return 'original-substitute', evidence
    return 'original', evidence


SUBSTITUTE_SUFFIXES = (('-generic', ' / generic'), ('-legacy', ' / legacy'))


def substitute(entry):
    """The prior rendering kept beside an original route: the generic native painter (original_weather_routes,
    original_world_weather_routes) or the field without source optics (original_gallery_routes). Its twin without
    the suffix uses the original source painter."""
    return any(str(entry.get('id', '')).endswith(i) and str(entry.get('name', '')).endswith(n) for i, n in SUBSTITUTE_SUFFIXES)


def twin(entry):
    ident = entry['id']
    for suffix, _ in SUBSTITUTE_SUFFIXES:
        if ident.endswith(suffix):
            return ident[:-len(suffix)]
    return None


def resolve_classes(entries, generator, resolver):
    """[(entry, class, evidence)] with the library-wide rules applied: a placeholder specimen or a substitute
    rendering is redundant when the same original is admitted in an original scene or with its source painter."""
    rows = [(e, *classify(e, generator[e['id']], resolver)) for e in entries]
    in_scene = {subject_effect(e) for e, cls, _ in rows if cls == 'original' and subject_effect(e)}
    originals = {e['id'] for e, cls, _ in rows if cls == 'original'}
    out = []
    for e, cls, evidence in rows:
        if cls == 'original-placeholder' and subject_effect(e) not in in_scene:
            cls, evidence = 'original', evidence + ['only presentation of this original effect: specimen kept']
        elif cls == 'original-substitute' and twin(e) not in originals:
            cls, evidence = 'original', evidence + ['source-painter twin not admitted: prior rendering kept']
        out.append((e, cls, evidence))
    return out


def placeholder(entry):
    """The catalogue specimen window: a grey "Effect study" panel of invented text around an original window effect."""
    return any(c.get('op') == 'window' and c.get('title') == 'Effect study' for c in entry.get('commands', []))


def subject_effect(entry):
    d = entry.get('demonstrates') or {}
    return d.get('effect') or entry.get('catalogueEffect')


PROPOSAL = {'synthetic': 'remove from the Gallery', 'unresolved-claim': 'remove from the Gallery',
            'original-framed': 'remove from the Gallery (isolated twin kept)', 'rc4-authored': 'operator review',
            'original-placeholder': 'remove when the same original effect is shown in an original scene',
            'original-substitute': 'remove: the prior generic rendering of an original whose source-painter twin ships',
            'withheld': 'withheld from the public Gallery (reason recorded)',
            'original': 'keep'}


LEDGER = NATIVE / 'contract/GALLERY-ADMISSION.json'
LEDGER_SCHEMA = 'nocturne.gallery-admission.v1'


def read_ledger(path=LEDGER):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema') != LEDGER_SCHEMA:
        raise ValueError(f'{path}: schema must be {LEDGER_SCHEMA}')
    return data


def operator_decisions(path=LEDGER):
    """{entry id: decision} for RC4-era entries the operator ruled on. Missing ledger: none."""
    try:
        return {d['id']: d for d in read_ledger(path).get('operatorDecisions', [])}
    except FileNotFoundError:
        return {}


def compute_ledger(decisions_path=LEDGER):
    """The admission ledger recomputed from repository bytes. Deterministic: no clocks, no host paths."""
    entries, generator = library()
    resolver = Resolver()
    decisions = operator_decisions(decisions_path)
    admitted, excluded, examples = [], collections.Counter(), []
    by_class = collections.Counter()
    for e, cls, evidence in resolve_classes(entries, generator, resolver):
        by_class[cls] += 1
        decision = decisions.get(e['id'])
        if cls == 'original' or (cls == 'rc4-authored' and decision and decision['decision'] == 'admit'):
            admitted.append({'id': e['id'], 'class': cls, 'generator': generator[e['id']], 'evidence': evidence})
        else:
            excluded[cls] += 1
            if generator[e['id']] == 'native/recipes.json' and cls == 'rc4-authored':
                examples.append(e['id'])
    return {'schema': LEDGER_SCHEMA,
            'policy': 'The Gallery admits an entry only when its provenance resolves to the original series of explorations '
                      '(class original), or when it is RC4-era work the operator admitted by name. Synthetic contract fixtures, '
                      'unresolved claims and originals wrapped in the invented application frame are not admitted. They stay '
                      'executable as tests (gallery_cases.py --execute); they are not artwork.',
            'corpusSha256': {name: hashlib.sha256(b).hexdigest() for name, b in sorted(resolver.corpus.items())},
            'libraryEntries': len(entries), 'byClass': dict(sorted(by_class.items())),
            'admittedCount': len(admitted), 'excludedByClass': dict(sorted(excluded.items())),
            'operatorDecisions': sorted(decisions.values(), key=lambda d: d['id']),
            'workshopExamples': {'policy': 'RC4-era SDK feature recipes that the Workshop panels open (condition console, '
                                           'selector studio, plots, notifications, anatomy, materials, graphs, flight). They are '
                                           'labelled SDK examples, never in the Gallery picker or attract rotation, and are not '
                                           'artwork. Nullified recipes are dropped at build.',
                                 'ids': examples},
            'admitted': admitted}


def workshop_examples(recipes, path=LEDGER):
    """The ledger's Workshop example recipes, in recipes.json order."""
    ids = set(read_ledger(path).get('workshopExamples', {}).get('ids', []))
    return [r for r in recipes if r['id'] in ids]


def admitted_ids(path=LEDGER):
    return [row['id'] for row in read_ledger(path)['admitted']]


def admit(recipes, path=LEDGER, strict=True):
    """The Gallery library restricted to the ledger's admitted ids, in library order. Every admitted id must be
    present: a missing one means the ledger is stale, and the build stops rather than silently shrinking."""
    ids = admitted_ids(path)
    available = {r['id'] for r in recipes}
    missing = [i for i in ids if i not in available]
    if missing and strict:
        raise SystemExit('Gallery admission ledger names entries the library no longer has: ' + ', '.join(missing[:8])
                         + ('' if len(missing) <= 8 else f' (+{len(missing) - 8} more)')
                         + '; run native/scripts/gallery_provenance.py --write-ledger')
    allowed = set(ids)
    return [present(r) for r in recipes if r['id'] in allowed]


INVENTED_MESH_COLORS = {0x42b8bc, 0xc586e1}


def invented_scenery(command):
    """The placeholder backdrop of world() in examples/screen_backdrop.py: two flat triangles (teal 0x42b8bc, violet 0xc586e1) that no
    original exploration drew. Source-route studies place their original painters in front of it."""
    return command.get('op') == 'mesh' and bool(command.get('triangles')) and all(
        t.get('color') in INVENTED_MESH_COLORS for t in command['triangles'])


def present(entry):
    """An admitted entry as the Gallery shows it: without invented scenery. The test harness keeps the fixture
    unchanged; the original painter, its camera, clock and sky are untouched."""
    if not any(invented_scenery(c) for c in entry.get('commands', [])):
        return entry
    shown = dict(entry)
    shown['commands'] = [c for c in entry['commands'] if not invented_scenery(c)]
    return shown


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--census', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--write-ledger', action='store_true')
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    if a.write_ledger or a.check:
        ledger = compute_ledger()
        text = json.dumps(ledger, indent=1, ensure_ascii=False) + '\n'
        if a.write_ledger:
            LEDGER.write_text(text, encoding='utf-8')
            print(f"admitted {ledger['admittedCount']} of {ledger['libraryEntries']}; excluded {ledger['excludedByClass']}")
            return
        if not LEDGER.is_file() or LEDGER.read_text(encoding='utf-8') != text:
            raise SystemExit('native/contract/GALLERY-ADMISSION.json differs from the recomputation; run --write-ledger and review the diff')
        print('Gallery admission ledger is current')
        return
    if not (a.census and a.output):
        p.error('--census and --output are required for a review report')
    census = {r['id']: r for r in json.loads(a.census.read_text())['records']}
    entries, generator = library()
    resolver = Resolver()
    hashes = collections.Counter((census.get(e['id'], {}).get('measures') or {}).get('hash') for e in entries)
    rows = []
    for e, cls, evidence in resolve_classes(entries, generator, resolver):
        c = census.get(e['id'], {})
        m = c.get('measures') or {}
        rows.append({'id': e['id'], 'name': e.get('name'), 'generator': generator[e['id']], 'class': cls,
                     'proposal': PROPOSAL[cls], 'evidence': evidence,
                     'feature': (e.get('demonstrates') or {}).get('feature') or (e.get('demonstrates') or {}).get('effect'),
                     'attract': c.get('attract'), 'thumb': c.get('thumb'), 'rendered': bool(m),
                     'renderError': c.get('error'), 'measures': m,
                     'duplicateFrames': hashes[m.get('hash')] if m.get('hash') else None})
    missing = [r['id'] for r in rows if r['id'] not in census]
    by_class = collections.Counter(r['class'] for r in rows)
    by_gen = collections.defaultdict(collections.Counter)
    for r in rows:
        by_gen[r['generator']][r['class']] += 1
    summary = {'entries': len(rows), 'byClass': dict(by_class),
               'attractByClass': dict(collections.Counter(r['class'] for r in rows if r['attract'])),
               'proposedRemoval': sum(r['class'] in ('synthetic', 'unresolved-claim', 'original-framed', 'original-placeholder', 'original-substitute', 'withheld') for r in rows),
               'operatorReview': by_class['rc4-authored'], 'kept': by_class['original'],
               'notInCensus': missing, 'renderErrors': sum(bool(r['renderError']) for r in rows),
               'catalogueIdentitiesWithoutSource': sorted(i['id'] for i in json.loads((NATIVE / 'catalogue.json').read_text()) if not resolver.identity(i['id'])),
               'originalCorpus': {name: hashlib.sha256(b).hexdigest() for name, b in resolver.corpus.items()}}
    a.output.mkdir(parents=True, exist_ok=True)
    doc = {'schema': 'nocturne.provenance-census.v1', 'summary': summary,
           'byGenerator': {g: dict(c) for g, c in sorted(by_gen.items(), key=lambda kv: -sum(kv[1].values()))}, 'entries': rows}
    (a.output / 'PROVENANCE-CENSUS.json').write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n')
    lines = ['# Gallery provenance census', '', f"Entries: {len(rows)}. Proposed for removal from the Gallery: {summary['proposedRemoval']}. "
             f"Operator review: {summary['operatorReview']}. Kept as original: {summary['kept']}.", '',
             '| Class | Entries | In attract rotation | Proposal |', '|---|---|---|---|']
    for cls in ('original', 'original-placeholder', 'original-substitute', 'original-framed', 'rc4-authored', 'unresolved-claim', 'withheld', 'synthetic'):
        lines.append(f"| {cls} | {by_class[cls]} | {summary['attractByClass'].get(cls, 0)} | {PROPOSAL[cls]} |")
    lines += ['', f"Catalogue identities with no original source: {', '.join(summary['catalogueIdentitiesWithoutSource']) or 'none'}.", '',
              '## By generator', '', '| Generator | Entries | original | original-placeholder | original-substitute | original-framed | rc4-authored | unresolved-claim | withheld | synthetic |', '|---|---|---|---|---|---|---|---|---|---|']
    for g, c in sorted(by_gen.items(), key=lambda kv: -sum(kv[1].values())):
        lines.append(f"| {g} | {sum(c.values())} | " + ' | '.join(str(c[k]) for k in ('original', 'original-placeholder', 'original-substitute', 'original-framed', 'rc4-authored', 'unresolved-claim', 'withheld', 'synthetic')) + ' |')
    lines += ['', '## Unresolved claims', '']
    for r in rows:
        if r['class'] == 'unresolved-claim':
            lines.append(f"- `{r['id']}` ({r['generator']}): " + '; '.join(r['evidence']))
    (a.output / 'PROVENANCE-CENSUS.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'originalCorpus'}, indent=1))


if __name__ == '__main__':
    main()
