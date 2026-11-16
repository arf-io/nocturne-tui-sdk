# Nocturne material contract, prototype v0.1

## What is implemented

One C11 material renderer; owned language-frame bindings; five example composition layouts; a browser gallery; an interactive POSIX terminal host; static Node/Go/Rust host examples. General-purpose framework adapters and individually packaged widget APIs are not part of this release.

The shared core is C, not Rust. The C core made it possible to execute the same integer code natively and in WASM in this environment. Python, Go, and TypeScript were tested. The Rust wrapper could not be compiled because the toolchain was absent. Moving the implementation behind the ABI to Rust later would be an explicit migration, not a claim about this prototype.

## Determinism boundary

Inputs are schema/engine version, normalized config, explicit motion milliseconds, text/data, dimensions, world origin, and seed. Output is ordered `(glyph, foreground, background, flags)` cells. Canonical bytes serialize each word little-endian, 16 bytes per cell. Actual glyph rasterization is outside the boundary.

No wall-clock access, random mutable generator, retained state, allocation, terminal output, or floating-point arithmetic occurs in the core. The 1024-phase Q1000 sine table is committed. Do not regenerate it casually: an altered table is an output migration. Native and WASM share exactly that source. Interpolation is integer encoded-RGB interpolation, not claimed perceptually uniform or linear-light interpolation.

Rendering does not integrate velocity. It evaluates an explicit time. Missing a display frame does not change subsequent material state. Defaults, schema indices, glyph choices, and integer rounding are part of the prototype output contract. The reference fixtures capture it. A future renderer version may change output only with an explicit fixture review/version decision.

## Clocks and immediate data

Decorative motion is sampled at 30 Hz in the example hosts. Data events update state and render immediately using the last sampled motion timestamp. They do not call the motion step and are not deferred to the next motion deadline. Multiple output writes can therefore occur between two decorative samples. The browser and Python hosts include an independent roughly 80 Hz synthetic source to make this visible.

The Python host has one output owner and uses `selectors` for input plus the nearest motion/data deadline. Input gets an immediate render before consulting the animation clock. The native renderer itself is faster than the demonstration host's ANSI conversion in most supplied studies. Actual output backpressure still matters; “immediate” means no deliberate animation-frame gate, not zero physical display latency.

Host pause freezes the last sampled timestamp. `motion=0`, a material configuration option, is distinct: it evaluates at zero. Host resume excludes paused wall time. Frame skipping produces the next logical sample without an accumulated burst.

## Stars and geometry

A coordinate/seed hash selects occupancy, glyph, peak palette color, period, phase, and twinkle envelope. It is not dependent on surface traversal order or frame count. Resize does not reseed the sky. World origins permit adjacent raw material tiles to address the same field. Prompt-centering and demo layout geometry can move overlays independently of the background during resize.

Stars use a specified smoothed attack/fade envelope, a configurable active duty window, and floor/peak brightness. A star's position/color identity is stable during its animation. “Random order” means many unrelated coordinate-keyed phases, not consumption of a frame-local random generator.

Width/height allow 0..512 and 0..256 respectively. The WASM shim preallocates for the maximum. Demo controls collapse to a simple prompt below 64 columns or 26 rows. The bindings allocate owned outputs; the core writes to caller-owned storage.

## Focused fields

The row period is repeatedly multiplied by `1000 / neighborSpeedPermille`; 500 exactly doubles the period at each step until the protective cap. Row saturation and brightness repeatedly multiply by their own thousandths factors with integer truncation. The row period saturates at a large finite bound (`2^52` ms), avoiding overflow for very distant rows; those rows are effectively static on a human timescale. Forcing 1000 in each falloff yields a full-surface field without decay.

Fields support linear, diagonal, wave, rotation, and plasma. Palette interpolation closes the final stop back to the first. A separate full-hue mode cycles HSV; an RGB-sine mode uses phase-shifted red/green/blue channels. Color saturation and brightness controls apply separately. A field's user-facing cycle period is the temporal phase cycle; pixel trajectories in a combined multi-wave field may be visually more complex.

## Cell materials and compositing

Sampling modes: one RGB background per cell; upper-half foreground/background samples; left-half samples; density-shade glyph; braille ordered dither using eight material samples. For stars, glyph presets include mixed, braille, punctuation, math, and a bounded custom set.

One cell cannot retain arbitrary text plus a separate half-block glyph. A text/star overlay replaces the cell glyph, computes a flattened background from half-block samples when needed, applies a scrim if configured, and emits its foreground. Braille dots share one foreground. This is terminal-cell compositing, not alpha channels or independent multicolor subpixel pixels.

The C renderer composes material, stars, and the selected showcase layout in that order. There is no public arbitrary layer graph or mask API yet. Hosts can use raw cells as a bottom layer and overlay their framework's content. A reusable compositing API and independent widget primitives should preserve this same frame contract.

## ABI and safety

`NsConfig` is 448 bytes: 64 signed integer slots, eight gradient colors, eight peak star colors, 32 custom code points. Only 49 slots currently have names. `NsCell` is four uint32 words. Version/size introspection is checked by bindings.

`nsRender` returns the cell count or -1 invalid config, -2 insufficient/null output, -3 invalid text. C callers must supply live, aligned, nonoverlapping buffers and follow pointer/length contracts. It is not possible for the C function to validate arbitrary memory addresses. No buffers are retained.

Python and Go must not concurrently mutate/render the same configured Surface. Rust rendering uses immutable config references and owned output. The WASM instance has reusable scratch memory and must not be reentered; returned arrays are copied. Use independent instances for workers. The core is stateless when callers keep their inputs immutable and output buffers separate.

The demo uses a deliberately restricted single-cell glyph profile. Unsupported/wide/control characters are replaced, never passed through as terminal controls. The host, not untrusted text, constructs ANSI. This is not a full Unicode layout implementation.

## Next API extraction

The showcase already renders fractional bars, half-height tracks, boxes, a menu, selected rows, a modal, chromatic text, four cursor treatments, and a synthetic braille scope. These functions are still internal composition helpers. Promote them to independent widgets only after specifying their content/layout/events and framework ownership. Do not label the demo compositions a finished multi-framework widget SDK.
