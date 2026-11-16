"""Exercise the actual C ABI against an independent exact-arithmetic reference."""
from pathlib import Path
import ctypes
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bindings/python'))
from nocturne_native import NativeScene
from reference_compositing import BLENDS, OPERATORS, referenceComposite

COLOR_PAIRS = ((0, 0xffffff), (0xffffff, 0), (0, 0), (0xffffff, 0xffffff),
               (0x2080c0, 0xc04080), (0xc04080, 0x2080c0),
               (0x00ff80, 0xff0080), (0xff0000, 0x00ffff),
               (0x7f8040, 0x80803f))
ALPHA_PAIRS = ((0, 0), (0, 65535), (65535, 0), (65535, 65535),
               (49151, 32768), (32768, 49151), (1, 65534), (65534, 1))
MATRIX_CASES = (len(BLENDS) - 1) * len(OPERATORS) * len(COLOR_PAIRS) * len(ALPHA_PAIRS)


class NativeCompositingReferenceTests(unittest.TestCase):
    def assertRgbWithinOne(self, actual, expected):
        self.assertEqual(actual[1], expected[1], 'alpha16 must be exact')
        for shift in (16, 8, 0):
            self.assertLessEqual(abs(((actual[0] >> shift) & 255) - ((expected[0] >> shift) & 255)), 1,
                                 'RGB8 tolerance is one quantization unit, not a blend-space tolerance')

    def testAllNativeBlendsAndOperatorsAgainstIndependentEquations(self):
        with NativeScene(2030) as scene:
            before = scene.snapshot()
            count = 0
            for mode, blend in enumerate(BLENDS):
                if blend == 'dissolve':
                    continue
                for operatorIndex, operation in enumerate(OPERATORS):
                    for base, source in COLOR_PAIRS:
                        for baseAlpha, sourceAlpha in ALPHA_PAIRS:
                            with self.subTest(blend=blend, operation=operation, base=hex(base), source=hex(source), alpha=(baseAlpha, sourceAlpha)):
                                expected = referenceComposite(base, source, baseAlpha, sourceAlpha, blend, operation)
                                actual = scene.composite(base, source, baseAlpha, sourceAlpha, mode, operatorIndex)
                                self.assertRgbWithinOne(actual, expected)
                            count += 1
            self.assertEqual(count, MATRIX_CASES)
            self.assertEqual(scene.snapshot(), before, 'pure composition cannot mutate a scene')

    def testDissolveHasOnlyTheTwoDocumentedCoverageOutcomes(self):
        with NativeScene(2030) as scene:
            seen = set()
            for operatorIndex, operation in enumerate(OPERATORS):
                for base, source in COLOR_PAIRS:
                    for sourceAlpha in (0, 32768, 65535):
                        endpoints = (0,) if sourceAlpha == 0 else (65535,) if sourceAlpha == 65535 else (0, 65535)
                        expected = {referenceComposite(base, source, 49151, alpha, 'normal', operation) for alpha in endpoints}
                        for seed in (0, 1, 17, 2030, 0xffffffff):
                            actual = scene.composite(base, source, 49151, sourceAlpha, 26, operatorIndex, seed)
                            self.assertTrue(any(actual[1] == e[1] and all(abs(((actual[0] >> s) & 255) - ((e[0] >> s) & 255)) <= 1 for s in (16, 8, 0)) for e in expected))
                            self.assertEqual(actual, scene.composite(base, source, 49151, sourceAlpha, 26, operatorIndex, seed))
                            if sourceAlpha == 32768 and operation == 'source':
                                seen.add(actual[1])
            self.assertEqual(seen, {0, 65535}, 'finite seed cases must exercise both branches')

    def testNativeRejectionDoesNotWriteTheOutputBuffer(self):
        with NativeScene(2030) as scene:
            valid = [0x123456, 0xfedcba, 49151, 32768, 0, 0, 0]
            for index, bad in enumerate((0x1000000, 0x1000000, 65536, 65536, 28, 13)):
                args = valid.copy()
                args[index] = bad
                out = (ctypes.c_uint32 * 2)(0xdeadbeef, 0xcafef00d)
                self.assertEqual(scene._lib.nrComposite(*args, out), -1)
                self.assertEqual(tuple(out), (0xdeadbeef, 0xcafef00d))
            self.assertEqual(scene._lib.nrComposite(*valid, None), -1)


if __name__ == '__main__':
    unittest.main()
