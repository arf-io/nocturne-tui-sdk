# Spatial Atelier / public API and integration

This is a source SDK, not independently published packages. The new high-level layout, camera, typography, particles and kinetic-window modules are **TypeScript**. The existing C11 renderer, OKLCh conversion, cell composition and native façades remain present for Rust, Python, Go and TypeScript/WASM. There is no hidden Node process inside a purportedly native binding.

## Entry points

| Module | Public entry | Result / ownership |
|---|---|---|
| `spatial.ts` | `layoutGraph(graph, options)` | Owned layout with positions, bounds, original edges, SCCs and warnings. |
| `spatial.ts` | `GraphLayoutJob` | Cooperative fixed-iteration job; never solve from rendering. |
| `spatial.ts` | `CameraRig` | Explicit look/orbit/pan/dolly and reusable projection snapshots. |
| `text_fx.ts` | `sampleText`, `textDuration`, `TextPlayer` | Per-character glyph, pose, opacity, hue offset and trail. |
| `particles.ts` | `sampleBurst`, `particleOptions` | Points, line segments and glows at one explicit time. |
| `window_fx.ts` | `WindowManager`, `windowMask`, `warpWindowCell` | Stable state, source-space masks and reversible geometry. |
| `atelier.ts` | `AtelierModel`, `AtelierRenderer`, `activateAtelier` | A working host-neutral composition plus interaction routes. |
| `atelier_settings.ts` | `exportAtelierSettings`, `loadAtelierSettings` | Validated visual settings, not conversation/session restore. |
| `cell_profile.ts` | `safeCellCodepoint`, `requireCellGlyph` | A pinned, deliberately restricted one-cell display profile. |

`dist/typescript/*.js` and `.d.ts` are included. Run `tsc -p tsconfig.json` after modifying TypeScript. `examples/atelier_embed.mjs` is executable from the checkout root, not pseudocode.

## Host ownership and immediate input

The host owns its clock, input decoding, terminal or parent framework, data sources and output. The model never owns a second terminal writer. Input must do the following in the same event callback:

```typescript
model.input(character);                  // authoritative local draft now
const result = renderer.render(model);   // existing decorative timestamp
present(result.frame);                  // do not enqueue behind the motion tick
```

The timer path independently sets `model.setTime(elapsedMotionMs)` and presents a frame. FPS is a presentation ceiling. At the same timestamp, effect duration and phase are the same at 30 and 60 FPS. Device/display/transport latency is not zero. A blocked writer may coalesce pending visual frames, never discard domain events or commands.

Local input always bypasses reveals. `sampleText(..., {local:true})` returns full immediate ink even when asked to hide. Use reveals for received text, labels and transitions; do not pass local edits through a deferred typewriter.

## Automatic graphs

A graph has `nodes:[{id,label?,width?,height?,pin?:{x,y,z}}]` and `edges:[{source,target}]`. IDs are unique, 1..80 ASCII word/dot/colon/dash characters. Edges must name existing nodes. Duplicate edges reject. Limits are 256 nodes and 2048 edges; force layout accepts 1..600 iterations. Configuration rejects unknown fields and non-finite values.

Layered layout condenses strongly connected components, assigns directed ranks, makes eight alternating barycentric ordering sweeps and allocates node-size-aware rank/row spacing. Input edges are retained; shared children are not copied into tree branches. `cyclePolicy:'reject'` rejects cycles. `condense` discloses cyclic groups in the output. The graph remains cyclic; layout does not claim to turn it into a DAG.

Force layout has seeded stable-ID initial positions, pairwise repulsion, springs, damping and fixed iteration counts. The browser calls `step(6)` from a work queue; chunk size does not change the result. Radial layout arranges ranks into rings, with optional depth per rank. Neither heuristic guarantees a crossing-free or overlap-free result. Exact pins can overlap or conflict with rank direction; warnings preserve that fact instead of moving them silently.

