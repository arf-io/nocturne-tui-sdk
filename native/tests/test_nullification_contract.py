"""The nullification contract (native/contract/NULLIFICATION.json), as far as the public tree can check it.

Decisions strike current catalogue identities and rendering outputs from the final contract; the Gallery builders omit
what they strike, so removed art cannot come back. These tests need only what the public tree ships: the schema and
validator, the catalogue, the port ledger, the recipes and captures, the reference pages, the Gallery builders and the
admission ledger. They check the schema and its exact rejection messages, resolve the scopes the generators apply
against the real catalogue, recipes and captures, and observe the effects at the boundaries that consume them: the
reference pages, the Gallery library and attract rotation, the HTTP bundle and the qualification fingerprint.

What needs the artwork inventory (native/evidence), the mechanism document, --apply or a Gallery gate pinned to the
complete library is checked in the source repository only. Where a count depends on how much of the library a tree
carries, it is a floor that the public Gallery also meets.
"""
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
REPOSITORY = NATIVE.parent
SCRIPTS = NATIVE / 'scripts'
INVENTORY = REPOSITORY / 'native/evidence/artwork-inventory-20261031/INVENTORY.json'
CONTRACT = 'native/contract/NULLIFICATION.json'
ADMISSION = 'native/contract/GALLERY-ADMISSION.json'
SCHEMA_ID = 'nocturne.nullification.v1'
EMPTY = {'schema': SCHEMA_ID, 'decisions': []}
WASM = NATIVE / 'dist/nocturne_native.wasm'
# The public tree's Gallery library is smaller than the source repository's: floors that count recipes use the smaller
# number there.
PUBLIC_TREE = (REPOSITORY / 'PUBLIC-TREE-REPORT.json').is_file()


def script(name):
    """Import native/scripts/<name>.py; a missing module fails only the tests that need it."""
    path = SCRIPTS / (name + '.py')
    if not path.is_file():
        raise AssertionError('Missing ' + path.relative_to(REPOSITORY).as_posix())
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module(name)


def decision(scope, key, name='Reviewed artwork', reason='Should be forgotten', decidedBy='operator',
             decidedAt='2026-11-01T17:45:00Z'):
    return {'scope': scope, 'key': key, 'name': name, 'reason': reason, 'decidedBy': decidedBy,
            'decidedAt': decidedAt}


def document(*decisions):
    return {'schema': SCHEMA_ID, 'decisions': list(decisions)}


