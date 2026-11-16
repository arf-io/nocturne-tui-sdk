## Summary

Add Nocturne Studio without changing legacy ABI behavior:12 fields,14 primitives,48 palettes,15 mock compositions,8 tmux profiles,4 bindings and bounded adapters.

## Verification

Read docs/TEST_REPORT_STUDIO.md and dist/studio evidence. Native Python/Go/WASM fixtures, legacy regressions, sanitizers and browser/POSIX host checks executed. Rust source reviewed, not executed in the delivery runtime; CI must compile and test it before treating Rust as verified.

## Boundaries

No claimed AFD drop-in plugin, arbitrary-shell repainting, verified TD Figlet binary execution, font redistribution, registry publication or remote infrastructure actions.
