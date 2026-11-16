"""Gallery admission: only artwork with provenance in the original series of explorations enters the Gallery.

native/contract/GALLERY-ADMISSION.json is the committed ledger (native/scripts/gallery_provenance.py). These tests
recompute it from the repository and require byte equality, so neither a new entry without provenance nor an edit
to the original corpus can change what the Gallery admits without a reviewed ledger change. They also check each
refusal class on real library entries and that the Gallery builder admits exactly the ledger.
"""
import copy
import importlib
import json
import sys
import unittest
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]
REPOSITORY = NATIVE.parent
sys.path.insert(0, str(NATIVE / 'scripts'))


def corpus_available():
    """The original corpus exists only in the source repository: a packaged SDK has no legacy/ directory, carries the
    committed ledger, and the Gallery admits from it. A source tree with legacy/ present must hold the whole corpus,
    so a missing or edited original fails the tests below rather than skipping them."""
    return (REPOSITORY / 'legacy/editions').is_dir()


# The public tree leaves out the fixture generators (tools/release/export_public_tree.py): the ledger counts their entries, so
# its recomputation and any check that picks a fixture entry belong to the source repository.
FIXTURES_LEFT_OUT = (REPOSITORY / 'PUBLIC-TREE-REPORT.json').is_file()


@unittest.skipUnless(corpus_available(), 'original corpus (legacy/ and git history) not present: provenance is recomputed in the source repository')
class GalleryAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gp = importlib.import_module('gallery_provenance')
        cls.ledger = cls.gp.read_ledger()
        cls.entries, cls.generator = cls.gp.library()
        cls.by_id = {e['id']: e for e in cls.entries}
        cls.resolver = cls.gp.Resolver()

    def classify(self, entry, generator=None):
        return self.gp.classify(entry, generator or self.generator.get(entry['id'], 'test'), self.resolver)[0]

    @unittest.skipIf(FIXTURES_LEFT_OUT, 'the ledger counts the fixture entries the public tree leaves out')
    def test_committed_ledger_equals_recomputation(self):
        expected = json.dumps(self.gp.compute_ledger(), indent=1, ensure_ascii=False) + '\n'
        self.assertEqual(self.gp.LEDGER.read_text(encoding='utf-8'), expected,
                         'GALLERY-ADMISSION.json is stale: run native/scripts/gallery_provenance.py --write-ledger and review the diff')

    def test_original_corpus_is_pinned(self):
        actual = {name: __import__('hashlib').sha256(b).hexdigest() for name, b in self.gp.original_corpus().items()}
        self.assertEqual(actual, self.ledger['corpusSha256'], 'the original corpus changed; provenance claims must not be made to resolve by editing it')
        self.assertIn('legacy/editions/0.9-rc.2-Nocturne-Workbench-Docs.html', actual)
        self.assertEqual(actual['legacy/editions/0.9-rc.2-Nocturne-Workbench-Docs.html'],
                         '375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')

    def test_every_admitted_entry_is_original_or_operator_admitted(self):
        decisions = {d['id']: d for d in self.ledger['operatorDecisions']}
        for row in self.ledger['admitted']:
            with self.subTest(row['id']):
                self.assertIn(row['id'], self.by_id)
                cls = self.classify(self.by_id[row['id']])
                if cls == 'original-placeholder':
                    self.assertIn('only presentation of this original effect: specimen kept', row['evidence'])
                    cls = 'original'
                if cls == 'original-substitute':
                    self.assertIn('source-painter twin not admitted: prior rendering kept', row['evidence'])
                    cls = 'original'
                self.assertEqual(cls, row['class'])
                if cls != 'original':
                    self.assertEqual(cls, 'rc4-authored')
                    self.assertEqual(decisions[row['id']]['decision'], 'admit')
                self.assertTrue(row['evidence'] and not any(e.startswith('FAIL') for e in row['evidence']))

    @unittest.skipIf(FIXTURES_LEFT_OUT, 'the public tree leaves out the fixture entries this classifies')
    def test_synthetic_fixture_is_refused(self):
        # A generator whose every entry the census classes synthetic, found in the census and not named here.
        by_generator = json.loads((REPOSITORY / 'native/evidence/provenance-census-20261114/PROVENANCE-CENSUS.json').read_text())['byGenerator']
        fixture = sorted(g for g, classes in by_generator.items() if {c for c, n in classes.items() if n} == {'synthetic'})[0]
        entry = next(e for e in self.entries if self.generator[e['id']] == fixture)
        self.assertEqual(self.classify(entry), 'synthetic')
        self.assertNotIn(entry['id'], self.gp.admitted_ids())

    def test_unresolvable_claim_is_refused(self):
        entry = copy.deepcopy(next(e for e in self.entries if self.classify(e) == 'original' and 'originalEffect' in e))
        entry['originalEffect'] = 'no-such-original-effect-zq'
        self.assertEqual(self.classify(entry), 'unresolved-claim')
        entry = copy.deepcopy(entry)
        entry.pop('originalEffect')
        entry['provenance'] = {'release': '0.9.0-rc.2', 'component': 'x', 'htmlSha256': '0' * 64}
        self.assertEqual(self.classify(entry), 'unresolved-claim')

    def test_catalogue_identity_without_source_is_refused(self):
        for ident in ('weather/silver-squall', 'weather/snowglobe'):
            with self.subTest(ident):
                self.assertIsNone(self.resolver.identity(ident))
                self.assertEqual(self.classify(self.by_id['study-' + ident.replace('/', '-') + '-isolated']), 'unresolved-claim')

    def test_original_in_invented_application_frame_is_refused(self):
        isolated = self.by_id['study-weather-chrysanthemum-isolated']
        framed = self.by_id['study-weather-chrysanthemum-application']
        self.assertEqual(self.classify(isolated), 'original')
        self.assertEqual(self.classify(framed), 'original-framed')
        self.assertIn(isolated['id'], self.gp.admitted_ids())
        self.assertNotIn(framed['id'], self.gp.admitted_ids())

    def test_placeholder_specimen_of_an_effect_shown_in_an_original_scene_is_refused(self):
        admitted = set(self.gp.admitted_ids())
        specimens = [e for e in self.entries if self.gp.placeholder(e)]
        self.assertTrue(specimens)
        for e in specimens:
            twins = [x for x in self.entries if x['id'] in admitted and self.gp.subject_effect(x) == self.gp.subject_effect(e)
                     and not self.gp.placeholder(x)]
            with self.subTest(e['id']):
                if twins:
                    self.assertNotIn(e['id'], admitted)

    def test_generic_rendering_beside_its_source_painter_twin_is_refused(self):
        admitted = set(self.gp.admitted_ids())
        substitutes = [e for e in self.entries if self.gp.substitute(e)]
        self.assertTrue(substitutes)
        for e in substitutes:
            with self.subTest(e['id']):
                self.assertIn(self.gp.twin(e), self.by_id)
                if self.gp.twin(e) in admitted:
                    self.assertNotIn(e['id'], admitted)
        self.assertIn('study-weather-chrysanthemum-isolated', admitted)
        self.assertNotIn('study-weather-chrysanthemum-isolated-generic', admitted)

    def test_tdf_wordmark_specimens_are_withheld(self):
        for e in self.entries:
            if self.generator[e['id']] == 'tdf_gallery_studies':
                with self.subTest(e['id']):
                    self.assertEqual(self.classify(e), 'withheld')
                    self.assertNotIn(e['id'], self.gp.admitted_ids())

    def test_gallery_presents_admitted_entries_without_invented_scenery(self):
        library = json.loads((NATIVE / 'recipes.json').read_text()) + __import__('gallery_cases').build_cases()
        shipped = self.gp.admit(library)
        self.assertTrue(any(any(self.gp.invented_scenery(c) for c in self.by_id[r['id']]['commands']) for r in shipped),
                        'expected source-route studies whose fixtures carry the placeholder mesh')
        for r in shipped:
            with self.subTest(r['id']):
                self.assertFalse(any(self.gp.invented_scenery(c) for c in r['commands']))
                original = [c for c in self.by_id[r['id']]['commands'] if not self.gp.invented_scenery(c)]
                self.assertEqual(r['commands'], original)

    def test_original_scene_in_application_mode_is_not_framed(self):
        # The original windows scene runs in "application" mode; only the invented window 90 frame is refused.
        entry = self.by_id['original-background-plasma']
        self.assertEqual(entry.get('mode'), 'application')
        self.assertEqual(self.classify(entry), 'original')

    def test_admit_refuses_a_stale_ledger(self):
        library = [e for e in self.entries if e['id'] != self.ledger['admitted'][0]['id']]
        with self.assertRaises(SystemExit) as raised:
            self.gp.admit(library)
        self.assertIn('no longer has', str(raised.exception))

    def test_gallery_builder_admits_exactly_the_ledger(self):
        build_gallery = importlib.import_module('build_gallery')
        library = json.loads((NATIVE / 'recipes.json').read_text()) + __import__('gallery_cases').build_cases()
        built = build_gallery.nullifiedRecipes(library)
        self.assertEqual([r['id'] for r in built], [i for i in (r['id'] for r in library) if i in set(self.gp.admitted_ids())])


if __name__ == '__main__':
    sys.path.insert(0, str(NATIVE / 'examples'))
    unittest.main()