def canonical(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def gallery_repository(directory, contract):
    """A scratch repository in which the Gallery builders run with contract committed at its default path.

    The builders find the contract and the admission ledger under their own repository root, so the scripts and every file
    they resolve against are copies; the read-only build inputs (examples, web template, built WASM, bindings and test
    fixtures) are linked."""
    root = Path(directory) / 'gallery-repository'
    shutil.copytree(SCRIPTS, root / 'native/scripts', ignore=shutil.ignore_patterns('__pycache__'))
    (root / 'native/contract').mkdir(parents=True)
    for name in ('NULLIFICATION.schema.json', 'GALLERY-ADMISSION.json'):
        shutil.copy2(NATIVE / 'contract' / name, root / 'native/contract' / name)
    (root / CONTRACT).write_text(canonical(contract))
    for name in ('catalogue.json', 'port-ledger.json', 'recipes.json', 'palettes.json'):
        shutil.copy2(NATIVE / name, root / 'native' / name)
    for name in ('examples', 'web', 'dist', 'bindings', 'tests'):
        os.symlink(NATIVE / name, root / 'native' / name)
    shutil.copy2(REPOSITORY / 'RELEASE.json', root / 'RELEASE.json')
    shutil.copytree(REPOSITORY / 'docs/current', root / 'docs/current')
    return root


def gallery_library():
    """(the Gallery library before admission and the contract: native/recipes.json, then the generated studies; the ids the
    admission ledger admits)."""
    if str(NATIVE / 'examples') not in sys.path:
        sys.path.insert(0, str(NATIVE / 'examples'))
    from gallery_cases import build_cases
    admitted = set(script('gallery_provenance').admitted_ids(REPOSITORY / ADMISSION))
    return json.loads((NATIVE / 'recipes.json').read_text()) + build_cases(), admitted


def run(arguments, cwd, stdin=None, timeout=900):
    return subprocess.run([sys.executable, *map(str, arguments)], cwd=cwd, input=stdin, capture_output=True,
                          text=True, timeout=timeout)


class ContractFiles(unittest.TestCase):
    def test_schema_file_declares_the_validator_vocabulary(self):
        n = script('nullification')
        schema = json.loads((NATIVE / 'contract/NULLIFICATION.schema.json').read_text())
        self.assertEqual(schema['$schema'], 'https://json-schema.org/draft/2020-12/schema')
        self.assertEqual(schema['required'], ['schema', 'decisions'])
        self.assertIs(schema['additionalProperties'], False)
        self.assertEqual(schema['properties']['schema']['const'], n.SCHEMA)
        self.assertEqual(n.SCHEMA, SCHEMA_ID)
        item = schema['properties']['decisions']['items']
        self.assertEqual(item, {'$ref': '#/$defs/decision'})
        definition = schema['$defs']['decision']
        self.assertEqual(definition['required'], list(n.FIELDS))
        self.assertEqual(sorted(definition['properties']), sorted(n.FIELDS))
        self.assertIs(definition['additionalProperties'], False)
        self.assertEqual(definition['properties']['scope']['enum'], list(n.SCOPES))
        self.assertEqual(definition['properties']['decidedAt']['pattern'], n.DECIDED_AT_PATTERN)
        rules = {rule['if']['properties']['scope']['const']: rule['then']['properties']['key']['pattern']
                 for rule in definition['allOf']}
        self.assertEqual(rules, n.KEY_PATTERNS)
        self.assertEqual(sorted(rules), sorted(n.SCOPES))
        for field in ('name', 'reason', 'decidedBy'):
            self.assertEqual(definition['properties'][field], {'$ref': '#/$defs/text'}, field)
        self.assertEqual(schema['$defs']['text'], {'type': 'string', 'pattern': '\\S'})

    def test_committed_contract_is_canonical_and_resolves_against_the_repository(self):
        # The contract is in canonical form in every state, so --apply never rewrites it, and every decision resolves: all
        # of them where the tree carries the artwork inventory, the scopes the generators apply where it does not.
        n = script('nullification')
        self.assertEqual(n.canonical_document(EMPTY), canonical(EMPTY))
        text = (REPOSITORY / CONTRACT).read_text()
        committed = json.loads(text)
        self.assertEqual(text, n.canonical_document(committed), 'canonical form, so --apply never rewrites it')
        self.assertEqual(text, canonical(committed))
        scopes = n.SCOPES if INVENTORY.is_file() else n.CONTRACT_SCOPES
        resolved = n.load_contract(REPOSITORY, scopes=scopes)
        self.assertEqual([(row['scope'], row['key']) for row in resolved],
                         [(d['scope'], d['key']) for d in committed['decisions'] if d['scope'] in scopes])


class Validation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = script('nullification')

    def rejected(self, value):
        with self.assertRaises(self.n.NullificationError) as caught:
            self.n.validate(value)
        self.assertIsInstance(caught.exception, ValueError)
        self.assertEqual(str(caught.exception), '\n'.join(caught.exception.messages))
        return caught.exception.messages

    def test_unknown_scope_rejects(self):
        self.assertEqual(self.rejected(document(decision('historic', 'weather/pearl-bloom'))), [
            'decision 0: unknown scope "historic" (expected historical-definition, historical-instance, '
            'current-identity or rendering-output)'])

    def test_missing_or_blank_reason_rejects(self):
        missing = decision('current-identity', 'weather/pearl-bloom')
        del missing['reason']
        self.assertEqual(self.rejected(document(missing)), ['decision 0: missing reason'])
        for blank in ('', '   ', 7, None):
            with self.subTest(reason=blank):
                self.assertEqual(self.rejected(document(decision('current-identity', 'weather/pearl-bloom', reason=blank))),
                                 ['decision 0: reason must be a non-empty string'])

    def test_duplicate_scope_and_key_rejects(self):
        self.assertEqual(self.rejected(document(decision('current-identity', 'weather/pearl-bloom'),
                                                decision('current-identity', 'weather/pearl-bloom', reason='Again'))),
                         ['decision 1: duplicates decision 0 (current-identity "weather/pearl-bloom")'])
        # A recipe and a capture may share a word; their namespaced keys are different decisions.
        self.n.validate(document(decision('rendering-output', 'recipe:text'), decision('rendering-output', 'capture:text/default')))

    def test_document_shape_fields_and_timestamps_reject_exactly(self):
        self.assertEqual(self.rejected([]), ['nullification contract must be a JSON object'])
        self.assertEqual(self.rejected({'schema': 'nocturne.nullification.v0', 'decisions': []}),
                         ['schema must be "nocturne.nullification.v1"'])
        self.assertEqual(self.rejected({**EMPTY, 'notes': 'x'}), ['unknown top-level field "notes"'])
        self.assertEqual(self.rejected({'schema': SCHEMA_ID}), ['missing decisions'])
        self.assertEqual(self.rejected({'schema': SCHEMA_ID, 'decisions': {}}), ['decisions must be an array'])
        self.assertEqual(self.rejected(document('weather/pearl-bloom')), ['decision 0: must be an object'])
        self.assertEqual(self.rejected(document({**decision('current-identity', 'weather/pearl-bloom'), 'notes': 'x'})),
                         ['decision 0: unknown field "notes"'])
        for stamp in ('2026-11-01', '2026-11-01T17:45:00', '2026-13-01T17:45:00Z', '2026-11-01 17:45:00Z',
                      '2026-11-01T17:45Z', 20261101):
            with self.subTest(decidedAt=stamp):
                self.assertEqual(self.rejected(document(decision('current-identity', 'weather/pearl-bloom', decidedAt=stamp))), [
                    'decision 0: decidedAt must be an ISO-8601 date-time with seconds and a UTC offset, '
                    'such as 2026-11-01T17:45:00Z'])
        for stamp in ('2026-11-01T17:45:00Z', '2026-11-01T17:45:00.123Z', '2026-11-01T09:45:00-08:00'):
            with self.subTest(decidedAt=stamp):
                self.n.validate(document(decision('current-identity', 'weather/pearl-bloom', decidedAt=stamp)))

    def test_malformed_keys_reject_with_the_schema_pattern(self):
        cases = [('historical-definition', 'A1FE67F6FD8D8E24'), ('historical-instance', 'Nocturne-Black-Hole.html'),
                 ('current-identity', 'pearl-bloom'), ('rendering-output', 'autumn'), ('rendering-output', 'capture:text')]
        for scope, key in cases:
            with self.subTest(scope=scope, key=key):
                self.assertEqual(self.rejected(document(decision(scope, key))),
                                 ['decision 0: ' + scope + ' key ' + json.dumps(key) + ' must match ' + self.n.KEY_PATTERNS[scope]])

    def test_every_problem_is_reported_in_decision_order(self):
        nameless = decision('current-identity', 'weather/pearl-bloom')
        del nameless['name']
        del nameless['reason']
        self.assertEqual(self.rejected(document(decision('historic', 'x'), nameless, decision('current-identity', 'weather/pearl-bloom'))), [
            'decision 0: unknown scope "historic" (expected historical-definition, historical-instance, current-identity or rendering-output)',
            'decision 1: missing name', 'decision 1: missing reason',
            'decision 2: duplicates decision 1 (current-identity "weather/pearl-bloom")'])

    def test_a_lone_surrogate_rejects_because_it_cannot_be_written(self):
        # JSON may escape half of a surrogate pair ("\ud800"); such a string has no UTF-8 form, so the contract and the
        # records could not be written.
        self.assertEqual(self.rejected(document(decision('current-identity', 'weather/pearl-bloom', reason='one\ud800two'))),
                         ['decision 0: reason contains a lone surrogate (U+D800) and cannot be written as UTF-8'])
        self.assertEqual(self.rejected(document(decision('historical-instance', 'a.html#line 1#x\udfff', name='\udc00'))),
                         ['decision 0: key contains a lone surrogate (U+DFFF) and cannot be written as UTF-8',
                          'decision 0: name contains a lone surrogate (U+DC00) and cannot be written as UTF-8'])
        self.n.validate(document(decision('current-identity', 'weather/pearl-bloom', reason='a pair \U0001F319 is one character')))

    def test_a_missing_or_unreadable_contract_is_an_error_not_an_empty_list(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'NULLIFICATION.json'
            with self.assertRaises(self.n.NullificationError) as caught:
                self.n.read_document(path)
            self.assertEqual(caught.exception.messages, [str(path) + ': missing nullification contract'])
            path.write_text('{"schema":')
            with self.assertRaises(self.n.NullificationError) as caught:
                self.n.read_document(path)
            self.assertTrue(caught.exception.messages[0].startswith(str(path) + ': not valid JSON:'))


class CurrentScopeResolution(unittest.TestCase):
    """Decisions in the scopes the documentation and Gallery generators apply (current-identity, rendering-output)."""

    @classmethod
    def setUpClass(cls):
        cls.n = script('nullification')
        cls.sources = cls.n.Sources(REPOSITORY)

    def resolve(self, *decisions):
        return self.n.resolve(document(*decisions), self.sources)

    def unresolved(self, *decisions):
        with self.assertRaises(self.n.NullificationError) as caught:
            self.resolve(*decisions)
        return caught.exception.messages

    def test_unresolvable_keys_reject_per_scope(self):
        self.assertEqual(self.unresolved(decision('current-identity', 'weather/no-such-identity')), [
            'decision 0: current-identity key "weather/no-such-identity" does not resolve against native/catalogue.json'])
        self.assertEqual(self.unresolved(decision('rendering-output', 'recipe:no-such-recipe')), [
            'decision 0: rendering-output key "recipe:no-such-recipe" does not resolve against native/recipes.json'])
        self.assertEqual(self.unresolved(decision('rendering-output', 'capture:widget-text/no-such-state')), [
            'decision 0: rendering-output key "capture:widget-text/no-such-state" does not resolve against '
            'docs/current/images/CAPTURES.json'])
        self.assertEqual(self.unresolved(decision('current-identity', 'weather/a'), decision('current-identity', 'weather/b')), [
            'decision 0: current-identity key "weather/a" does not resolve against native/catalogue.json',
            'decision 1: current-identity key "weather/b" does not resolve against native/catalogue.json'])

    def test_a_current_identity_strikes_its_catalogue_ledger_recipes_and_pages(self):
        [row] = self.resolve(decision('current-identity', 'weather/autumn-drift', name='Autumn Drift'))
        self.assertEqual(row['resolved']['name'], 'Autumn Drift')
        strikes = row['strikes']
        self.assertEqual(strikes['catalogue'], {'id': 'weather/autumn-drift', 'name': 'Autumn Drift', 'contract': 'ParticleEmitter', 'family': 0})
        self.assertEqual(strikes['portLedger'], {'newId': 'weather/autumn-drift', 'oldId': 'weather/thermal.leaves',
                                                 'state': 'native-source-thermal-implemented-review-pending'})
        self.assertEqual(strikes['recipes'], ['autumn', 'leaf-anatomy', 'surface-lab'])
        self.assertEqual(strikes['captures'], [])
        self.assertEqual(strikes['docsPages'], [{'page': 'Catalogue-Weather.md', 'omits': 'section weather/autumn-drift'},
                                                {'page': 'Catalogue.md', 'omits': 'index row'}])
        retained = row['retained']
        self.assertEqual(retained['engineDefaultFor'], ['emitter'])
        mentions = {(m['page'], m['text']) for m in retained['docsMentions']}
        self.assertIn(('Commands.md', 'Native default: `weather/autumn-drift`.'), mentions)
        self.assertEqual({m['page'] for m in retained['docsMentions']}, {'Catalogue-Weather.md', 'Commands.md'})
        self.assertEqual(retained['capturesLoadingStruckRecipes'], ['emitter/advanced', 'emitter/default', 'floor/advanced',
                                                                     'floor/default', 'surface/advanced', 'surface/default'])
        self.assertTrue(any(w.startswith('weather/autumn-drift is the engine default effect for emitter commands that omit effect')
                            for w in row['warnings']), row['warnings'])
        self.assertTrue(any('Missing reference recipe autumn' in w for w in row['warnings']), row['warnings'])

    def test_a_separate_addition_has_no_port_ledger_entry(self):
        [row] = self.resolve(decision('current-identity', 'weather/snowglobe'))
        self.assertIsNone(row['strikes']['portLedger'])
        self.assertEqual(row['strikes']['recipes'], ['snow'])
        self.assertEqual(row['retained']['engineDefaultFor'], [])

    def test_every_catalogue_identity_resolves_and_no_component_capture_names_one(self):
        identities = [x['id'] for x in json.loads((NATIVE / 'catalogue.json').read_text())]
        resolved = self.resolve(*[decision('current-identity', x) for x in identities])
        self.assertEqual(len(resolved), 111)
        self.assertEqual([row['strikes']['captures'] for row in resolved], [[]] * 111)
        defaults = {row['key']: row['retained']['engineDefaultFor'] for row in resolved if row['retained']['engineDefaultFor']}
        self.assertEqual(defaults, {'weather/autumn-drift': ['emitter'], 'surface-field/silk-tide': ['field'],
                                    'text/ink-dissolve': ['text'], 'window-transition/glass-dissolve': ['window']})

    def test_rendering_outputs_are_namespaced_recipes_and_captures(self):
        recipe, capture = self.resolve(decision('rendering-output', 'recipe:text'), decision('rendering-output', 'capture:text/default'))
        self.assertEqual(recipe['resolved'], {'kind': 'recipe', 'id': 'text', 'name': 'Ink Choreography'})
        self.assertEqual(recipe['strikes'], {'recipes': ['text']})
        self.assertEqual(recipe['retained']['capturesLoadingStruckRecipes'], ['text/advanced', 'text/default'])
        self.assertEqual((capture['resolved']['kind'], capture['resolved']['component'], capture['resolved']['state'],
                          capture['resolved']['image']), ('capture', 'text', 'default', 'text-default.png'))
        self.assertEqual(capture['strikes'], {'captures': ['text/default']})

    def test_a_struck_capture_keeps_its_shared_image_and_the_hand_maintained_atlas(self):
        [row] = self.resolve(decision('rendering-output', 'capture:path/default'))
        self.assertEqual(row['resolved']['image'], 'float-default.png')
        self.assertEqual(row['retained'], {'image': 'float-default.png', 'imageSharedWith': ['float/default'], 'pages': ['Components.md']})
        self.assertTrue(any('Components.md' in w and 'recaptured' in w for w in row['warnings']), row['warnings'])

    def test_generators_resolve_only_the_scopes_they_apply(self):
        # The Gallery build and a packaged SDK have no inventory: historical keys are checked for shape there,
        # and resolved against INVENTORY.json by apply_nullification.py and this suite.
        resolved = self.n.resolve(document(decision('historical-definition', '0000000000000000'),
                                           decision('current-identity', 'weather/snowglobe')),
                                  self.n.Sources(REPOSITORY, inventory=False), self.n.CONTRACT_SCOPES)
        self.assertEqual([row['key'] for row in resolved], ['weather/snowglobe'])


class GalleryEffects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = script('nullification')
        cls.sources = cls.n.Sources(REPOSITORY)
        sys.path.insert(0, str(NATIVE / 'examples'))
        from gallery_cases import build_cases
        cls.recipes = json.loads((NATIVE / 'recipes.json').read_text()) + build_cases()

    def test_an_empty_contract_leaves_the_gallery_library_untouched(self):
        self.assertIs(self.n.gallery_recipes(self.recipes, []), self.recipes)

    def test_a_nullified_identity_strikes_every_recipe_that_names_it(self):
        identity = 'window-transition/ribbon-genie'
        resolved = self.n.resolve(document(decision('current-identity', identity)), self.sources)
        kept = self.n.gallery_recipes(self.recipes, resolved)
        quoted = json.dumps(identity)
        expected = sorted(r['id'] for r in self.recipes if quoted in json.dumps(r, ensure_ascii=False))
        self.assertGreater(len(expected), 100 if PUBLIC_TREE else 2900, 'every application study draws its backdrop window with this identity')
        self.assertEqual(sorted({r['id'] for r in self.recipes} - {r['id'] for r in kept}), expected)
        self.assertFalse([r['id'] for r in kept if quoted in json.dumps(r, ensure_ascii=False)])
        strikes = self.n.gallery_strikes(self.recipes, resolved)
        self.assertEqual(sorted(strikes), expected)
        reasons = Counter(reason for found in strikes.values() for reason in found)
        self.assertLessEqual(set(reasons), {'commands', 'comparison', 'subject'})
        self.assertGreaterEqual(set(reasons), {'commands', 'subject'})
        self.assertEqual(strikes['windows'], ['commands'])
        self.assertEqual(strikes['study-window-transition-ribbon-genie-isolated'], ['commands', 'subject'])

    def test_a_nullified_recipe_strikes_only_that_recipe(self):
        resolved = self.n.resolve(document(decision('rendering-output', 'recipe:rain')), self.sources)
        kept = {r['id'] for r in self.n.gallery_recipes(self.recipes, resolved)}
        self.assertEqual([r['id'] for r in self.recipes if r['id'] not in kept], ['rain'])
        self.assertEqual(self.n.gallery_strikes(self.recipes, resolved), {'rain': ['decision']})

    def test_a_nullified_capture_does_not_change_the_gallery(self):
        resolved = self.n.resolve(document(decision('rendering-output', 'capture:path/default')), self.sources)
        self.assertEqual(len(self.n.gallery_recipes(self.recipes, resolved)), len(self.recipes))


class ReferenceDocsEffects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = script('nullification')
        cls.docs = script('build_reference_docs')
        cls.sources = cls.n.Sources(REPOSITORY)
        cls.current = REPOSITORY / 'docs/current'
        cls.section = json.loads((cls.current / 'components.json').read_text())['catalogue']

    def test_the_committed_pages_are_what_the_committed_contract_determines(self):
        resolved = self.n.load_contract(REPOSITORY)
        expected = self.docs.nullified_docs(self.current, resolved)
        self.assertEqual(expected['Nullification.md'] is None, not resolved)
        for name, text in expected.items():
            path = self.current / name
            self.assertEqual(text, path.read_text() if path.is_file() else None, name)
        identities = [row['key'] for row in resolved if row['scope'] == 'current-identity']
        for name, text in self.docs.catalogue_pages(self.section, identities).items():
            self.assertEqual(text, (self.current / name).read_text(), name)
        self.docs.check_nullified_docs(self.current, resolved)

    def test_no_decision_renders_every_identity_and_no_ledger(self):
        pages = self.docs.catalogue_pages(self.section, [])
        index = pages['Catalogue.md']
        self.assertIn('This catalogue lists all 111 native catalogue identities in four families.', index)
        self.assertNotIn('Nullification.md', '\n'.join(pages.values()))
        families = {0: 'Catalogue-Weather.md', 1: 'Catalogue-Surface-Fields.md', 2: 'Catalogue-Text.md', 3: 'Catalogue-Windows.md'}
        for entry in self.section['entries']:
            self.assertIn('| [`' + entry['id'] + '`](', index)
            self.assertIn('\n### ' + entry['id'] + '\n', pages[families[entry['family']]])
        expected = self.docs.nullified_docs(self.current, [])
        self.assertIsNone(expected['Nullification.md'])
        self.assertNotIn('Nullification.md', json.loads(expected['manifest.json'])['pages'])
        self.assertEqual({name: text for name, text in expected.items() if name in pages}, pages)

    def test_a_nullified_identity_is_omitted_from_the_catalogue_pages_and_points_to_the_ledger(self):
        full = self.docs.catalogue_pages(self.section, [])
        pages = self.docs.catalogue_pages(self.section, ['weather/pearl-bloom'])
        self.assertNotIn('\n### weather/pearl-bloom\n', pages['Catalogue-Weather.md'])
        self.assertNotIn('weather/pearl-bloom', pages['Catalogue.md'])
        self.assertIn('This catalogue lists 110 of the 111 native catalogue identities in four families', pages['Catalogue.md'])
        self.assertIn('](Nullification.md)', pages['Catalogue.md'])
        self.assertIn('| [Weather](Catalogue-Weather.md) | `ParticleEmitter` | `emitter`, `weather-author` | 27 |', pages['Catalogue.md'])
        self.assertIn('\n27 identities with the native contract `ParticleEmitter`.', pages['Catalogue-Weather.md'])
        for name in ('Catalogue-Surface-Fields.md', 'Catalogue-Text.md', 'Catalogue-Windows.md'):
            self.assertEqual(pages[name], full[name], name)

        def section(text, identity):
            return text.split('\n### ' + identity + '\n', 1)[1].split('\n### ', 1)[0]
        for entry in self.section['entries']:
            if entry['family'] == 0 and entry['id'] != 'weather/pearl-bloom':
                self.assertEqual(section(pages['Catalogue-Weather.md'], entry['id']), section(full['Catalogue-Weather.md'], entry['id']))
        with self.assertRaisesRegex(ValueError, 'not in the catalogue: weather/no-such-identity'):
            self.docs.catalogue_pages(self.section, ['weather/no-such-identity'])

    def test_the_page_lists_each_decision_without_who_decided_or_when(self):
        # The public page lists what is hidden and why; the free text of decidedBy and the decision date stay in the
        # contract file.
        resolved = self.n.resolve(document(
            decision('current-identity', 'weather/pearl-bloom', decidedBy='Reviewer, provisional default pending an answer; reversible',
                     decidedAt='2026-11-14T19:50:00Z'),
            decision('rendering-output', 'recipe:rain', decidedBy='The maintainers', decidedAt='2026-11-02T08:00:00+02:00')), self.sources)
        page = self.docs.nullification_page(resolved)
        self.assertIn('| Identity | Name | Recipes omitted | Reason |', page)
        self.assertIn('| Output | Name | Reason |', page)
        for text in ('Reviewer', 'The maintainers', 'provisional', 'awaiting', 'Decision', 'Decided by', 'Decided at', '19:50', '2026-11-02'):
            self.assertNotIn(text, page)

    def test_free_text_from_the_review_page_renders_literally_through_html_and_pdf(self):
        # name, reason and decidedBy arrive from the review page as free text; the ledger goes through Markdown,
        # ElementTree and reportlab when the reference is built and packaged.
        hostile = 'Line one\nline <br> two & <script>alert(1)</script> | pipe `tick` *star* [link](x.md) \\ end'
        resolved = self.n.resolve(document(decision('current-identity', 'weather/pearl-bloom', name=hostile, reason=hostile, decidedBy=hostile),
                                           decision('rendering-output', 'recipe:rain', name=hostile, reason=hostile)), self.sources)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'docs'
            (root / 'images').mkdir(parents=True)
            (root / 'Catalogue.md').write_text('# Catalogue\n')
            (root / 'Components.md').write_text('# Components\n')
            (root / 'components.json').write_text('{"components": []}\n')
            (root / 'images/CAPTURES.json').write_text('{"captures": []}\n')
            (root / 'Nullification.md').write_text(self.docs.nullification_page(resolved))
            (root / 'manifest.json').write_text(json.dumps({'schema': 'nocturne.reference.v1', 'title': 'Ledger', 'pages': ['Nullification.md']}))
            self.docs.build(root, Path(directory) / 'out')
            html = (Path(directory) / 'out/Nullification.html').read_text()
            for raw in ('<script>', '<br>', '<em>', 'href="x.html"', 'href="x.md"'):
                self.assertNotIn(raw, html)
            self.assertIn('line &lt;br&gt; two &amp; &lt;script&gt;alert(1)&lt;/script&gt; | pipe `tick` *star* [link](x.md) \\ end', html)
            from pypdf import PdfReader
            text = ''.join(''.join(page.extract_text().split()) for page in PdfReader(Path(directory) / 'out/Nocturne-SDK-Reference.pdf').pages)
            self.assertIn('<script>alert(1)</script>', text, 'the PDF shows the text literally (table cells may wrap)')


class Generators(unittest.TestCase):
    def require_gallery_inputs(self):
        if not WASM.is_file():
            raise AssertionError('BLOCKED: ' + str(WASM) + ' is not built; run sh build-native.sh')
        if not shutil.which('node'):
            raise AssertionError('BLOCKED: node is not on PATH')

    def test_the_gallery_omits_struck_recipes_from_its_library_and_attract_rotation(self):
        self.require_gallery_inputs()
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            contract = directory / 'NULLIFICATION.json'
            contract.write_text(json.dumps(document(decision('current-identity', 'weather/autumn-drift'),
                                                    decision('rendering-output', 'recipe:rain'))))
            gallery = directory / 'gallery.html'
            built = run([SCRIPTS / 'build_gallery.py', '--output', gallery, '--nullification', contract], NATIVE)
            self.assertEqual(built.returncode, 0, built.stderr)
            library, admitted = gallery_library()
            # The library the contract applies to is the one the admission ledger leaves.
            admitted_library = [r for r in library if r['id'] in admitted]
            (directory / 'unfiltered.json').write_text(json.dumps(admitted_library))
            probe = directory / 'attract.mjs'
            probe.write_text(ATTRACT_PROBE)
            evaluated = subprocess.run([shutil.which('node'), str(probe), str(gallery), str(NATIVE / 'bindings/typescript/gallery_attract.mjs'),
                                        str(directory / 'unfiltered.json')], capture_output=True, text=True, timeout=600)
            self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
            shown = json.loads(evaluated.stdout)
            struck = {r['id'] for r in library if '"weather/autumn-drift"' in json.dumps(r)} | {'rain'}
            self.assertGreater(len(struck), 5 if PUBLIC_TREE else 500)
            self.assertTrue({'autumn', 'leaf-anatomy', 'surface-lab', 'rain'} <= struck)
            self.assertTrue({'autumn', 'thermal-leaves-isolated'} <= struck & admitted, 'the contract strikes admitted artwork')
            self.assertEqual(shown['library'], [r['id'] for r in admitted_library if r['id'] not in struck])
            self.assertEqual(shown['attract'], [x for x in shown['unfilteredAttract'] if x not in struck])
            self.assertIn('autumn', shown['unfilteredAttract'], 'the classic recipe rotated before it was nullified')
            self.assertLess(len(shown['attract']), len(shown['unfilteredAttract']))
            self.assertIn('; ' + str(len(shown['library'])) + ' admitted artworks, ' + str(len(library) - len(shown['library']))
                          + ' entries not admitted (provenance admission and nullification)', built.stdout)

    def test_the_gallery_site_bundle_omits_what_the_committed_contract_strikes(self):
        # build_gallery_site.py publishes the HTTP bundle. It must take its library from the same choke point as the
        # standalone page it embeds (admission, then the contract at its default path).
        self.require_gallery_inputs()
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            root = gallery_repository(directory, document(decision('current-identity', 'weather/pearl-bloom'),
                                                          decision('rendering-output', 'recipe:rain')))
            output = directory / 'site'
            built = run([root / 'native/scripts/build_gallery_site.py', '--output', output], root / 'native')
            self.assertEqual(built.returncode, 0, built.stderr + built.stdout)
            library, admitted = gallery_library()
            struck = {r['id'] for r in library if '"weather/pearl-bloom"' in json.dumps(r)} | {'rain'}
            self.assertGreater(len(struck & admitted), 1, 'the identity strikes admitted artwork')
            expected = [r['id'] for r in library if r['id'] in admitted and r['id'] not in struck]
            manifest = json.loads((output / 'MANIFEST.json').read_text())
            self.assertEqual(manifest['recipes'], len(expected))
            self.assertEqual(manifest['nullifiedRecipes'], len(library) - len(expected))
            self.assertEqual(json.loads(built.stdout.strip().splitlines()[-1])['recipes'], manifest['recipes'])
            prefix, suffix, published = 'window.nocturneRecipeAssets.push(...', ');\n', []
            for name in sorted(name for name in manifest['files'] if name.endswith('.js')):
                text = (output / name).read_text()
                self.assertTrue(text.startswith(prefix) and text.endswith(suffix), name)
                published += [r['id'] for r in json.loads(text[len(prefix):-len(suffix)])]
            self.assertEqual(published, expected, 'the recipe assets carry exactly the library the contract leaves')
            self.assertIn('window.nocturneRecipeAssets.length!==' + str(len(expected)) + ')', (output / 'gallery.html').read_text())
            server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(output)))
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()
                    try:
                        page = browser.new_page()
                        page.goto('http://127.0.0.1:' + str(server.server_port) + '/gallery.html')
                        page.wait_for_function('window.nativeLab !== undefined', timeout=120000)
                        self.assertEqual(page.evaluate('nativeLab.recipes.map(r => r.id)'), expected)
                        rotation = page.evaluate('nativeLab.demoRecipes.map(r => r.id)')
                        self.assertTrue(rotation and set(rotation) <= set(expected), 'the attract rotation draws from the published library')
                        self.assertEqual(page.evaluate("document.getElementById('error').textContent"), '')
                    finally:
                        browser.close()
            finally:
                server.shutdown()
                server.server_close()
                worker.join()

    def test_the_gallery_build_refuses_a_missing_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / 'absent' / 'NULLIFICATION.json'
            built = run([SCRIPTS / 'build_gallery.py', '--output', Path(directory) / 'unused.html', '--nullification', missing], NATIVE)
            self.assertEqual(built.returncode, 1)
            self.assertEqual(built.stderr.strip().splitlines()[-1], str(missing) + ': missing nullification contract')
            self.assertFalse((Path(directory) / 'unused.html').exists())

    def test_the_reference_check_refuses_a_missing_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / 'absent' / 'NULLIFICATION.json'
            checked = run([SCRIPTS / 'build_reference_docs.py', '--check', '--nullification', missing], REPOSITORY)
            self.assertEqual(checked.returncode, 1)
            self.assertEqual(checked.stderr.strip().splitlines()[-1], str(missing) + ': missing nullification contract')


