"""Real archive/Git/Node tests for historical Nocturne runtime custody."""
import base64
import hashlib
import gzip
import json
import os
import pathlib
import subprocess
import tarfile
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/recover_historical_runtimes.py"
NODE = pathlib.Path(subprocess.check_output(["which", "node"], text=True).strip())
WASM = bytes.fromhex(
    "0061736d01000000"
    "010401600000"
    "03020100"
    "0707010372756e0000"
    "0a040102000b"
)
WASM_ALT = WASM.replace(b"run", b"go!")
WASM_SHA = hashlib.sha256(WASM).hexdigest()


def put_zip(path, members):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)


def put_tar_gz(path, members):
    with tarfile.open(path, "w:gz") as archive:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mtime = 0
            archive.addfile(info, __import__("io").BytesIO(content))


def init_git_repo(repo):
    repo.mkdir(exist_ok=True)
    subprocess.run(["git", "init", "-b", "historical-fixture"], cwd=repo, check=True, capture_output=True)


def invoke(archive_root, git_root, output):
    return subprocess.run([
        "python3", str(SCRIPT), "--archive-root", str(archive_root),
        "--git-root", str(git_root), "--output", str(output),
    ], text=True, capture_output=True, check=False)


class HistoricalRuntimeRecovery(unittest.TestCase):
    def fixture(self, directory):
        base = pathlib.Path(directory)
        inputs = base / "archives"
        inputs.mkdir()
        js = b"export async function boot(){ return WebAssembly.instantiate(await (await fetch('../dist/nocturne.wasm')).arrayBuffer(), {}); }\n"
        html = ("<!doctype html><script>const wasm='" + base64.b64encode(WASM).decode() +
                "'; WebAssembly.instantiate(bytes, {});</script>").encode()
        nested = base / "nested.zip"
        put_zip(nested, {"runtime/nocturne.wasm": WASM, "runtime/engine.js": js})
        repo = base / "git"
        init_git_repo(repo)
        subprocess.run(["git", "config", "user.name", "Runtime Fixture"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "runtime-fixture@example.invalid"], cwd=repo, check=True)
        (repo / "dist").mkdir()
        (repo / "dist/nocturne.wasm").write_bytes(WASM)
        (repo / "Nocturne-Gallery.html").write_bytes(html)
        (repo / "boot.js").write_bytes(js)
        subprocess.run(["git", "add", "dist/nocturne.wasm", "Nocturne-Gallery.html", "boot.js"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "fixture historical runtime"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "tag", "v0.3.0"], cwd=repo, check=True)
        bundle = base / "runtime.bundle"
        subprocess.run(["git", "bundle", "create", str(bundle), "--all"], cwd=repo, check=True, capture_output=True)
        put_zip(inputs / "Nocturne-Workbench-v0.3.zip", {
            "Nocturne-Pearl-Fleet.html": html,
            "scripts/boot.js": js,
            "scripts/profile.js": b"export const sceneProfile = 'scene:tidal-glass';\n",
            "src/world.inc": b"static const int nswDetail = 8;\n",
            "private/credentials.json": b'{"token":"do-not-copy"}\n',
            "scripts/packed-loader.js": b"const bytes = new Uint8Array([0,97,115,109]); const packed='AAECAw=='+ 'BAUG'; new DecompressionStream('gzip'); WebAssembly.instantiate(bytes);\n",
            "archives/engine-v0.3.zip": nested.read_bytes(),
            "archive/runtime.bundle": bundle.read_bytes(),
            "catalogue/world-controls.json.gz": gzip.compress(b'{"worldControls":["scene:tidal-glass"]}\n', mtime=0),
        })
        put_tar_gz(inputs / "Nocturne-Observatory-v0.4.tar.gz", {
            "dist/nocturne.wasm": WASM,
            "catalogue/scenes.json": b'{"components":["scene:observatory"]}\n',
        })
        return inputs, repo

    def test_deduplicates_archives_nested_embedded_and_git_sources_with_real_node_validation(self):
        with tempfile.TemporaryDirectory(prefix="nocturne-runtime-positive-") as temp:
            inputs, repo = self.fixture(temp)
            output = pathlib.Path(temp) / "recovered"
            result = invoke(inputs, repo, output)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            manifest = json.loads((output / "manifest.json").read_text())
            modules = manifest["uniqueWasmModules"]
            self.assertEqual(len(modules), 1)
            module = modules[0]
            self.assertEqual(module["sha256"], WASM_SHA)
            self.assertTrue(module["validation"]["valid"])
            self.assertEqual(module["validation"]["validator"], "Node WebAssembly.Module")
            self.assertEqual(module["validation"]["imports"], [])
            self.assertEqual(module["validation"]["exports"], [{"name":"run","kind":"function"}])
            kinds = {origin["kind"] for origin in module["provenance"]}
            self.assertTrue({"archive-entry", "embedded-base64", "git-blob", "git-bundle-blob"}.issubset(kinds))
            self.assertTrue(any(origin.get("containerDepth", 0) > 0 for origin in module["provenance"]))
            self.assertIn("0.3", json.dumps(module["provenance"]))
            self.assertTrue(any(ref["name"].endswith("historical-fixture") for ref in manifest["gitRefs"]))
            self.assertTrue(any(c["path"].endswith("scenes.json") for c in manifest["companions"]))
            self.assertTrue(any(c["path"].endswith("world-controls.json") for c in manifest["companions"]))
            self.assertTrue(any(c["path"].endswith("world.inc") and c["sourceKind"] == "c-family-source"
                                for c in manifest["companions"]))
            self.assertTrue(any(c["path"].endswith("profile.js") for c in manifest["companions"]))
            self.assertTrue(any(x["path"].endswith("credentials.json") and x["reason"]
                                for x in manifest["excludedSources"]))
            self.assertTrue(any("Uint8Array" in x["detectedPatterns"] and "DecompressionStream" in x["detectedPatterns"]
                                for x in manifest["unresolvedLoaderEvidence"]))
            companion = next(c for c in manifest["companions"] if c["path"].endswith("Gallery.html"))
            self.assertTrue((output / companion["objectPath"]).is_file())
            self.assertTrue(manifest["callerEvidence"])
            self.assertTrue(manifest["archiveOccurrences"])
            self.assertTrue(any(a["containerDepth"] > 0 for a in manifest["archiveOccurrences"]))
            self.assertTrue(manifest["gitBundles"])
            self.assertTrue(any(any(r["name"] == "refs/heads/historical-fixture" for r in b["refs"])
                                for b in manifest["gitBundles"]))

            second = pathlib.Path(temp) / "recovered-again"
            again = invoke(inputs, repo, second)
            self.assertEqual(again.returncode, 0, again.stderr + again.stdout)
            self.assertEqual((output / "manifest.json").read_bytes(), (second / "manifest.json").read_bytes())
            self.assertEqual((output / module["objectPath"]).read_bytes(), WASM)
            stale = output / "objects/sha256" / ("f" * 64)
            stale.write_bytes(b"not reachable from this inventory")
            rerun = invoke(inputs, repo, output)
            self.assertEqual(rerun.returncode, 0, rerun.stderr + rerun.stdout)
            self.assertFalse(stale.exists())

    def test_invalid_module_is_reported_by_node_and_fails_run(self):
        with tempfile.TemporaryDirectory(prefix="nocturne-runtime-invalid-wasm-") as temp:
            inputs = pathlib.Path(temp) / "archives"; inputs.mkdir()
            repo = pathlib.Path(temp) / "git"; init_git_repo(repo)
            bad = b"\x00asm\x02\x00\x00\x00"
            put_zip(inputs / "Nocturne-v0.7-invalid.zip", {"bad.wasm": bad})
            output = pathlib.Path(temp) / "out"
            result = invoke(inputs, repo, output)
            self.assertNotEqual(result.returncode, 0)
            module = json.loads((output / "manifest.json").read_text())["uniqueWasmModules"][0]
            self.assertFalse(module["validation"]["valid"])
            self.assertIn("error", module["validation"])
            self.assertEqual(module["sizeBytes"], len(bad))
            self.assertEqual((output / module["objectPath"]).read_bytes(), bad)

    def test_node_rejects_valid_module_when_expected_content_hash_is_wrong(self):
        with tempfile.TemporaryDirectory(prefix="nocturne-runtime-hash-mismatch-") as temp:
            module_path = pathlib.Path(temp) / "module.wasm"
            module_path.write_bytes(WASM)
            result = subprocess.run([
                str(NODE), str(ROOT / "scripts/validate_historical_wasm.mjs")
            ], input=json.dumps({"modules": [{"path": str(module_path), "sha256": "0" * 64}]}),
                text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            item = json.loads(result.stdout)["results"][0]
            self.assertFalse(item["valid"])
            self.assertEqual(item["errorCode"], "sha256-mismatch")
            self.assertEqual(item["actualSha256"], WASM_SHA)

    def test_mutating_archive_and_module_bytes_changes_both_content_identities(self):
        with tempfile.TemporaryDirectory(prefix="nocturne-runtime-identity-") as temp:
            inputs = pathlib.Path(temp) / "archives"; inputs.mkdir()
            repo = pathlib.Path(temp) / "git"; init_git_repo(repo)
            archive = inputs / "Nocturne-v0.4.zip"
            put_zip(archive, {"dist/nocturne.wasm": WASM})
            first = pathlib.Path(temp) / "first"
            one = invoke(inputs, repo, first)
            self.assertEqual(one.returncode, 0, one.stderr + one.stdout)
            m1 = json.loads((first / "manifest.json").read_text())
            archive_sha1 = m1["archiveOccurrences"][0]["sha256"]
            module_sha1 = m1["uniqueWasmModules"][0]["sha256"]
            put_zip(archive, {"dist/nocturne.wasm": WASM_ALT})
            second = pathlib.Path(temp) / "second"
            two = invoke(inputs, repo, second)
            self.assertEqual(two.returncode, 0, two.stderr + two.stdout)
            m2 = json.loads((second / "manifest.json").read_text())
            self.assertNotEqual(archive_sha1, m2["archiveOccurrences"][0]["sha256"])
            self.assertNotEqual(module_sha1, m2["uniqueWasmModules"][0]["sha256"])

    def test_corrupt_nested_archive_is_an_explicit_error_not_silently_skipped(self):
        with tempfile.TemporaryDirectory(prefix="nocturne-runtime-nested-error-") as temp:
            inputs = pathlib.Path(temp) / "archives"; inputs.mkdir()
            repo = pathlib.Path(temp) / "git"; init_git_repo(repo)
            put_zip(inputs / "Nocturne-v0.2.zip", {"nested/hidden.zip": b"PK\x03\x04truncated"})
            output = pathlib.Path(temp) / "out"
            result = invoke(inputs, repo, output)
            self.assertNotEqual(result.returncode, 0)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertTrue(any("nested" in error["path"] and error["category"] == "nested-archive" for error in manifest["errors"]))

    def test_corrupt_standalone_gzip_is_an_explicit_error(self):
        with tempfile.TemporaryDirectory(prefix="nocturne-runtime-gzip-error-") as temp:
            inputs = pathlib.Path(temp) / "archives"; inputs.mkdir()
            repo = pathlib.Path(temp) / "git"; init_git_repo(repo)
            put_zip(inputs / "Nocturne-v0.8.zip", {"catalogue/world.json.gz": b"\x1f\x8btruncated"})
            output = pathlib.Path(temp) / "out"
            result = invoke(inputs, repo, output)
            self.assertNotEqual(result.returncode, 0)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertTrue(any(error["category"] == "nested-archive" and error["path"].endswith("world.json.gz")
                                for error in manifest["errors"]))

    def test_traversal_member_is_only_a_provenance_name_never_an_extraction_path(self):
        with tempfile.TemporaryDirectory(prefix="nocturne-runtime-traversal-") as temp:
            inputs = pathlib.Path(temp) / "archives"; inputs.mkdir()
            repo = pathlib.Path(temp) / "git"; init_git_repo(repo)
            put_zip(inputs / "Nocturne-v0.5.zip", {"../../escape.wasm": WASM})
            output = pathlib.Path(temp) / "out"
            result = invoke(inputs, repo, output)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            module = json.loads((output / "manifest.json").read_text())["uniqueWasmModules"][0]
            self.assertEqual((output / module["objectPath"]).read_bytes(), WASM)
            self.assertFalse((pathlib.Path(temp) / "escape.wasm").exists())


if __name__ == "__main__":
    unittest.main()