```typescript
const job = new GraphLayoutJob(graph, {algorithm:'force',dimensions:3,seed:42});
// The host schedules work slices and continues receiving input between them.
function workSlice() {
  if (job.step(6)) commitLayout(job.result());
  else scheduleWork(workSlice);
}
```

`layoutGraph` is the synchronous convenience path for small graphs or a worker/CLI. `examples/atelier_layout.mjs` emits the full JSON layout. Applications in Python/Go/Rust can explicitly consume that preprocessing result, or port the solver with its conformance tests. That is not a claim that the solver already exists natively in all languages.

Graph IDs are semantic identity. Numeric hit IDs in a composed frame are rendering routes, not persistent graph identifiers; use the frame's current ID mapping. Discard stale scene interactions when replacing a graph.

## Camera and travel

`orbit(yawDelta,pitchDelta)` moves the eye around a fixed target. `look(...)` turns the view while retaining the eye position. `pan(right,up,forward)` translates both eye and target in the current camera basis. `dolly(factor)` changes target distance; it is distinct from translating the entire rig. Angles use degrees, coordinates use world units. `frameGraph()` fits graph bounds.

`projector(columns,rows)` captures a pure transform for a whole frame, avoiding repeated trigonometry per cell. Rebuild that projection after moving the camera. A 2:1 cell aspect is used; actual terminal font geometry may differ. This is perspective projection into terminal cells, not GPU pixels.

Starfield travel heading/elevation and signed velocity are separate from view angles. `setVelocity(-12)` flies backward along the travel vector. `aimTravel()` copies the current look direction once. Looking elsewhere does not automatically steer. Rate changes integrate from the current position. Changing a rate after seeking backward explicitly forks future rate edits; retained history is bounded. Settings import restarts at time zero and does not restore an entire flight recording.

## Text choreography

`sampleText(text,'show'|'hide',ageMs,options)` does not mutate text or read time. It returns a pose for each scalar. `textDuration` provides the exact completion bound, including delay, batching, stagger and per-glyph duration variation. Show ends at the original character and column with full opacity; hide ends at zero opacity. The source string remains available for plain-text access.

The 18 effects are in `TEXT_EFFECTS`: instant, fade, rain, scramble, flipboard, sweep-left/right, lift, fall, marquee, iris, constellation, prism-weave, ink-tide, comet-stitch, orbit, fold and zipper. Every effect accepts show and hide. Examples of exit behavior include falling down, scrambled display substitution fading to blank, a marquee leaving the field, and reverse ribbon/orbital separation.

`TextPlayer.show(time)` and `.hide(time)` capture their current poses before retargeting. `.configure(patch,time)` also captures before changing an effect; this avoids a snap when switching a rain arrival into a flipboard exit. Configure without a timestamp only when intentionally replacing a fresh/nonrunning sampler's settings. Duration changes restart the newly targeted segment from the current visual pose, not its old time origin.

`durationMs` is per glyph; `staggerMs` separates batches of `batchSize` characters. `speedJitter` controls deterministic duration variation. `randomOrder` and `reverseOrder` change start ordering. `spreadColumns`, `travelRows`, `drift`, `turns`, `trailLength` and `hueSpread` shape motion. `alphabet`/`cycleHz` control scramble and flipboard. Not every parameter affects every effect; for example, fade has no spatial path. All accepted values are documented in `CONTROLS.md` and `atelier.schema.json`.

This is a one-cell scalar display system, not general grapheme shaping. Unsupported wide/combining/control glyphs display as `?`; original text is retained. Fonts and ambiguous character widths remain terminal-dependent. No font files are distributed.

## Weather

`sampleBurst({id,x,y,atMs,kind},nowMs,options)` returns abstract points, segments and glows. Screen X is right and Y is down. Time uses milliseconds. Horizontal/radial distances use cell widths; embers' `rise` and `gravity` use rows/s and rows/s². The renderer compensates circular distances for the cell aspect.