class Binding(unittest.TestCase):
    def test_the_contract_ships_with_the_generators_that_read_it(self):
        package = script('rc2_package')
        names = ['native/contract/NULLIFICATION.json', 'native/contract/NULLIFICATION.schema.json',
                 'native/scripts/build_gallery.py', 'native/scripts/nullification.py']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in names:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(name)
            self.assertEqual(sorted(package.currentPayload(root, names)), sorted(names))

    def test_the_contract_is_bound_into_the_qualification_fingerprint(self):
        qualify = script('qualify')
        files = qualify.fingerprint()['files']
        for name in ('contract/NULLIFICATION.json', 'contract/NULLIFICATION.schema.json'):
            self.assertEqual(files[name], hashlib.sha256((NATIVE / name).read_bytes()).hexdigest(), name)


class Documentation(unittest.TestCase):
    def test_the_hand_maintained_reference_pages_allow_for_nullified_identities(self):
        # README.md and Components.md are maintained by hand and no decision rewrites them, while Catalogue.md omits every
        # nullified identity, so their sentence about the catalogue must say that hidden effects are left out.
        for name in ('README.md', 'Components.md'):
            sentence = next(line for line in (REPOSITORY / 'docs/current' / name).read_text().split('\n')
                            if '[component catalogue](Catalogue.md)' in line)
            self.assertIn('except those hidden by the nullification contract', sentence, name)


