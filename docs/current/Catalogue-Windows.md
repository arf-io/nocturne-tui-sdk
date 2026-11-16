# Window transition components

43 identities with the native contract `WindowTransition`. An identity is the value of the `effect` field of `window`, `window-action`. Back to the [catalogue](Catalogue.md).

Each default and domain comes from the command guidance, from values the engine reads back, or from commands the engine accepts and refuses. The Basis column says which.

An observed default is a value the engine reads back identically in two scenes that differ in seed and viewport size. A default applied when omitted is the value the engine uses when the field is left out: the command without the field and the same command naming the value leave identical documents. A new-run or new-window default is what a new resource receives. Editing an existing one without the field keeps its current value for `window.chrome`. A required parameter is refused when omitted. A parameter refused when omitted under a condition is required whenever the condition in its Default column holds. An observed domain is the range the engine accepts: it accepts the edge values and refuses values just beyond them. A file and line in the Basis column point to the native statement that applies the default or checks the domain.

## Parameters of window

| Parameter | Type | Default | Domain | Basis |
|---|---|---|---|---|
| `alpha` | number \| undefined | New-window default: 0.8 | 0..1 | guidance |
| `anchorX` | number \| undefined | New-window default: 0.5,1.15 | −2..3 | guidance |
| `anchorY` | number \| undefined | New-window default: 0.5,1.15 | −2..3 | guidance |
| `bend` | number \| undefined | New-window default: 9 | −40..40 | guidance |
| `border` | Border \| undefined | New-window default: `rounded` | `none`, `rounded`, `square`, `double`, `heavy` | guidance |
| `chrome` | WindowSourceChrome \| undefined | Source presentation default: "mac" | One of "custom", "mac", "windows", "gnome" | default: applied when omitted (`window_source_presentation.c:17`); domain: declared type |
| `chromeSize` | number \| undefined | New-window default: 3 | Integer1..5 | guidance |
| `controlHeight` | number \| undefined | Source presentation default: 3 | Observed: integers from 3 to 6 | default: applied when omitted (`window_source_presentation.c:19`); domain: refusal probes |
| `controlWidth` | number \| undefined | Source presentation default: 10 | Observed: integers from 5 to 15 | default: applied when omitted (`window_source_presentation.c:18`); domain: refusal probes |
| `customGlyphs` | string \| undefined | Source presentation default: "−,□,◇,×" | Four comma-separated single Unicode scalars, none from U+0000 to U+001F or U+007F to U+009F; the comma separates them and is never one of them | default: applied when omitted (`window_source_presentation.c:25`, `window_source_presentation.c:28`); domain: accepted and refused commands (`window_presentation.c:54`, `window_presentation.c:60`, `window_source_presentation.c:9`) |
| `customOrder` | string \| undefined | Source presentation default: "minimize,maximize,background,close" | Four comma-separated names: close, minimize, maximize and background, each exactly once | default: applied when omitted (`window_source_presentation.c:21`, `window_source_presentation.c:24`); domain: accepted and refused commands (`window_presentation.c:45`, `window_source_presentation.c:51`) |
| `customSide` | "left" \| "right" \| undefined | Source presentation default: "right" | One of "left", "right" | default: applied when omitted (`window_source_presentation.c:20`); domain: declared type |
| `depthFade` | number \| undefined | Source presentation default: 0.008 | Observed: numbers from 0 to 0.08 | default: applied when omitted (`window_source_presentation.c:16`); domain: refusal probes |
| `durationMs` | number \| undefined | New-window default: 600 | 0..60000 milliseconds | guidance |
| `effect` | string \| undefined | New-window default: `window-transition/glass-dissolve` | Current WindowTransition identity | guidance |
| `fadeEndRatio` | number \| undefined | New-window default: 1,0.22 | Start0.001..8, end0..8; end strictly below start | guidance |
| `fadeStartRatio` | number \| undefined | New-window default: 1,0.22 | Start0.001..8, end0..8; end strictly below start | guidance |
| `folds` | number \| undefined | New-window default: 6 | Integer1..32 | guidance |
| `group` | number \| undefined | New-window default: 0 | Integer0..65535 | guidance |
| `height` | number \| undefined | New-window default: 28,22 | 1..2147483647; world geometry dimensions | guidance |
| `id` | number | required | Observed: integers from 1 to 65535 | default: refused when omitted (`commands.c:1979`); domain: accepted and refused commands (`commands.c:1978`) |
| `material` | number \| undefined | New-window default: 2 | Integer0..15 | guidance |
| `maxColumns` | number \| undefined | New-window default: 30,78 | Integers8..2147483647; ordered; minimum strictly greater than `2*(padding+1)` | guidance |
| `meshColumns` | number \| undefined | New-window default: 12 | Integer2..32 | guidance |
| `meshRows` | number \| undefined | New-window default: 8 | Integer2..24 | guidance |
| `minColumns` | number \| undefined | New-window default: 30,78 | Integers8..2147483647; ordered; minimum strictly greater than `2*(padding+1)` | guidance |
| `overshoot` | number \| undefined | New-window default: 0.18 | 0..1 | guidance |
| `padding` | number \| undefined | New-window default: 1 | Integer0..8 | guidance |
| `pitch` | number \| undefined | New-window default: 0 | Each −36000..36000 degrees | guidance |
| `polygon` | readonly (readonly [number, number])[] \| undefined | New-window default: none; shape "polygon" requires vertices | 3 to 32 [u, v] points, each coordinate from 0 to 1, whose shoelace sum (twice the net signed area) exceeds 1e-8 in magnitude, so lobes of opposite winding cancel | default: refused when omitted under a condition (`commands.c:1984`, `commands.c:2029`); domain: accepted and refused commands (`commands.c:2018`, `commands.c:2021`, `commands.c:2023`, `commands.c:2026`, `commands.c:2027`) |
| `position` | Vector3 \| undefined | New-window default: Slot-dependent arrangement | XYZ scene units, each −16000..16000 | guidance |
| `roll` | number \| undefined | New-window default: 0 | Each −36000..36000 degrees | guidance |
| `scatter` | number \| undefined | New-window default: 32 | 0..100 | guidance |
| `seed` | number \| undefined | New-window default: Scene seed | uint32 | guidance |
| `shape` | string \| undefined | New-window default: `rectangle` | Rectangle, rounded, ellipse, hexagon, diamond, capsule, ticket, squircle, petal, wave, cloud or polygon | guidance |
| `sourceGeometry` | boolean \| undefined | New-window default: `false` | Boolean; opts into preserved source geometry | guidance |
| `sourcePresentation` | boolean \| undefined | Observed default: false | Boolean: true or false | default: engine readback; domain: declared type |
| `text` | string \| undefined | New-window default: Empty | Up to 2048 Unicode scalars | guidance |
| `title` | string \| undefined | New-window default: Empty | Up to 160 Unicode scalars | guidance |
| `width` | number \| undefined | New-window default: 28,22 | 1..2147483647; world geometry dimensions | guidance |
| `yaw` | number \| undefined | New-window default: 0 | Each −36000..36000 degrees | guidance |

