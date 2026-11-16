## Change

Continue the Nocturne history with visible scene controls, stable automatic 2D/3D layouts, deterministic text and weather, and recoverable shaped/spatial windows. Keep immediate local input and explicit elapsed-time presentation.

## Validation

Run `sh scripts/check_atelier.sh` and `python3 scripts/check_atelier_browser.py`. In CI, `REQUIRE_RUST=1 REQUIRE_PTY=1` remain mandatory. See `docs/atelier/TEST_REPORT.md` for actual local execution and missing-tool disclosure. Existing fixtures are not auto-accepted or replaced.

## Boundaries

New high-level APIs are TypeScript. Native renderer/bindings remain unchanged. No provider connection, sensor capture, remote CI execution, registry publication or complete native framework-adapter suite is implied. The optional existing PTY skin remains a separately tested opt-in integration, not a sandbox.
