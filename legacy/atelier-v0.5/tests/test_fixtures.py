"""Verify the native renderer against checked-in canonical frame hashes."""
import pathlib
import sys
import json
import hashlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne import Surface

class GoldenTests(unittest.TestCase):
    def testNativeGoldenFrames(self):
        fixtures=json.loads((ROOT/'tests/fixtures.json').read_text())
        for fixture in fixtures:
            with self.subTest(fixture=fixture['name']):
                surface=Surface(**fixture['values'])
                if 'palette' in fixture:surface.setPalette(fixture['palette'])
                if 'starPalette' in fixture:surface.setStarPalette(fixture['starPalette'])
                if 'glyphs' in fixture:surface.setGlyphs(fixture['glyphs'])
                actual=hashlib.sha256(surface.render(fixture['timeMs'],text=fixture['text']).tobytes()).hexdigest()
                self.assertEqual(fixture['sha256'],actual)