## Parameters of window-action

| Parameter | Type | Default | Domain | Basis |
|---|---|---|---|---|
| `action` | WindowAction | Applied when omitted: "restore" | One of "background", "rotate", "move", "minimize", "maximize", "fade", "close", "restore", "summon", "visit", "roll-up", "roll-down", "read", "scroll", "page-next", "page-prev" | default: applied when omitted (`commands.c:2059`, `commands.c:2060`); domain: declared type |
| `durationMs` | number \| undefined | Applied when omitted: The window's current durationMs, unchanged | Observed: numbers from 0 to 60000 | default: applied when omitted (`commands.c:2070`); domain: refusal probes |
| `dx` | number \| undefined | Applied when omitted: 0 | Observed with action "move": numbers from -1000 to 1000 | default: applied when omitted (`commands.c:2080`); domain: refusal probes |
| `dy` | number \| undefined | Applied when omitted: 0 | Observed with action "move": numbers from -1000 to 1000 | default: applied when omitted (`commands.c:2080`); domain: refusal probes |
| `effect` | string \| undefined | Applied when omitted: The window's current effect, unchanged | A WindowTransition identity from the catalogue, 43 identities | default: applied when omitted (`commands.c:2069`); domain: catalogue |
| `forward` | number \| undefined | Applied when omitted: 0 | Observed with action "move": numbers from -1000 to 1000 | default: applied when omitted (`commands.c:2080`); domain: refusal probes |
| `group` | number \| undefined | Applied when omitted: The window's current group, unchanged | Observed: integers from 0 to 65535 | default: applied when omitted (`commands.c:2071`); domain: refusal probes |
| `id` | number | Applied when omitted: The selected window, as info reports selectedWindow | Integers from 1 to 65535 that name an existing window | default: applied when omitted (`commands.c:2054`); domain: accepted and refused commands (`commands.c:2055`, `commands.c:2057`) |
| `pitch` | number \| undefined | Applied when omitted: 0 | Observed with action "rotate": numbers from -3600 to 3600 | default: applied when omitted (`commands.c:2090`); domain: refusal probes |
| `roll` | number \| undefined | Applied when omitted: 0 | Observed with action "rotate": numbers from -3600 to 3600 | default: applied when omitted (`commands.c:2090`); domain: refusal probes |
| `rows` | number \| undefined | Applied when omitted: 0 | Observed with action "scroll": integers from -2048 to 2048 | default: applied when omitted (`commands.c:2065`); domain: refusal probes |
| `yaw` | number \| undefined | Applied when omitted: 0 | Observed with action "rotate": numbers from -3600 to 3600 | default: applied when omitted (`commands.c:2090`); domain: refusal probes |

