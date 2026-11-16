# Observatory acceptance contracts / test-first

Existing v0.1/v0.2/v0.3 snapshots remain authoritative. New behavior is additive.

1. Explicit wall-time animation supports 30/60 FPS with no duration/phase change. Input transactions present synchronously without asking a motion scheduler. Local typed ink is always visible, including while a workspace expands.
2. Shared OKLCh-to-sRGB C/native/WASM path holds requested lightness and hue while reducing chroma to gamut. Invalid inputs return errors. Old HSV modes remain only for legacy replay compatibility.
3. Gradient spacing is specified in screens per adjacent stop; custom positive stop intervals, offscreen pivot and independent axis periods have bounded typed controls.
4. Bounded event weather and 3D projection preserve text and clip behind the camera. Keyboard/pointer select the same stable IDs; 2D/list navigation remains available.
5. Optional explicit audio capture; sensor samples have sequence/time validation, TTL, bounds and smoothing. No silent capture, invented hardware samples, or audio recording.
6. PTY adapter owns exactly one terminal output channel, never evaluates screen text, preserves child explicit styles, forwards terminal queries to emulator replies, handles resize/cleanup. Requires a vetted VT emulator. Compatibility is not inferred from a screenshot.
7. Gallery mockups clearly identify synthetic data and nonfunctional integrations; commands cannot execute from the offline gallery.
8. Full docs, agent handoff, original source, Git history, test evidence, and required Rust CI are delivered together.
