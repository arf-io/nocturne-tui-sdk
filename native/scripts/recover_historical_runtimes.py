#!/usr/bin/env python3
"""Recursively inventory and content-address historical Nocturne runtimes."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

SCHEMA = "nocturne-historical-runtime-inventory/1"
WASM_MAGIC = b"\x00asm"
ARCHIVE_NAME_RE = re.compile(r"^(?:Nocturne|nocturne).*\.(?:zip|tar\.gz)$", re.I)
VERSION_RE = re.compile(r"(?<!\d)v?(\d+(?:\.\d+){1,2}(?:[-.]rc[.-]?\d+)?)(?!\d)", re.I)
BASE64_RE = re.compile(rb"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{32,}={0,2}(?![A-Za-z0-9+/])")
TEXT_EXTS = {".html", ".htm", ".js", ".mjs", ".cjs", ".ts", ".tsx"}
C_FAMILY_EXTS = {".c", ".h", ".hh", ".hpp", ".hxx", ".cc", ".cpp", ".cxx", ".inc"}
CONTROL_WORDS = ("catalog", "scene", "world", "control", "config", "manifest", "schema", "field", "effect", "component", "version", "art")
SENSITIVE_PATH_RE = re.compile(r"(?:^|/)(?:credential(?:s)?|secret(?:s)?|private-keys?)(?:/|$)|(?:^|/)(?:\.env(?:\.[^/]*)?|[^/]*(?:credential|password|secret)[^/]*\.(?:json|ya?ml|txt))$|\.(?:pem|key|p12)$", re.I)
ARCHIVE_SUFFIXES = (".zip", ".tar.gz", ".tgz", ".tar", ".gz", ".7z", ".rar")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version_labels(*labels: str) -> list[str]:
    return sorted({match.group(1).lower() for label in labels for match in VERSION_RE.finditer(label)})


def source_text_candidate(name: str) -> bool:
    return source_extension_candidate(name) and sensitive_path_reason(name) is None


def source_extension_candidate(name: str) -> bool:
    path = PurePosixPath(name)
    ext = path.suffix.lower()
    low = name.lower()
    if sensitive_path_reason(name) is not None:
        return True
    if ext in TEXT_EXTS or ext in C_FAMILY_EXTS:
        return True
    return ext == ".json" and any(word in low for word in CONTROL_WORDS) and path.name.lower() not in {"package-lock.json", "pnpm-lock.yaml"}


def sensitive_path_reason(name: str) -> str | None:
    return "sensitive-path-name" if SENSITIVE_PATH_RE.search(name.lower()) else None


def is_nested_archive(name: str, data: bytes) -> bool:
    low = name.lower()
    return low.endswith(ARCHIVE_SUFFIXES) or data.startswith(b"PK\x03\x04") or data.startswith(b"PK\x05\x06") or data.startswith(b"PK\x07\x08") or data.startswith(b"ustar")


class Recovery:
    def __init__(self, output: Path, max_depth: int, max_entry_bytes: int):
        self.output = output
        self.max_depth = max_depth
        self.max_entry_bytes = max_entry_bytes
        self.modules: dict[str, dict] = {}
        self.companions: list[dict] = []
        self.components: list[dict] = []
        self.caller_evidence: list[dict] = []
        self.excluded_sources: list[dict] = []
        self.unresolved_loader_evidence: list[dict] = []
        self.archives: list[dict] = []
        self.errors: list[dict] = []
        self.release_labels: set[str] = set()
        self.git_bundles: dict[str, dict] = {}
        self._bundle_processed: set[str] = set()
        self._archive_serial = 0
        (output / "objects" / "sha256").mkdir(parents=True, exist_ok=True)

    def write_object(self, data: bytes) -> tuple[str, str]:
        digest = sha(data)
        rel = f"objects/sha256/{digest}"
        path = self.output / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != data:
                raise RuntimeError(f"content-address collision at {rel}")
        else:
            path.write_bytes(data)
        return digest, rel

    def add_module(self, data: bytes, origin: dict):
        digest, object_path = self.write_object(data)
        item = self.modules.setdefault(digest, {
            "sha256": digest, "sizeBytes": len(data), "objectPath": object_path,
            "provenance": [], "validation": None,
        })
        if origin not in item["provenance"]:
            item["provenance"].append(origin)
        return digest

    def add_source(self, data: bytes, name: str, origin: dict):
        if not source_extension_candidate(name):
            return
        reason = sensitive_path_reason(name)
        if reason:
            self.excluded_sources.append({"path": name, "reason": reason, "sizeBytes": len(data),
                                          "sha256": sha(data), "provenance": origin})
            return
        digest, object_path = self.write_object(data)
        suffix = PurePosixPath(name).suffix.lower()
        record = {"path": name, "sha256": digest, "sizeBytes": len(data), "objectPath": object_path,
                  "sourceKind": "c-family-source" if suffix in C_FAMILY_EXTS else "text-source", "provenance": origin}
        self.companions.append(record)
        if suffix not in TEXT_EXTS:
            return
        embedded_hashes = []
        for match in BASE64_RE.finditer(data):
            encoded = match.group(0)
            try:
                decoded = base64.b64decode(encoded, validate=True)
            except (ValueError, base64.binascii.Error):
                continue
            if decoded.startswith(WASM_MAGIC):
                module_origin = dict(origin)
                module_origin.update({"kind": "embedded-base64", "sourceSha256": digest,
                                      "sourceObjectPath": object_path,
                                      "embeddedByteOffset": match.start(), "embeddedByteLength": len(encoded)})
                embedded_hashes.append(self.add_module(decoded, module_origin))
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = ""
        caller_patterns = []
        for pattern in ("WebAssembly.instantiate", "WebAssembly.compile", "WebAssembly.Module", "fetch(", ".wasm"):
            if pattern.lower() in text.lower():
                caller_patterns.append(pattern)
        loader_patterns = []
        if re.search(r"new\s+Uint8Array\s*\(\s*\[", text, re.I):
            loader_patterns.append("Uint8Array")
        if re.search(r"['\"][A-Za-z0-9+/=]{8,}['\"]\s*\+\s*['\"][A-Za-z0-9+/=]{4,}['\"]", text):
            loader_patterns.append("constructed-base64")
        for pattern in ("DecompressionStream", "inflate", "gunzip", "pako.ungzip", ".wasm.gz"):
            if pattern.lower() in text.lower():
                loader_patterns.append(pattern)
        if loader_patterns:
            self.unresolved_loader_evidence.append({"sourcePath": name, "sourceSha256": digest,
                "provenance": origin, "detectedPatterns": sorted(set(loader_patterns)),
                "status": "loader-bytes-not-decoded-by-inventory"})
        labels = version_labels(name)
        catalog_ids = sorted(set(re.findall(r"(?:scene:[a-z0-9][a-z0-9._-]*)", text, re.I)))
        self.components.append({
            "sourcePath": name, "sourceSha256": digest, "sourceObjectPath": object_path,
            "sourceKind": "html" if suffix in {".html", ".htm"} else "javascript-or-typescript",
            "versionLabels": labels, "declaredCatalogIds": catalog_ids,
            "classification": "wasm-backed-source" if embedded_hashes or caller_patterns else "javascript-only-source-candidate",
            "classificationEvidence": {"embeddedModuleSha256": sorted(set(embedded_hashes)), "callerPatterns": caller_patterns},
            "provenance": origin,
        })
        if embedded_hashes or caller_patterns:
            self.caller_evidence.append({
                "sourcePath": name, "sourceSha256": digest, "provenance": origin,
                "detectedPatterns": caller_patterns,
                "embeddedModuleSha256": sorted(set(embedded_hashes)),
                "declaredCatalogIds": catalog_ids,
            })

    def error(self, category: str, path: str, digest: str | None, message: str, parent: str | None = None):
        self.errors.append({"category": category, "path": path, "sha256": digest, "parent": parent, "message": message})

    def process_archive(self, data: bytes, source_path: str, parent: str | None, entry_path: str | None,
                        depth: int, ancestors: tuple[str, ...]):
        digest = sha(data)
        self._archive_serial += 1
        occurrence_id = f"archive-{self._archive_serial:06d}"
        suffix = source_path.lower()
        archive_type = "zip" if suffix.endswith(".zip") or data.startswith(b"PK") else "tar"
        record = {
            "occurrenceId": occurrence_id, "sourcePath": source_path,
            "sha256": digest, "sizeBytes": len(data), "format": archive_type,
            "containerDepth": depth, "parentArchiveOccurrence": parent,
            "containerEntryPath": entry_path, "versionLabels": version_labels(source_path, entry_path or ""),
            "members": [],
        }
        self.archives.append(record)
        self.release_labels.update(record["versionLabels"])
        if digest in ancestors:
            self.error("nested-archive-cycle", source_path, digest, "archive repeats in its own parent chain", parent)
            return
        if depth > self.max_depth:
            self.error("nested-archive-depth", source_path, digest, f"maximum nested depth {self.max_depth} exceeded", parent)
            return
        next_ancestors = (*ancestors, digest)
        try:
            if archive_type == "zip":
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    for index, info in enumerate(archive.infolist()):
                        name = info.filename
                        member = {"index": index, "path": name, "sizeBytes": info.file_size,
                                  "compressedBytes": info.compress_size, "directory": info.is_dir()}
                        record["members"].append(member)
                        if info.is_dir():
                            continue
                        if info.file_size > self.max_entry_bytes:
                            self.error("entry-size-limit", f"{source_path}!/{name}", None,
                                       f"entry size {info.file_size} exceeds configured limit {self.max_entry_bytes}", occurrence_id)
                            continue
                        try:
                            child = archive.read(info)
                        except Exception as exc:
                            self.error("archive-member-read", f"{source_path}!/{name}", None, f"{type(exc).__name__}: {exc}", occurrence_id)
                            continue
                        member["sha256"] = sha(child)
                        self.process_member(child, name, occurrence_id, source_path, depth, next_ancestors)
            else:
                with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
                    for index, info in enumerate(archive.getmembers()):
                        name = info.name
                        member = {"index": index, "path": name, "sizeBytes": info.size,
                                  "directory": info.isdir(), "type": info.type.decode("ascii", "replace") if isinstance(info.type, bytes) else str(info.type)}
                        record["members"].append(member)
                        if not info.isfile():
                            if info.issym() or info.islnk():
                                self.error("archive-link-member", f"{source_path}!/{name}", None, "link members are listed but never followed or extracted", occurrence_id)
                            continue
                        if info.size > self.max_entry_bytes:
                            self.error("entry-size-limit", f"{source_path}!/{name}", None,
                                       f"entry size {info.size} exceeds configured limit {self.max_entry_bytes}", occurrence_id)
                            continue
                        stream = archive.extractfile(info)
                        child = stream.read() if stream else b""
                        member["sha256"] = sha(child)
                        self.process_member(child, name, occurrence_id, source_path, depth, next_ancestors)
        except (zipfile.BadZipFile, tarfile.TarError, OSError, EOFError) as exc:
            self.error("nested-archive" if depth else "top-level-archive", source_path, digest,
                       f"{type(exc).__name__}: {exc}", parent)

    def process_member(self, data: bytes, member_path: str, archive_id: str,
                      source_path: str, depth: int, ancestors: tuple[str, ...]):
        display = f"{source_path}!/{member_path}"
        lower_name = member_path.lower()
        if lower_name.endswith(".bundle") or data.startswith(b"# v2 git bundle") or data.startswith(b"# v3 git bundle"):
            self.process_git_bundle(data, display, archive_id, depth)
            return
        if lower_name.endswith(".gz") and not lower_name.endswith((".tar.gz", ".tgz")):
            self.process_gzip_entry(data, display, member_path, archive_id, source_path, depth)
            return
        if is_nested_archive(member_path, data):
            if member_path.lower().endswith((".7z", ".rar")):
                self.error("unsupported-nested-archive", display, sha(data), "archive format is not supported; entry retained in inventory", archive_id)
            else:
                self.process_archive(data, display, archive_id, member_path, depth + 1, ancestors)
            return
        origin = {"kind": "archive-entry", "sourceArchive": source_path,
                  "archiveOccurrenceId": archive_id, "containerDepth": depth,
                  "entryPath": member_path, "versionLabels": version_labels(source_path, member_path)}
        self.release_labels.update(origin["versionLabels"])
        if PurePosixPath(member_path).suffix.lower() == ".wasm":
            self.add_module(data, origin)
        self.add_source(data, member_path, origin)

    def process_gzip_entry(self, data: bytes, display: str, member_path: str,
                           parent_id: str, source_path: str, depth: int):
        digest = sha(data)
        self._archive_serial += 1
        occurrence_id = f"archive-{self._archive_serial:06d}"
        record = {"occurrenceId": occurrence_id, "sourcePath": display, "sha256": digest,
                  "sizeBytes": len(data), "format": "gzip-file", "containerDepth": depth + 1,
                  "parentArchiveOccurrence": parent_id, "containerEntryPath": member_path,
                  "versionLabels": version_labels(source_path, member_path), "members": []}
        self.archives.append(record)
        try:
            expanded = gzip.decompress(data)
        except (OSError, EOFError) as exc:
            self.error("nested-archive", display, digest, f"{type(exc).__name__}: {exc}", parent_id)
            return
        if len(expanded) > self.max_entry_bytes:
            self.error("entry-size-limit", display, sha(expanded),
                       f"gzip output {len(expanded)} exceeds configured limit {self.max_entry_bytes}", occurrence_id)
            return
        inner_name = member_path[:-3]
        record["members"].append({"index": 0, "path": inner_name, "sizeBytes": len(expanded),
                                  "sha256": sha(expanded), "directory": False})
        self.process_member(expanded, inner_name, occurrence_id, source_path, depth + 1, (digest,))

    def process_git_bundle(self, data: bytes, display: str, archive_id: str, depth: int):
        digest = sha(data)
        bundle = self.git_bundles.setdefault(digest, {
            "sha256": digest, "sizeBytes": len(data), "refs": [], "archiveProvenance": [],
            "uniqueBlobCount": 0, "validation": None,
        })
        origin = {"kind": "git-bundle-entry", "archiveOccurrenceId": archive_id,
                  "containerDepth": depth, "entryPath": display}
        if origin not in bundle["archiveProvenance"]:
            bundle["archiveProvenance"].append(origin)
        if digest in self._bundle_processed:
            return
        self._bundle_processed.add(digest)
        import tempfile
        with tempfile.TemporaryDirectory(prefix="nocturne-git-bundle-") as temp:
            bundle_path = Path(temp) / "history.bundle"
            repo_path = Path(temp) / "repo.git"
            bundle_path.write_bytes(data)
            listed = subprocess.run(["git", "bundle", "list-heads", str(bundle_path)],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if listed.returncode != 0:
                bundle["validation"] = {"valid": False, "error": listed.stderr.decode("utf-8", "replace").strip()}
                self.error("nested-archive", display, digest, "invalid Git bundle: " + bundle["validation"]["error"], archive_id)
                return
            refs = []
            for line in listed.stdout.decode("utf-8", "replace").splitlines():
                parts = line.split(None, 1)
                if len(parts) == 2:
                    refs.append({"objectId": parts[0], "name": parts[1]})
            bundle["refs"] = sorted(refs, key=lambda item: item["name"])
            cloned = subprocess.run(["git", "clone", "--mirror", str(bundle_path), str(repo_path)],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if cloned.returncode != 0:
                message = cloned.stderr.decode("utf-8", "replace").strip()
                bundle["validation"] = {"valid": False, "error": message}
                self.error("nested-archive", display, digest, "Git bundle clone failed: " + message, archive_id)
                return
            refs_found = self.process_git(repo_path, bundle_context={
                "bundleSha256": digest,
                "bundleRefNames": [r["name"] for r in bundle["refs"]],
                "bundleOccurrencePath": display,
            }, include_worktree=False)
            bundle["uniqueBlobCount"] = refs_found["blobCount"]
            bundle["validation"] = {"valid": True, "method": "git bundle list-heads + git clone --mirror", "refCount": len(refs)}

    def process_git(self, git_root: Path, bundle_context: dict | None = None, include_worktree: bool = True):
        def git(*args, check=True):
            return subprocess.run(["git", "-C", str(git_root), *args], check=check,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        refs_proc = git("for-each-ref", "--sort=refname", "--format=%(refname)%09%(objectname)")
        refs = []
        for line in refs_proc.stdout.decode().splitlines():
            name, oid = line.split("\t", 1)
            refs.append({"name": name, "objectId": oid})
        ls = git("ls-files", "-z", check=False) if include_worktree else subprocess.CompletedProcess([],0,b"",b"")
        for raw_name in ls.stdout.split(b"\x00"):
            if not raw_name:
                continue
            name = raw_name.decode("utf-8", "replace")
            if Path(name).suffix.lower() != ".wasm" and not source_extension_candidate(name):
                continue
            path = git_root / name
            try:
                data = path.read_bytes()
            except OSError as exc:
                self.error("tracked-source-read", name, None, f"{type(exc).__name__}: {exc}")
                continue
            origin = {"kind": "tracked-worktree-file", "gitRootLabel": git_root.name, "path": name}
            if path.suffix.lower() == ".wasm":
                self.add_module(data, origin)
            self.add_source(data, name, origin)
        rev = git("rev-list", "--all", "--objects", check=False)
        objects = []
        seen = set()
        for line in rev.stdout.decode("utf-8", "replace").splitlines():
            try:
                oid, name = line.split(" ", 1)
            except ValueError:
                continue
            suffix = Path(name).suffix.lower()
            if suffix != ".wasm" and not source_extension_candidate(name):
                continue
            if oid in seen:
                continue
            seen.add(oid)
            objects.append((oid, name))
        if objects:
            batch = subprocess.Popen(["git", "-C", str(git_root), "cat-file", "--batch"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = batch.communicate(b"".join((oid + "\n").encode() for oid, _ in objects))
            if batch.returncode != 0:
                self.error("git-cat-file", git_root.name, None, stderr.decode("utf-8", "replace").strip())
            else:
                stream = io.BytesIO(stdout)
                for oid, name in objects:
                    header = stream.readline().decode("ascii", "replace").strip().split()
                    if len(header) != 3 or header[1] != "blob":
                        self.error("git-object-read", name, None, f"expected blob response for {oid}")
                        continue
                    size = int(header[2]); data = stream.read(size); stream.read(1)
                    origin = ({"kind": "git-bundle-blob", **bundle_context,
                               "blobObjectId": oid, "path": name,
                               "reachableFromNamedRefs": True} if bundle_context else
                              {"kind": "git-blob", "gitRootLabel": git_root.name,
                               "blobObjectId": oid, "path": name,
                               "reachableFromNamedRefs": True})
                    if Path(name).suffix.lower() == ".wasm":
                        self.add_module(data, origin)
                    self.add_source(data, name, origin)
        return {"refs": refs, "blobCount": len(objects)}

    def validate_modules(self, node_script: Path):
        requests = []
        for digest, module in sorted(self.modules.items()):
            requests.append({"sha256": digest, "path": str(self.output / module["objectPath"])})
        proc = subprocess.run([shutil.which("node") or "node", str(node_script)],
                              input=json.dumps({"modules": requests}), text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode != 0:
            self.error("node-validator", str(node_script.name), None,
                       f"Node validator exited {proc.returncode}: {proc.stderr.strip()}")
            return None
        try:
            result = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            self.error("node-validator-output", node_script.name, None, str(exc))
            return None
        by_hash = {item["sha256"]: item for item in result["results"]}
        for digest, module in self.modules.items():
            module["validation"] = by_hash.get(digest, {"valid": False, "error": "Node omitted module result"})
        return result.get("nodeVersion")

    def finalize_relationships(self):
        module_names: dict[str, set[str]] = {}
        for module in self.modules.values():
            for origin in module["provenance"]:
                path = origin.get("entryPath") or origin.get("path") or origin.get("sourcePath") or ""
                module_names.setdefault(PurePosixPath(path).name.lower(), set()).add(module["sha256"])
        component_lookup = {(c["sourceSha256"], c["sourcePath"]): c for c in self.components}
        for evidence in self.caller_evidence:
            text_name = evidence["sourcePath"].lower()
            candidates = set(evidence["embeddedModuleSha256"])
            raw = (self.output / next(c["sourceObjectPath"] for c in self.components
                                     if c["sourceSha256"] == evidence["sourceSha256"] and c["sourcePath"] == evidence["sourcePath"])).read_bytes()
            decoded = raw.decode("utf-8", "ignore").lower()
            for name, digests in module_names.items():
                if name and name in decoded:
                    candidates.update(digests)
            if "webassembly." in decoded and not candidates:
                # Explicitly weak same-release candidates are kept separate from exact links.
                source_origin = evidence["provenance"]
                archive = source_origin.get("sourceArchive")
                for module in self.modules.values():
                    if any(origin.get("sourceArchive") == archive for origin in module["provenance"]):
                        candidates.add(module["sha256"])
                evidence["linkConfidence"] = "same-archive-candidate"
            else:
                evidence["linkConfidence"] = "embedded-bytes-or-explicit-filename" if candidates else "unresolved"
            evidence["moduleSha256Candidates"] = sorted(candidates)
            component = component_lookup.get((evidence["sourceSha256"], evidence["sourcePath"]))
            if component:
                component["classification"] = "wasm-backed-source" if candidates else "javascript-only-source-candidate"
                component["classificationEvidence"]["linkedModuleSha256Candidates"] = sorted(candidates)

    def build_manifest(self, archive_root: Path, git_root: Path, git_refs: list[dict], node_version: str | None):
        for module in self.modules.values():
            module["provenance"].sort(key=lambda item: json.dumps(item, sort_keys=True))
        modules = sorted(self.modules.values(), key=lambda item: item["sha256"])
        companions = sorted(self.companions, key=lambda item: (item["path"], item["sha256"], json.dumps(item["provenance"], sort_keys=True)))
        components = sorted(self.components, key=lambda item: (item["sourcePath"], item["sourceSha256"], json.dumps(item["provenance"], sort_keys=True)))
        callers = sorted(self.caller_evidence, key=lambda item: (item["sourcePath"], item["sourceSha256"], json.dumps(item["provenance"], sort_keys=True)))
        return {
            "schema": SCHEMA,
            "archiveRootLabel": archive_root.name,
            "gitRootLabel": git_root.name,
            "extractorSha256": sha(Path(__file__).read_bytes()),
            "validatorSha256": sha((Path(__file__).parent / "validate_historical_wasm.mjs").read_bytes()),
            "nodeVersion": node_version,
            "archiveOccurrences": self.archives,
            "topLevelArchiveCount": len([a for a in self.archives if a["containerDepth"] == 0]),
            "gitRefs": git_refs,
            "gitBundles": sorted(self.git_bundles.values(), key=lambda item: item["sha256"]),
            "uniqueWasmModules": modules,
            "companions": companions,
            "components": components,
            "callerEvidence": callers,
            "excludedSources": sorted(self.excluded_sources, key=lambda e: (e["path"], json.dumps(e["provenance"], sort_keys=True))),
            "unresolvedLoaderEvidence": sorted(self.unresolved_loader_evidence, key=lambda e: (e["sourcePath"], e["sourceSha256"])),
            "javascriptOnlyCandidates": [c for c in components if c["classification"] == "javascript-only-source-candidate"],
            "observedVersionLabels": sorted(self.release_labels),
            "unresolvedReleaseFamilies": [{"version": "0.1.9", "status": "requested source/runtime family not reconciled by available source identity"}],
            "errors": sorted(self.errors, key=lambda e: (e["category"], e["path"], e.get("parent") or "", e["message"])),
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", required=True, type=Path)
    parser.add_argument("--git-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-nested-depth", type=int, default=8)
    parser.add_argument("--max-entry-bytes", type=int, default=512 * 1024 * 1024)
    args = parser.parse_args(argv)
    if not args.archive_root.is_dir() or not args.git_root.is_dir():
        parser.error("archive-root and git-root must be existing directories")
    args.output.mkdir(parents=True, exist_ok=True)
    recovery = Recovery(args.output, args.max_nested_depth, args.max_entry_bytes)
    archives = sorted(path for path in args.archive_root.iterdir()
                      if path.is_file() and ARCHIVE_NAME_RE.match(path.name))
    for path in archives:
        try:
            data = path.read_bytes()
        except OSError as exc:
            recovery.error("top-level-archive-read", path.name, None, f"{type(exc).__name__}: {exc}")
            continue
        recovery.process_archive(data, path.name, None, None, 0, ())
    try:
        git_refs = recovery.process_git(args.git_root)["refs"]
    except (OSError, subprocess.CalledProcessError) as exc:
        git_refs = []
        recovery.error("git-source-scan", args.git_root.name, None, f"{type(exc).__name__}: {exc}")
    node_script = Path(__file__).with_name("validate_historical_wasm.mjs")
    node_version = recovery.validate_modules(node_script)
    recovery.finalize_relationships()
    manifest = recovery.build_manifest(args.archive_root, args.git_root, git_refs, node_version)
    manifest_path = args.output / "manifest.json"
    referenced = {item["objectPath"] for item in manifest["uniqueWasmModules"]}
    referenced.update(item["objectPath"] for item in manifest["companions"])
    object_root = args.output / "objects" / "sha256"
    if object_root.exists():
        for object_file in object_root.iterdir():
            rel = object_file.relative_to(args.output).as_posix()
            if object_file.is_file() and rel not in referenced:
                object_file.unlink()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    invalid = [m for m in manifest["uniqueWasmModules"] if not m["validation"] or not m["validation"].get("valid")]
    if recovery.errors or invalid:
        print(f"recovery recorded {len(recovery.errors)} archive/source errors and {len(invalid)} invalid WASM modules; manifest={manifest_path}", file=sys.stderr)
        return 1
    print(f"recovered {len(manifest['uniqueWasmModules'])} unique WASM modules from {len(archives)} top-level archives and {len(git_refs)} named refs; manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
