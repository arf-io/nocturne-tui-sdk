# Nocturne GUI SDK implementation prompt

Implement a graphical Nocturne SDK whose pixel/vector components carry the TUI's aesthetic, materials and motion into graphical applications. Build a GUI rendering and layout backend with proportional text, icons, menus and normal graphical controls. A terminal canvas embedded in a window is not sufficient. Keep the TUI backend available and preserve shared simulation, artwork geometry, clocks, owned data, event contracts and semantic identities. This document is a brief for a GUI backend that is not built yet.

## Visual system

Use a deep charcoal/navy stage, warm pale text, muted teal, lavender and copper accents. Use space and fine borders to establish hierarchy. Keep panels quiet so the artwork is dominant. Keep typography readable at normal zoom and use monospace for values and code. Avoid promotional cards, process narration and unexplained implementation vocabulary in product controls.

The viewport remains visible on the left with tools to the right, or above tools on narrow screens. Each tool region scrolls independently. A component catalogue uses actual rendered state thumbnails, concise names and searchable families. Show selected element properties without hiding the scene. The user can switch between visual authoring and structured Workshop code without losing state.

## GUI backend and layout

Use an appropriate GUI toolkit or pixel/vector renderer. Keep device-independent layout separate from device pixels; support high-DPI scaling, resizing, clipping, scrolling, nested containers, alignment and minimum/intrinsic sizes. Expose real buttons, text fields, lists, trees, menus, tabs, dialogs, tooltips, progress indicators and graphical windows, with visible hover, focus, selected, pressed, disabled and validation states. Icons and text have their own metrics; do not force GUI layout onto terminal-cell dimensions.

Provide a native accessibility tree with roles, names, values, focus, actions and live updates. Support keyboard navigation, touch and pointer capture, screen readers, platform text input and IME. Adapt platform windowing and menus without changing the shared scene model.

## Material and geometry contract

Retain cell, half, braille and hybrid sampling as distinct TUI and optional stylized GUI modes. Give the GUI backend continuous pixel/vector geometry and text rather than a mandatory character grid. Braille uses all 256 geometric masks; full occupancy remains eight dots and never fills the spaces between dots with foreground color. Preserve pseudo-alpha, depth ordering, floor contacts, leaf contours/veins and changing backgrounds. Window text remains readable as its plane recedes; full source remains available through a reader.

Make logical GUI, device-pixel, cell and world coordinate conversions explicit. Use the shared geometry and appropriate backend hit testing. Camera orbit picks one fixed world anchor per gesture. Support head, dolly, crane, follow, spacecraft and orbit rigs with independently configurable XYZ actions, sensitivity, enable and inversion. Default wheel movement changes distance; roll remains an explicit configurable action.

## Fonts and imported assets

Support TDF, OTF and TTF assets with explicit loading errors, selected font metrics, shaping, fallback and baseline alignment. Preserve TDF artwork while allowing scalable GUI typography. Support imported 3D models with complete vertices, faces, materials, hierarchy and transforms; do not silently downsample geometry. Keep asset ownership and serialization consistent across backends and exports.

Retain material combinations, animated text, fields, surfaces, particles, weather, projected windows, graph geometry, camera motion and compositing. Translate the existing artistic controls into GUI renderers without substituting generic gradients, stock effects or unrelated artwork.

## Motion and interaction

Native time drives animation. Rendering is pure. Preserve independent scenic travel and water-phase timelines when controls change. Manual camera edits do not stop scripted flight; brake does. Retain banked/flat turns, roll, climb, dive and fast-travel star trails. Provide pause and reduced-motion behavior while keeping text editing and controls responsive.

Select, drag, place, resize and reorder elements using one composition model. Provide keyboard and numeric equivalents, atomic undo/redo, import/export and named saved projects. State restoration includes assets, text, event bindings, materials and clocks. Unknown fields, invalid resources or allocation failure reject atomically with actionable feedback; never silently discard user content.

## Text and application input

Support complete Unicode, grapheme-safe movement, bidi presentation, IME, paste, selection and copy. Retain arbitrary practical document sizes using the SDK's growable storage. Let prompt weather and cursor appearance be configured directly: period/duty, ink/material animation, shape and custom glyph. Physical input follows native ownership across prompt, help, readers and an eight-entry modal stack. Do not route a hidden textarea around a modal.

## Code and integration

Expose the GUI backend and composition contract through C, WASM/TypeScript, Python, Go and Rust. Generate runnable examples and applications from the same normalized project, with a declared backend and explicit platform dependencies. Expose documented event/time entry points and retain semantic IDs. Keep host device/clipboard/network actions outside the pure core. Use caller-owned C buffers or binding-owned allocations and copy borrowed data before the next call. No imported project may execute arbitrary code.

## Acceptance

Demonstrate actual component states and interaction sequences, not mock screens. Test actual pixel/vector GUI components, layout, high-DPI text and icons, platform menus, accessibility-tree behavior and font/model import. Test direct manipulation plus keyboard alternatives, undo/redo, long Unicode import/export, asset identity, rejected transaction rollback, camera anchor invariance, independent flight and phase clocks, all 256 braille masks and background gap pixels. Compile and execute generated programs against the packaged SDK, compare deterministic shared state and backend frames across bindings, and test the actual browser at wide and narrow sizes. Publish Markdown, per-language PDF references and screenshots generated from the same source manifest, and document what each test covers.