## Components

### window-transition/glass-dissolve

| Field | Value |
|---|---|
| Name | Glass Dissolve |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 0 |
| Source identity | `window/kinetic/fade` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/glass-dissolve"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/glass-dissolve"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/glass-dissolve","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/glass-dissolve"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/glass-dissolve","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/glass-dissolve","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/elastic-pop

| Field | Value |
|---|---|
| Name | Elastic Pop |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 1 |
| Source identity | `window/kinetic/bounce` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/elastic-pop"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/elastic-pop"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/elastic-pop","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/elastic-pop"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/elastic-pop","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/elastic-pop","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/lamp-genie

| Field | Value |
|---|---|
| Name | Lamp Genie |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 2 |
| Source identity | `window/kinetic/genie` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/lamp-genie"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/lamp-genie"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/lamp-genie","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/lamp-genie"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/lamp-genie","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/lamp-genie","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/scroll-up

| Field | Value |
|---|---|
| Name | Scroll Up |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 3 |
| Source identity | `window/kinetic/roll-up` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/scroll-up"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/scroll-up"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/scroll-up","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/scroll-up"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/scroll-up","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/scroll-up","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/scroll-down

| Field | Value |
|---|---|
| Name | Scroll Down |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 4 |
| Source identity | `window/kinetic/roll-down` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/scroll-down"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/scroll-down"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/scroll-down","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/scroll-down"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/scroll-down","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/scroll-down","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/rail-left

| Field | Value |
|---|---|
| Name | Rail Left |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 5 |
| Source identity | `window/kinetic/drawer-left` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/rail-left"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/rail-left"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/rail-left","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/rail-left"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/rail-left","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/rail-left","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/rail-right

| Field | Value |
|---|---|
| Name | Rail Right |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 6 |
| Source identity | `window/kinetic/drawer-right` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/rail-right"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/rail-right"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/rail-right","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/rail-right"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/rail-right","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/rail-right","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/rail-top

| Field | Value |
|---|---|
| Name | Rail Top |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 7 |
| Source identity | `window/kinetic/drawer-top` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/rail-top"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/rail-top"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/rail-top","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/rail-top"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/rail-top","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/rail-top","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/rail-bottom

| Field | Value |
|---|---|
| Name | Rail Bottom |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 8 |
| Source identity | `window/kinetic/drawer-bottom` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/rail-bottom"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/rail-bottom"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/rail-bottom","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/rail-bottom"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/rail-bottom","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/rail-bottom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/center-aperture

| Field | Value |
|---|---|
| Name | Center Aperture |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 9 |
| Source identity | `window/kinetic/center` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/center-aperture"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/center-aperture"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/center-aperture","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/center-aperture"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/center-aperture","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/center-aperture","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/northwest-aperture

| Field | Value |
|---|---|
| Name | Northwest Aperture |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 10 |
| Source identity | `window/kinetic/top-left` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/northwest-aperture"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/northwest-aperture"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/northwest-aperture","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/northwest-aperture"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/northwest-aperture","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/northwest-aperture","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/northeast-aperture

| Field | Value |
|---|---|
| Name | Northeast Aperture |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 11 |
| Source identity | `window/kinetic/top-right` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/northeast-aperture"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/northeast-aperture"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/northeast-aperture","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/northeast-aperture"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/northeast-aperture","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/northeast-aperture","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/southwest-aperture

| Field | Value |
|---|---|
| Name | Southwest Aperture |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 12 |
| Source identity | `window/kinetic/bottom-left` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/southwest-aperture"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/southwest-aperture"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/southwest-aperture","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/southwest-aperture"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/southwest-aperture","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/southwest-aperture","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/southeast-aperture

