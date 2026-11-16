# Exporting a source release

`export_git.py` writes a source release from one committed tree, together with a Git bundle that holds every named ref of the repository: branches, annotated tags, `refs/archive/` and `refs/handoff/`. It never renames or deletes a ref. It builds nothing, and its record reports `SOURCE_HISTORY_VERIFIED` with `runtimeQualification` set to `NOT_ASSESSED_BY_EXPORTER`.

The SDK packager is a separate tool. It requires passing build, frozen-source and four-runtime results and a matching source fingerprint. `RELEASE.json` sets the build label and the source baseline for both tools. The baseline must be an existing ancestor commit. The source export reads `RELEASE.json` from the selected commit. The SDK packager also requires the working copy to match the committed bytes.

## Export

Commit your work first, and finish any concurrent branch work: if a named ref or `HEAD` moves during the export, the exporter fails. Pass the full commit SHA:

```sh
python3 tools/release/export_git.py \
  --root /absolute/path/to/nocturne \
  --commit FULL_40_CHARACTER_COMMIT_SHA \
  --output /absolute/path/to/new-source-export
```

The output directory must be new and outside the repository. The exporter needs no toolchain, dependency cache or network, and it reads committed Git objects directly, so staged, unstaged and untracked files are ignored. It refuses a shallow repository, and every named ref must resolve to a commit it can inspect.

## Output

| File | Contents |
| --- | --- |
| `Nocturne-BUILD-COMMIT-Source.tar.gz` | Every regular file of the selected tree under `nocturne/`, with exact bytes and executable modes. |
| `Nocturne-BUILD-COMMIT-History.bundle` | One union of all named refs and the worktree's `HEAD`, with the original object IDs. |
| `Nocturne-BUILD-COMMIT-Full-Source.md` | Every UTF-8 text file in full. Each binary file is listed with its path, size, Git object ID and SHA-256. |
| `SOURCE-TREE.json` | The selected commit and tree, and for every path its Git blob ID, mode, size and SHA-256. |
| `NAMED-REFS.json` | All named refs and `HEAD` before the export. |
| `EXPORT-VERIFICATION.json` | The Git commands run with their exit codes and output hashes, the history content audit, the results of restoring the bundle and extracting the tarball, tool versions and artifact hashes. |
| `SHA256SUMS.txt` | Hashes of all the files above, including `EXPORT-VERIFICATION.json`. |

In file names, `BUILD` is the build from `RELEASE.json` and `COMMIT` is the first twelve characters of the SHA. Every manifest carries the full SHA.

The tarball has sorted paths, fixed owner IDs and names, Git's executable modes, the commit timestamp on every member, and a zero gzip timestamp with an empty filename. With the same Python and zlib, repeated exports give byte-identical tarballs. Git attributes such as `export-ignore` and `export-subst` and checkout filters never remove or rewrite a file. The bundle holds exact refs and objects; its bytes can differ between Git versions.

The audit reads every distinct reachable tree, including files deleted in later commits. The export fails on font files, dependency caches, compiler distributions, credential file names and private-key envelopes. It also fails on symlinks and submodules. It never leaves out a prohibited file and then calls the tree complete. Source, locks, manifests and refs are never rewritten.

## Verify

The exporter checks its own output in new temporary directories: `git bundle verify`, a fetch of `refs/*:refs/*`, a comparison of the restored refs, `git fsck --full --strict`, a comparison of the selected tree, and a fresh tar extraction compared with the restored Git files by bytes and mode.

To repeat the history check and create a checkout:

```sh
git init --bare /absolute/path/to/new-history.git
git -C /absolute/path/to/new-history.git bundle verify /absolute/path/to/History.bundle
git -C /absolute/path/to/new-history.git fetch --no-tags \
  /absolute/path/to/History.bundle 'refs/*:refs/*'
git -C /absolute/path/to/new-history.git fetch --no-tags \
  /absolute/path/to/History.bundle HEAD
git -C /absolute/path/to/new-history.git fsck --full --strict
git -C /absolute/path/to/new-history.git worktree add --detach \
  /absolute/path/to/new-checkout FULL_40_CHARACTER_COMMIT_SHA
```

Use the exact names from `EXPORT-VERIFICATION.json`, and compare the restored refs with `NAMED-REFS.json`, not only the branch tips. Extract the tarball separately and compare it with `SOURCE-TREE.json`. To test the code, run `sh qualify-native.sh --profile rc2 --strict --capture` in the new checkout.

## Test

```sh
python3 native/tests/test_git_export.py
```

The test uses disposable Git repositories with annotated tags and custom refs, real bundles and fresh restores, and real tar bytes. It covers reproducibility, binary, executable and Unicode content, Git attributes, uncommitted-file isolation, and the refusals above.