Nova consists of a hot short-lived core, radial spokes and ballistic-looking ejecta trails; the optional shockwave is secondary. Sparks have several jittered electrical branches and forks, updated at an explicit logical cadence. Embers have upward initial velocity plus downward gravity, lateral drag/turbulence and seeded glitter. Increasing gravity or lowering rise makes their return earlier. Rain/snow retain distinct downward paths. Lifetimes and colors are display effects, not physical plasma simulation.

The model retains at most 128 weather events; the renderer evaluates the newest 16 active events. `reducedMotion` suppresses this layer without affecting input. This is a deliberate render budget, not data loss in an application event log. Applications needing durable events must own that log separately.

## Windows

`WindowManager.add` gives a stable window ID. Minimize and close retain the window; `tasks()` exposes it for a recovery dock. `restore(id,time)` also unfolds and restores opacity, so rolled-up or nearly invisible surfaces have a one-click recovery path. `show`, `hide`, `action` and `toggleRoll` take explicit time. Visibility, opacity, maximize and body roll each have their own reversible tween. Changing direction starts at the current sampled value. A different geometry effect selected during motion can alter its path; finish/retarget a window intentionally when changing the effect family.

Window properties are local cell X/Y, source width/height, world depth and independent yaw/pitch/roll. A separate workspace camera views the planes. 22 motion fields and 9 masks are exposed. Genie motion bends and travels toward the corresponding dock slot. Custom polygons accept 3..32 normalized vertices, reject self-intersections/zero area and can be concave.

Tool strips use 6×2 source-cell pads by default, configurable from 5..10 columns and 2..4 rows. The minimum 30-cell source width may clip very wide custom tool strips; use a larger source window when selecting maximum pad sizes. Perspective shrinks a far window's cell pads along with its texture. Named companion controls and the dock remain full-sized, even when a surface is faded or far away. mac/windows/gnome/custom refer to arrangements, not OS-native implementations. Custom order, side, glyphs and four RGB tool colors are editable.

Nonrectangular masks apply to the body; the tool strip deliberately floats as a full-width recovery/control surface. Source content can clip at mask boundaries. Choose appropriate padding or a readable rectangular content plane for important data. The current renderer uses painter ordering, not a per-fragment depth buffer for intersecting window planes. It does not promise correct solid-object occlusion for intersecting planes.

### Supply your application's window body

`renderer.setWindowPainter(windowId, painter)` receives a fresh body `StudioFrame`, explicit time, and window metadata. Paint that frame using your own data or `engine.paint`, without owning a terminal. Its geometry cannot be resized by the callback. Native cell data is copied before projection, so retaining and modifying the callback's body later does not mutate a previously returned frame. Pass `null` to remove the painter.

Use custom hit IDs >=100000, dispatch those in the host, then call `activateAtelier` for built-in IDs. The same mask, opacity and 3D transformation applies to your body's glyphs and hit regions. `examples/atelier_embed.mjs` demonstrates application data and a clickable native progress primitive.

## Visual settings

`exportAtelierSettings(model)` excludes drafts and transcripts. It includes camera, material, typography, particles, graph/layout, selected window and all window positions/visibility intent. `loadAtelierSettings(value)` validates an independent model before returning it. Replace the host's model only on success. The gallery preserves its local draft, notes and editor buffers through `preserveLocalContent(previous)` during this settings replacement. It starts a fresh motion timeline and settled window intent, not a historical session. Imported force layouts are bounded synchronous work; large imports belong in a worker.

## Existing framework and language integration

Keep Ratatui/Textual/Bubble Tea/Ink or another framework as the sole owner of input, focus and terminal output. Copy canonical `[glyph, foregroundRGB, backgroundRGB, hitID]` cells into the host buffer. Do not run a second ANSI writer inside an embedded widget. Framework adapters are not complete products in this source SDK. The native C APIs and prior language binding examples remain unchanged; new orchestration APIs are TypeScript and must not be represented as native Rust/Python/Go implementations.
