# CI

Three workflows run the tests:

- `.forgejo/workflows/nocturne.yml` runs on pushes, pull requests and manual dispatch, on Ubuntu 24.04. It runs qualification and the coverage gate. A manual dispatch also runs delivery: measured qualification, shipping-binary qualification and independent qualification of the extracted SDK packages. The delivery job has a 30-hour limit and each test step a two-hour limit.
- `.github/workflows/nocturne.yml` has native, supplemental and qualification jobs and a coverage ratchet job, all on Ubuntu 24.04, for pushes, pull requests and manual dispatch.
- `.github/workflows/rc4-native.yml` is run by hand on Ubuntu 24.04 and macOS 14. It builds the native library, runs the strict captured four-runtime plan, and runs the Terminal Kit, Bubble Tea and Ratatui host tests. The pseudo-terminal host tests run on Linux only; on macOS the job reports BLOCKED for them and exits nonzero. There is no Windows job.

Every action is pinned to a full commit ID, and `action-pins.json` records the original tag and the GitHub API source of each pin. To change a pin, update that record and run `python3 native/tests/test_release_ci_policy.py`.

The workflows use Rust 1.88.0, Python 3.13, Node 22.16.0, Go 1.23.2 and TypeScript 5.8.3. Python packages come from `tools/requirements-qualification.txt`, which pins Playwright 1.55.0. Clang, LLD and FFmpeg come from the runner's package manager.

Dependencies are fetched in a separate step (`npm ci`, `cargo fetch --locked`, `go mod download`), and the tests then run offline: Cargo with `--offline --locked`, Go with `-mod=readonly`. No manifest or lock file is regenerated, and a changed dependency file after the fetch fails the job. Build targets and host test directories are under `RUNNER_TEMP`, outside the checkout. The last step of the manual workflow uploads the `nocturne-ci` directory and `native/evidence`, even after a failure.

## Coverage

`coverage_gate.py` measures native production line coverage and requires at least 70%. It also compares `coverage-ratchet.json` with the copies on `origin/main` and `origin/integration` and uses the highest threshold. An empty profile or an empty production denominator fails. Python, Go and Rust tests run the same instrumented C shared library, and their LLVM profiles are merged. The strict dependency audit runs on a separate uninstrumented library, so the shipping SDK does not depend on the LLVM runtime. The coverage figure covers the C core. WASM semantics are tested separately.

After all checks pass on `main` or `integration`, `ratchet_coverage.py` commits the new floor if the measured coverage is higher. It uses an ordinary push. If another update lands first, the push is rejected and nothing is forced.

## Other tools

| Tool | Purpose |
|---|---|
| `cargo_artifact.py` | Finds the example executable in a Cargo JSON build log |
| `check_tdfiglet.py` | Runs external TDF scenes in both modes and both runtimes |
| `prepare_shaping.py` | Downloads hash-checked shaping fixtures to a directory outside the checkout |
| `run_historical_tests.py` | Runs the Python and npm tests of the original root editions |
| `verify_packages.py` | Extracts each emitted SDK archive and verifies it |

## Tests

```sh
python3 -m unittest discover -s tools/ci -p 'test_*.py' -v
```

These tests compile a small instrumented C program, run its LLVM profiles through the gate, and exercise real Git refs. They test the gate's decisions, not the coverage of the Nocturne source.
