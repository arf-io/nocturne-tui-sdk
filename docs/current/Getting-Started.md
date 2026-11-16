# Getting started

## Choose a host

Use C for explicit allocation and integration with an existing native render loop. Python, Go and Rust own native context and scratch allocations for you. TypeScript owns the same allocations inside an import-free WebAssembly module. The core opens no files, clocks, devices, sockets or threads; the application owns those services.

The SDK contains `native/include/nocturne_native.h`, `native/dist`, the four binding directories and source. Load the library and bindings from the same SDK. Query runtime metadata for the ABI and snapshot writer rather than embedding a snapshot byte count.

## Build a first screen

This command transaction resizes the viewport, creates a panel, writes text and adds a progress meter. Coordinates use terminal cells. The viewport is 80 columns by 24 rows.

```json
{"op":"batch","commands":[{"op":"resize","width":80,"height":24},{"op":"widget","id":1,"kind":"box","x":2,"y":2,"width":76,"height":18,"border":"rounded","alpha":0.25},{"op":"widget","id":2,"kind":"text","x":5,"y":4,"width":65,"height":2,"text":"Nocturne / activity"},{"op":"widget","id":3,"kind":"progress","x":5,"y":9,"width":58,"height":3,"value":0.65,"border":"rounded"}]}
```

Submit it once, render, then copy the frame into your terminal or canvas. Keep the scene alive between frames. Update the progress value with a partial `widget` command using the same identity; do not reset the scene on each paint.

![Progress meter](images/widget-progress-default.png)

## Advance and paint

The host supplies monotonically increasing integer microseconds. A time command can return catch-up pending when its step budget is exhausted. Continue the same target in later work until complete. Binding `advanceTo` or `advance_to` helpers drain the target synchronously; use explicit time commands when your UI must yield between budgets. Render is pure with respect to authored state and simulation. Redrawing never advances an animation.

## Handle failure

A rejected command leaves authoritative scene state unchanged. Report the native error to the user, retain their draft, and let them correct it. A successful transaction may still expose capacity or saturation diagnostics; inspect those explicitly when exact emission counts matter. Copy borrowed C data before another context call. Close binding-owned contexts when the application stops.

## Save user work

A project describes authored elements, assets and interactions; a snapshot captures an exact runtime checkpoint. Keep both when the user needs editable design and resume. Import into a trial scene and adopt only after validation. [Composition](Composition.md) describes the shared project format and generated applications.
