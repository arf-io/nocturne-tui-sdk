# Pearl Fleet / Volume III

**Implemented user experience:** an expert can monitor a data-rich animated fleet, select an agent, watch its tile expand into a maximized workspace, and read arriving text that dissolves into view and softens near the top of the conversation.

Open `Nocturne-Pearl-Fleet.html`, or run `node examples/fleet_terminal.mjs`. The default source is explicitly synthetic. Nothing connects to providers or executes a shell command.

## Interaction sequence

The fleet deck shows eight agents, each with role, status, throughput, latency, context utilization, queue depth and a braille history. The lower Pearl Signal envelope combines throughput, latency and context on declared scales. A party-line panel shows the most recent message per visible agent. Dense mode switches the deck to a compact metric matrix.

Click an agent tab or card, or navigate with Tab/arrows and press Enter. Its rectangle expands from the visible tile into the full application workspace. The global header and agent tab strip remain available. Escape returns to the deck. Clicking another agent opens that workspace without discarding the previous agent's draft or transcript position.

The maximized workspace contains the conversation, agent-local composer, scope, large throughput number and compact operational metrics. Select a trace to inspect the corresponding sample. Click a message to restore full emphasis. The browser also exposes ordinary agent buttons and an unfaded, selectable transcript; these are companion interaction paths, not a claim of comprehensive screen-reader support.

## Independent animation treatments

| Setting | Default | Meaning |
|---|---:|---|
| `expandMs` | 560 ms | Smoothstep rectangle expansion/collapse; 0 disables. |
| `arrivalMs` | 520 ms | Smoothstep fade of each newly delivered text run; 0 disables. |
| `horizonRows` | 6 rows | Spatial fade near the top of the transcript only. |
| `horizonMinimum` | 760 / 1000 | 76% of nominal foreground blend at the top row. |
| `backgroundBrightness` | 110 / 1000 | Decorative field light; independent of ink. |
| `scopeColorSpeed` | 8 | Color travel on the surrounding rules; not fake movement of metric samples. |
| `dense` | false | Compact data matrix in the overview. |
| `readMode` | false | Full ink and static decoration. |
| `reducedMotion` | false | Immediate geometry/text appearance, static decorative field. |

These are explicit values, not frame counts. The default 76% is a compositing coefficient, not a calibrated contrast ratio or physical luminance. The top fade never changes, trims or deletes stored text. Warnings, errors, explicitly selected messages and reading mode bypass the top fade. The composer and header do not fade with scroll position.

Arrival opacity is multiplied by the spatial horizon opacity. Incoming text is in the model and semantic transcript immediately; only its visual ink fades. Existing text does not restart its fade when another delivery chunk arrives. Ordinary chunk boundaries retain their original presentation timestamps. Above 256 runs per message, old runs coalesce with their earliest timestamp to bound memory.

## Two clocks, not an animation gate

Hosts commit input/data synchronously and paint using the current decorative time. A separate deadline targets 30 motion frames per second. The browser demo source produces updates every 80 ms; external input has no such artificial cadence. Native terminal output uses dirty runs and coalesces only superseded pending frames when stdout is blocked; it does not discard authoritative events to maintain a frame rate.

A pause holds decorative time but still shows incoming messages, metrics, selection and drafts. Text revealed during a pause/read policy stays revealed after resuming; it cannot flash back to invisible. Pausing settles an unfinished workspace expansion at its target.

The received event `atMs` is the source timestamp. `motionMs` is the explicitly supplied presentation timestamp. A producer's clock is never used blindly to decide whether received text is visible.

## Reading history

Page Up, Page Down and mouse wheel move by rows. New content does not drag a historical viewport back to the bottom; a new-message count appears. End explicitly resumes live tail. Draft, history offset and clicked-message emphasis are stored per agent.

The retained model is bounded: 32 agents, 256 messages per agent, 16,384 Unicode scalars per message, 96 metric samples per agent, 8,192 recorded inbound events, and 64 pending outbound commands. Drop counts are exposed for messages/events; applications requiring durable full history must persist it upstream. The UI is not an archival database.

## Layer and screen behavior

The deck remains active under the expanding workspace. The workspace's text is composed from fresh state on every paint, including during a resize or transition. Interrupted expansion reverses from its current rectangle. Layout uses whole terminal cells, so geometric movement is cell-stepped, not an arbitrary-pixel browser transformation.

Large screens remain within the shared renderer's 512-node/32,768-text-scalar budget. Mature adjacent text runs merge by effective opacity. Extreme fragmentation falls back to one opacity per line without dropping characters. At very large viewports the rendered transcript window is capped by its 24,000-scalar content budget; additional history remains scrollable and exportable.

The preview uses actual C/WASM cell output. Braille dots and half blocks are painted as cell geometry, other glyphs with the installed browser font. Terminal font shapes and pixel rasterization can differ. The shared canonical cell frames, not arbitrary screenshots, are the parity contract.

## Included and deliberately not claimed

Included: reusable TypeScript domain/controller/scene composer, browser host, POSIX Node terminal host, additive shared opacity helper in C/Python/Go/Rust/TypeScript, Python/Go normalized-scene readers, tests, fixtures and integration documentation. The original Studio and its materials remain present.

Not included: actual fleet-provider connections, authorization/ACK protocol, production command delivery, a full shell/editor, arbitrary remote terminal embedding, full grapheme/CJK/emoji layout, virtualized millions-of-record history, or independently published framework packages. The high-level Fleet controller is TypeScript; its visual primitives and normalized scenes use the shared core. It is not a claim of four separately implemented Fleet applications.
