"""Authoritative release declaration and completed-build policy for local packaging.

All Git operations are read-only. This module never promotes a candidate, rewrites
a declaration, regenerates a lockfile, or treats a declared status as execution.
"""
from pathlib import Path
import json
import re
import subprocess

BUILD_PATTERN = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
VERIFICATION_PATH = "native/evidence/BUILD-VERIFICATION.json"
MANDATORY_BUILD_FLAGS = ("complete", "sourceUnchanged", "localBuildVerified", "fourRuntimeVerified")

def rejectDuplicateKeys(pairs):
    """Decode one JSON object without accepting duplicate authoritative fields."""
    value = {}
    for key, entry in pairs:
        if key in value:
            raise ValueError("Duplicate release field: " + key)
        value[key] = entry
    return value

def runGit(root, *arguments):
    """Run read-only Git arguments and return bytes; fail with the original diagnostic."""
    result = subprocess.run(["git", *arguments], cwd=Path(root), capture_output=True, timeout=60)
    if result.returncode:
        raise ValueError("Git " + " ".join(arguments) + ": " +
                         result.stderr.decode("utf-8", "replace").strip())
    return result.stdout

def loadReleaseIdentity(root, commit="HEAD", *, requireWorktreeMatch=True):
    """Read release identity from the selected committed RELEASE.json.

    Inputs: a repository root, a commit selector, and whether the current
    declaration must be byte-identical to that committed object.
    Output: the retained declaration plus sourceCommit and artifactPrefix.
    Errors: ValueError for unsafe build labels, ambiguous metadata, an invalid or
    non-ancestor baseline, a changed declaration, or an unsupported receipt path.
    Example: loadReleaseIdentity(Path.cwd())["artifactPrefix"].
    """
    root = Path(root).resolve()
    selected = runGit(root, "rev-parse", "--verify", commit + "^{commit}").decode().strip()
    raw = runGit(root, "show", selected + ":RELEASE.json")
    path = root / "RELEASE.json"
    if requireWorktreeMatch and (
        path.is_symlink() or not path.is_file() or path.read_bytes() != raw
    ):
        raise ValueError("RELEASE.json must match its committed bytes")
    release = json.loads(raw, object_pairs_hook=rejectDuplicateKeys)
    if not isinstance(release, dict):
        raise ValueError("RELEASE.json must contain an object")
    build = release.get("build")
    if not isinstance(build, str) or len(build) > 128 or not BUILD_PATTERN.fullmatch(build):
        raise ValueError("Release build must be a portable semantic version")
    baseline = release.get("sourceBaseline")
    if not isinstance(baseline, str) or not COMMIT_PATTERN.fullmatch(baseline):
        raise ValueError("Release source baseline must be an exact full commit SHA")
    try:
        kind = runGit(root, "cat-file", "-t", baseline).decode().strip()
    except ValueError as error:
        raise ValueError("Release source baseline commit is unavailable") from error
    if kind != "commit":
        raise ValueError("Release source baseline must identify a commit")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", baseline, selected],
                              cwd=root, capture_output=True, timeout=60)
    if ancestor.returncode != 0:
        raise ValueError("Release source baseline must be an ancestor of the exported commit")
    if type(release.get("fullRC4Qualified")) is not bool:
        raise ValueError("Release fullRC4Qualified must be a boolean")
    if release.get("verification") != VERIFICATION_PATH:
        raise ValueError("Release verification must name " + VERIFICATION_PATH)
    for key in ("state", "scope"):
        if not isinstance(release.get(key), str) or not release[key].strip():
            raise ValueError("Release " + key + " must be explicit")
    return {**release, "sourceCommit": selected, "artifactPrefix": "Nocturne-" + build}

def validateCompletedBuild(receipt, currentFingerprint, declaredFullQualification=False):
    """Require completed frozen four-runtime evidence before SDK packaging.

    This validates supplied policy inputs; it does not execute the qualification.
    Every mandatory flag must be the boolean True, both recorded source hashes
    must agree, and the current source must match that same SHA-256. A separate
    full-RC4 declaration needs a corresponding fullRC4Qualified execution result.
    Raises ValueError instead of silently accepting missing or string-valued flags.
    """
    if not isinstance(receipt, dict) or any(
        receipt.get(key) is not True for key in MANDATORY_BUILD_FLAGS
    ):
        raise ValueError("A completed frozen four-runtime pass is required")
    recorded = receipt.get("sourceAfter")
    if not isinstance(recorded, str) or not SHA256_PATTERN.fullmatch(recorded):
        raise ValueError("A complete source fingerprint is required")
    if receipt.get("sourceBefore") != recorded or currentFingerprint != recorded:
        raise ValueError("Current source differs from the tested fingerprint")
    if type(declaredFullQualification) is not bool:
        raise ValueError("Declared fullRC4Qualified must be a boolean")
    if declaredFullQualification and receipt.get("fullRC4Qualified") is not True:
        raise ValueError("Declared fullRC4Qualified requires its own executed qualification")

