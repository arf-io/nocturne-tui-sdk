# SDK contract

This document defines the shared runtime and host boundary. The shipped `native/include/nocturne_native.h` specifies C signatures, units, alias rules and return values. [Commands](Commands.md) specifies JSON operations and typed fields. Command-specific validation remains part of the implementation: a field typed as `number` does not accept arbitrary magnitudes, NaN or infinity.

## Runtime and ownership

The C11 core exposes ABI 1 through an opaque context. It performs no heap allocation, clock reads, device access, file I/O or subprocess execution. A host supplies an explicit seed, input and elapsed time. The native library and import-free WASM implement the same scene contract.

The C caller allocates `nrContextSize()` bytes with 8-byte alignment and initializes with `nrInit`. Serialize every call on one context. Returned views are borrowed until the next call; the language bindings return owned copies. Retain caller-owned prompt, model, modal and render buffers while they are bound. Follow each query's output-capacity unit and overlap rule; rows, scalars, doubles and bytes are not interchangeable. [C](C.md) describes allocation, queries and errors.

## Transactions and identity

A command is one bounded UTF-8 JSON transaction. Accepted mutations commit together; invalid commands and failed batches preserve authoritative state. Return 1 indicates catch-up pending, not completion at a requested future time. Error text and diagnostic storage may change on rejection. Text input commits independently of decorative impulse capacity, so a full effect pool does not discard an accepted edit.

Resource and semantic IDs are explicit. Material, geometry, area, field, path, widget, window, node and emitter references must resolve in the consumed scene. Preserve dependency ordering and use each resource operation's removal rules. IDs are not filesystem paths or executable strings. An event or activation transaction changes the native scene; network, clipboard and operating-system actions remain host operations.

[Composition](Composition.md) defines project normalization, resources, trial validation, replacement, insertion and generated applications. Scene commands and model uploads are separate atomic operations. To replace a complete project atomically, prepare a context or snapshot and swap it in.

## Geometry, cells and color

World axes are +X right, +Y up and +Z toward the default viewer; the default view looks along -Z. Projected world geometry and screen-cell widgets retain their separate coordinate contracts. Camera rigs, picked world anchors, independent head/body motion and input-axis mappings follow [Input and motion](Input-and-Motion.md).

A canonical cell has four little-endian unsigned 32-bit words: Unicode scalar, foreground RGB, background RGB and semantic ID. Rendering returns the current viewport's cells without advancing simulation, queued work, input state or random keys. Render scratch and diagnostics may change. A repeated render at unchanged authoritative state has unchanged cell output.

Cell, half, braille and hybrid sampling remain distinct. Braille occupancy selects one of 256 dot masks; a full mask remains eight dots over the cell background. Blending and alpha composition are separate operations. The selected color-space and material controls determine interpolation; there is no implicit bright-cell replacement for a filled braille mask. [Materials and rendering](Materials-and-Rendering.md) describes presentation and compositing.

## Time and input

The host supplies integer scene microseconds. Advancing may require multiple bounded calls; the host must inspect completion before reporting the requested time as reached. Rendering and queries do not advance time. Pausing stops scene advancement while permitting commands and editing. Explicit scenic sample clocks and rate timelines preserve phase across control changes.

Physical input follows the active owner: prompt, reader, help or modal. Authoring commands are a separate interface for changing scene data. A camera gesture does not implicitly stop scripted flight; an explicit brake does. Hosts must cancel lost pointer capture and must not replay stale drag state after an owner changes. Bindings and host adapters preserve scalar offsets, selection direction and complete text during input and restoration.

## Text, assets and capacities

Text storage uses Unicode scalars; UTF-8 command bytes and JavaScript UTF-16 offsets require conversion at their boundaries. Grapheme navigation, bidi layout, shaping and line breaking use the SDK's corresponding queries. Text content may include embedded NUL where the length-bearing API permits it. A C string length is not a substitute for an explicit scalar or byte length.

Prompt documents, modal strings, imported model records and presentation scratch can grow through caller-provided storage. Bindings allocate and retry only the precise storage-required operation. Allocation failure and integer representability remain real bounds. Memory, JSON transaction size and the number of simultaneous objects are finite. An authored prompt limit, when nonzero, is an application setting.

| Public capacity | Domain |
|---|---|
| JSON command bytes | At most 1,048,576 per transaction |
| Complete metadata page | At most 65,536 bytes; reassemble pages before UTF-8 decoding |
| Retained particles / emitters | 2,048 / 16 |
| Surfaces / float bodies | 16 / 64 |
| World windows / graph nodes | 32 / 64 |
| Fixed collision-mesh triangles | 256; separate from growable imported model records |
| Modal stack | 8 entries; title, body, context and query storage can grow |

The public `NR_MAX_TEXT` and `NR_MAX_PROMPT` constants describe fixed/inline domains used by particular APIs; they do not cap the growable prompt document. Pure bounded text and geometry queries retain their documented input limits. Use whole-document APIs for whole documents. Render-size arithmetic, snapshot length, query return types and available host memory must all remain representable.

Imported model records contain signed Q8 XYZ coordinates and packed RGB. The host retains the complete model data through upload, snapshot and export. Fonts, model decoding and asset acquisition are explicit host responsibilities; imported data does not execute code or fetch dependencies.

## Persistence

Use `nrSnapshotSizeFor(context)` and the save/load APIs; never serialize a C struct or hard-code its private size. Snapshots contain pointer-free state and owned variable payloads, with ABI/schema, length and CRC checks. Supported schema migrations validate the consumed representation before promotion; unknown schema/length pairs reject. Rejected restores preserve the current scene. CRC detects corruption and is not authentication.

A scene checkpoint does not persist browser DOM, platform pointer capture or arbitrary host closures. A project persists its declared scene, resources and activation data. The host separately restores editor selection, application state and device handles as appropriate.

## Tests and distribution

`qualify-native.sh --profile rc2` runs the build, binding, rendering, browser, export and documentation tests and writes a report of each step. The native line-coverage floor is 70 percent, measured on an instrumented library; the shipping binary is inspected separately. Packaging checks source identity, runtime identity, file membership and hashes, the documentation inputs, and that an extracted SDK builds and runs from its shipped paths. The component atlas lists the native and WASM cell hashes that match each screenshot.

Use bindings, runtime, Gallery and documentation from the same SDK. Detect optional capabilities before use.
