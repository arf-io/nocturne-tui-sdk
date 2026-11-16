"""Every third-party Python module the qualification scripts and tests import is pinned in
tools/requirements-qualification.txt, the one file tools/bootstrap.py and the CI workflows
install. A fresh host provisioned from that file must not fail a plan case on ImportError."""
import ast
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native"
REQUIREMENTS = ROOT / "tools/requirements-qualification.txt"
# Python the plan executes: native/scripts and native/tests, the qualification helpers under
# tools/qualification, the ci-policy discovery over tools/ci, and the Python host the binding tests load.
SCANNED = ("native/scripts", "native/tests", "tools/qualification", "tools/ci", "native/hosts/python")
# Folders the scanned files put on sys.path (relative to the repository root); gen_transaction_streams.py inserts
# native/tests/fixtures/transactions for its composite_scenes fixture module.
LOCAL_ROOTS = ("native/scripts", "native/tests", "native/bindings/python", "native/hosts/python", "native/examples",
               "native/web", "native/tests/fixtures/transactions", "native", "tools", "tools/qualification", "tools/ci", "tools/release", "integrations", ".")
# Import name -> distribution name as pip spells it (case-insensitive match below).
DISTRIBUTIONS = {"PIL": "Pillow", "markdown": "Markdown", "yaml": "PyYAML", "playwright": "playwright",
                 "prompt_toolkit": "prompt_toolkit", "pypdf": "pypdf", "reportlab": "reportlab", "numpy": "numpy"}
OWN_PACKAGES = {"nocturne_native", "nocturne", "native"}


def is_local(module):
    return any((ROOT / rel / (module + ".py")).is_file() or (ROOT / rel / module).is_dir() for rel in LOCAL_ROOTS)


def third_party_imports():
    """{module: sorted importing files} for every absolute import that is neither stdlib nor local."""
    stdlib = set(sys.stdlib_module_names)
    found = {}
    for rel in SCANNED:
        for path in sorted((ROOT / rel).glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    modules = [node.module.split(".")[0]]
                else:
                    continue
                for module in modules:
                    if module in DISTRIBUTIONS:
                        pass  # a checkout file named like a distribution never hides the import
                    elif module in stdlib or module in OWN_PACKAGES or is_local(module):
                        continue
                    found.setdefault(module, set()).add(path.relative_to(ROOT).as_posix())
    return {module: sorted(files) for module, files in found.items()}


def pinned_distributions():
    pins = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)", line)
        if match:
            pins[match.group(1).lower()] = match.group(2)
        else:
            pins[line.lower()] = None
    return pins


class QualificationRequirements(unittest.TestCase):
    def test_the_scanner_sees_the_known_third_party_modules(self):
        imports = third_party_imports()
        for module in ("playwright", "yaml", "PIL", "markdown", "pypdf", "reportlab"):
            with self.subTest(module=module):
                self.assertIn(module, imports)

    def test_the_python_floor_the_pins_need_is_declared(self):
        """Markdown 3.11.x requires Python 3.11; the README and tools/bootstrap.py must say so,
        or a 3.10 host aborts the whole requirements install, losing playwright and PyYAML too."""
        self.assertIn("Markdown==3.11", REQUIREMENTS.read_text(encoding="utf-8"))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("The test runner (`qualify-native.sh`) needs Python 3.11 or later", readme)
        bootstrap = (ROOT / "tools/bootstrap.py").read_text(encoding="utf-8")
        self.assertIn("sys.version_info < (3, 11)", bootstrap)

    def test_every_third_party_import_has_a_known_distribution(self):
        unknown = sorted(m for m in third_party_imports() if m not in DISTRIBUTIONS)
        self.assertEqual(unknown, [], "add each module's distribution to DISTRIBUTIONS or pin it")

    def test_every_third_party_import_is_pinned_in_the_qualification_requirements(self):
        pins = pinned_distributions()
        imports = third_party_imports()
        missing = {}
        unpinned = {}
        for module, files in sorted(imports.items()):
            distribution = DISTRIBUTIONS.get(module, module)
            version = pins.get(distribution.lower(), "ABSENT")
            if version == "ABSENT":
                missing[distribution] = files
            elif version is None:
                unpinned[distribution] = files
        self.assertEqual(missing, {}, "not listed in tools/requirements-qualification.txt")
        self.assertEqual(unpinned, {}, "listed without an exact == version")


if __name__ == "__main__":
    unittest.main()