| Field | Value |
|---|---|
| Name | Southeast Aperture |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 13 |
| Source identity | `window/kinetic/bottom-right` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/southeast-aperture"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/southeast-aperture"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/southeast-aperture","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/southeast-aperture"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/southeast-aperture","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/southeast-aperture","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/circular-iris

| Field | Value |
|---|---|
| Name | Circular Iris |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 14 |
| Source identity | `window/kinetic/iris` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/circular-iris"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/circular-iris"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/circular-iris","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/circular-iris"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/circular-iris","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/circular-iris","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/shard-burst

| Field | Value |
|---|---|
| Name | Shard Burst |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 15 |
| Source identity | `window/kinetic/explosion` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/shard-burst"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/shard-burst"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/shard-burst","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/shard-burst"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/shard-burst","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/shard-burst","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/concertina

| Field | Value |
|---|---|
| Name | Concertina |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 16 |
| Source identity | `window/kinetic/accordion` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/concertina"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/concertina"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/concertina","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/concertina"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/concertina","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/concertina","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/portal-fold

| Field | Value |
|---|---|
| Name | Portal Fold |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 17 |
| Source identity | `window/kinetic/portal` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/portal-fold"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/portal-fold"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/portal-fold","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/portal-fold"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/portal-fold","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/portal-fold","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/orbital-bloom

| Field | Value |
|---|---|
| Name | Orbital Bloom |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 18 |
| Source identity | `window/kinetic/orbital-bloom` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/orbital-bloom"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/orbital-bloom"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/orbital-bloom","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/orbital-bloom"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/orbital-bloom","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/orbital-bloom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/venetian

| Field | Value |
|---|---|
| Name | Venetian |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 19 |
| Source identity | `window/kinetic/venetian` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/venetian"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/venetian"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/venetian","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/venetian"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/venetian","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/venetian","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/ribbon-unfurl

| Field | Value |
|---|---|
| Name | Ribbon Unfurl |
| Contract | `WindowTransition` |
| Profile | 0 |
| Algorithm | 20 |
| Source identity | `window/kinetic/ribbon-unfurl` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-unfurl"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/ribbon-unfurl"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-unfurl","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/ribbon-unfurl"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-unfurl","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-unfurl","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/silk-dissolve

| Field | Value |
|---|---|
| Name | Silk Dissolve |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 0 |
| Source identity | `window/atelier/fade` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/silk-dissolve"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/silk-dissolve"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/silk-dissolve","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/silk-dissolve"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/silk-dissolve","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/silk-dissolve","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/center-bloom

| Field | Value |
|---|---|
| Name | Center Bloom |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 9 |
| Source identity | `window/atelier/expand-center` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/center-bloom"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/center-bloom"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/center-bloom","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/center-bloom"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/center-bloom","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/center-bloom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/northwest-bloom

| Field | Value |
|---|---|
| Name | Northwest Bloom |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 10 |
| Source identity | `window/atelier/expand-nw` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/northwest-bloom"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/northwest-bloom"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/northwest-bloom","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/northwest-bloom"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/northwest-bloom","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/northwest-bloom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/northeast-bloom

| Field | Value |
|---|---|
| Name | Northeast Bloom |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 11 |
| Source identity | `window/atelier/expand-ne` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/northeast-bloom"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/northeast-bloom"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/northeast-bloom","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/northeast-bloom"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/northeast-bloom","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/northeast-bloom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/southwest-bloom

| Field | Value |
|---|---|
| Name | Southwest Bloom |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 12 |
| Source identity | `window/atelier/expand-sw` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/southwest-bloom"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/southwest-bloom"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/southwest-bloom","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/southwest-bloom"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/southwest-bloom","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/southwest-bloom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/southeast-bloom

| Field | Value |
|---|---|
| Name | Southeast Bloom |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 13 |
| Source identity | `window/atelier/expand-se` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/southeast-bloom"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/southeast-bloom"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/southeast-bloom","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/southeast-bloom"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/southeast-bloom","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/southeast-bloom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/circle-bloom

| Field | Value |
|---|---|
| Name | Circle Bloom |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 14 |
| Source identity | `window/atelier/circle` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/circle-bloom"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/circle-bloom"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/circle-bloom","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/circle-bloom"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/circle-bloom","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/circle-bloom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/reel-up

| Field | Value |
|---|---|
| Name | Reel Up |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 3 |
| Source identity | `window/atelier/roll-up` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/reel-up"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/reel-up"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/reel-up","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/reel-up"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/reel-up","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/reel-up","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/reel-down