# Evaluates the built page's own attract code (the embedded policy statement and its demoRecipes definition)
# against the page's recipe data and against the unfiltered library, as gallery_attract_built.test.mjs does.
ATTRACT_PROBE = r"""
import {readFileSync} from 'node:fs';
const [html, policyPath, unfilteredPath] = process.argv.slice(2);
const page = readFileSync(html, 'utf8'), lines = page.split('\n');
const policy = readFileSync(policyPath, 'utf8').replace(/\bexport (?=(?:const|function|class)\b)/g, '');
const at = page.indexOf(policy);
if (at === -1) throw new Error('the built gallery does not embed the attract policy');
const close = page.indexOf('\n', at + policy.length + 1);
const statement = page.slice(page.lastIndexOf('\n', at - 2) + 1, close === -1 ? page.length : close);
const top = prefix => lines.find(line => line.startsWith(prefix)) ?? '';
const data = top('const recipes=');
const own = JSON.parse(data.slice('const recipes='.length, -1));
const demo = recipes => new Function('recipes', statement + '\n' + top('const scenicFeatures=') + '\n' + top('const demoRecipes=') +
  '\nreturn demoRecipes.map(recipe => recipe.id);')(recipes);
const unfiltered = JSON.parse(readFileSync(unfilteredPath, 'utf8'));
console.log(JSON.stringify({library: own.map(recipe => recipe.id), attract: demo(own), unfilteredAttract: demo(unfiltered)}));
"""

if __name__ == '__main__':
    unittest.main()