| Field | Value |
|---|---|
| Name | Reel Down |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 4 |
| Source identity | `window/atelier/roll-down` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/reel-down"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/reel-down"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/reel-down","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/reel-down"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/reel-down","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/reel-down","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/pocket-left

| Field | Value |
|---|---|
| Name | Pocket Left |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 5 |
| Source identity | `window/atelier/drawer-left` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-left"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/pocket-left"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-left","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/pocket-left"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-left","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-left","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/pocket-right

| Field | Value |
|---|---|
| Name | Pocket Right |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 6 |
| Source identity | `window/atelier/drawer-right` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-right"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/pocket-right"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-right","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/pocket-right"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-right","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-right","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/pocket-top

| Field | Value |
|---|---|
| Name | Pocket Top |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 7 |
| Source identity | `window/atelier/drawer-top` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-top"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/pocket-top"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-top","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/pocket-top"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-top","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-top","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/pocket-bottom

| Field | Value |
|---|---|
| Name | Pocket Bottom |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 8 |
| Source identity | `window/atelier/drawer-bottom` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-bottom"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/pocket-bottom"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-bottom","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/pocket-bottom"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-bottom","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/pocket-bottom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/spring-pop

| Field | Value |
|---|---|
| Name | Spring Pop |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 1 |
| Source identity | `window/atelier/bounce` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/spring-pop"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/spring-pop"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/spring-pop","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/spring-pop"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/spring-pop","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/spring-pop","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/ribbon-genie

| Field | Value |
|---|---|
| Name | Ribbon Genie |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 2 |
| Source identity | `window/atelier/genie` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-genie"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/ribbon-genie"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-genie","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/ribbon-genie"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-genie","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-genie","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/fragment-scatter

| Field | Value |
|---|---|
| Name | Fragment Scatter |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 15 |
| Source identity | `window/atelier/explode` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/fragment-scatter"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/fragment-scatter"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/fragment-scatter","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/fragment-scatter"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/fragment-scatter","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/fragment-scatter","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/accordion-fold

| Field | Value |
|---|---|
| Name | Accordion Fold |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 16 |
| Source identity | `window/atelier/accordion` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/accordion-fold"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/accordion-fold"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/accordion-fold","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/accordion-fold"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/accordion-fold","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/accordion-fold","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/origami

| Field | Value |
|---|---|
| Name | Origami |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 21 |
| Source identity | `window/atelier/origami` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/origami"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/origami"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/origami","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/origami"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/origami","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/origami","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/vortex-fold

| Field | Value |
|---|---|
| Name | Vortex Fold |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 22 |
| Source identity | `window/atelier/vortex` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/vortex-fold"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/vortex-fold"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/vortex-fold","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/vortex-fold"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/vortex-fold","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/vortex-fold","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/ribbon-unspool

| Field | Value |
|---|---|
| Name | Ribbon Unspool |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 23 |
| Source identity | `window/atelier/ribbon-unspool` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-unspool"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/ribbon-unspool"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-unspool","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/ribbon-unspool"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-unspool","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/ribbon-unspool","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/petal-bloom

| Field | Value |
|---|---|
| Name | Petal Bloom |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 24 |
| Source identity | `window/atelier/petal-bloom` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/petal-bloom"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/petal-bloom"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/petal-bloom","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/petal-bloom"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/petal-bloom","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/petal-bloom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### window-transition/gravity-well

| Field | Value |
|---|---|
| Name | Gravity Well |
| Contract | `WindowTransition` |
| Profile | 1 |
| Algorithm | 25 |
| Source identity | `window/atelier/gravity-well` |
| Commands | [`window`](#parameters-of-window), [`window-action`](#parameters-of-window-action) |

Accepted by the native library:

**Minimal window command**

```json
{"op":"window","id":1,"effect":"window-transition/gravity-well"}
```

**Minimal window-action command**

```json
[{"op":"window","id":1},{"op":"window-action","id":1,"action":"minimize","effect":"window-transition/gravity-well"}]
```

**Value at the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/gravity-well","durationMs":60000}
```

Refused by the native library:

**Identity used on the emitter command of another family**

```json
{"op":"emitter","id":1,"effect":"window-transition/gravity-well"}
```

Diagnostic: `Unknown native particle effect`

**Value outside the finite choices of border**

```json
{"op":"window","id":1,"effect":"window-transition/gravity-well","border":"unlisted"}
```

Diagnostic: `Invalid choice: border`

**Value above the stated maximum of durationMs**

```json
{"op":"window","id":1,"effect":"window-transition/gravity-well","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`
