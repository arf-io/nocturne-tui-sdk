# Text transition components

36 identities with the native contract `TextTransition`. An identity is the value of the `effect` field of `text`. Back to the [catalogue](Catalogue.md).

Each default and domain comes from the command guidance, from values the engine reads back, or from commands the engine accepts and refuses. The Basis column says which.

An observed default is a value the engine reads back identically in two scenes that differ in seed and viewport size. A default applied when omitted is the value the engine uses when the field is left out: the command without the field and the same command naming the value leave identical documents. A new-run or new-window default is what a new resource receives. Editing an existing one without the field keeps its current value for `text.durationMs`. A required parameter is refused when omitted. A file and line in the Basis column point to the native statement that applies the default or checks the domain.

## Parameters of text

| Parameter | Type | Default | Domain | Basis |
|---|---|---|---|---|
| `alphabet` | string \| undefined | Observed default: " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" | 1–256 printable Unicode scalars for substitutions | default: engine readback; domain: guidance |
| `batchSize` | number \| undefined | New-run default: 1 | Integer 1–128 | default: applied when omitted (`commands.c:1915`); domain: guidance |
| `cycles` | number \| undefined | New-run default: 3 for profile 0, 1.5 for profile 1 | 0–50 | default: applied when omitted (`commands.c:1936`); domain: guidance |
| `delayMs` | number \| undefined | New-run default: 0 | Start delay, 0–60000 ms | default: applied when omitted (`commands.c:1900`); domain: guidance |
| `distance` | number \| undefined | New-run default: 18 for profile 0, 13 for profile 1 | 0–100 | default: applied when omitted (`commands.c:1935`); domain: guidance |
| `durationMs` | number \| undefined | New-run default: 1200 | Treatment duration, 0–60000 ms | default: applied when omitted (`commands.c:1909`); domain: guidance |
| `easing` | "back" \| Easing \| "cubic" \| "bounce" \| undefined | New-run default: "smooth" | linear, ease-in, ease-out, smooth, smoother, sine, step, cubic, back, bounce | default: applied when omitted (`commands.c:1919`, `commands.c:1968`); domain: guidance |
| `effect` | string \| undefined | New-run default: "text/ink-dissolve" | Exact text-family catalogue identity; unknown/wrong-family names reject | default: applied when omitted (`commands.c:1905`); domain: guidance |
| `hueSpread` | number \| undefined | New-run default: 10 for profile 0, 110 for profile 1 | −360–360 degrees | default: applied when omitted (`commands.c:1937`); domain: guidance |
| `id` | number | required | Required integer 1–65535; caller-reserved text resource | default: refused when omitted (`commands.c:1893`); domain: guidance |
| `jitterMs` | number \| undefined | New-run default: 360 for profile 0, 0 for profile 1 | Authored progression jitter, 0–10000 ms | default: applied when omitted (`commands.c:1934`); domain: guidance |
| `local` | boolean \| undefined | Observed default: false | Boolean local presentation option | default: engine readback; domain: guidance |
| `material` | number \| undefined | New-run default: 2; 15 for a new run with phaseModel "source-paint" | Integer 0–15 | default: applied when omitted (`commands.c:1918`, `commands.c:1930`); domain: guidance |
| `overshoot` | number \| undefined | New-run default: 0.2 for profile 0, 1.2 for profile 1 | 0–3 | default: applied when omitted (`commands.c:1936`); domain: guidance |
| `phase` | "show" \| "hide" \| undefined | Observed default: "show" | show or hide | default: engine readback; domain: guidance |
| `phaseModel` | "source" \| "reverse-show" \| "source-paint" \| undefined | Observed default: "reverse-show" | One of "source", "reverse-show", "source-paint" | default: engine readback; domain: declared type |
| `randomOrder` | boolean \| undefined | New-run default: false | Boolean seeded random progression order | default: applied when omitted (`commands.c:1900`); domain: guidance |
| `reverseOrder` | boolean \| undefined | New-run default: false | Boolean reverse progression order | default: applied when omitted (`commands.c:1900`); domain: guidance |
| `scatter` | number \| undefined | New-run default: 5 for profile 0, 8 for profile 1 | 0–120 | default: applied when omitted (`commands.c:1935`); domain: guidance |
| `scrambleHz` | number \| undefined | New-run default: 24 for profile 0, 18 for profile 1 | 0–120 Hz | default: applied when omitted (`commands.c:1937`); domain: guidance |
| `seed` | number \| undefined | New-run default: The scene seed (observed 2030 with seed 2030 at 160×48; 4242 with seed 4242 at 100×30) | Unsigned 32-bit integer, including 0 and 4294967295 | default: applied when omitted (`commands.c:1920`); domain: guidance |
| `staggerMs` | number \| undefined | New-run default: 24 for profile 0, 28 for profile 1 | Per-glyph progression offset, 0–10000 ms | default: applied when omitted (`commands.c:1934`); domain: guidance |
| `text` | string \| undefined | Observed default: "" | Retained Unicode source within native text capacity | default: engine readback; domain: guidance |
| `trailLength` | number \| undefined | New-run default: 0 for profile 0, 2 for profile 1 | Integer 0–8 | default: applied when omitted (`commands.c:1937`); domain: guidance |
| `variation` | number \| undefined | New-run default: 0.4 for profile 0, 0.55 for profile 1 | 0–2 | default: applied when omitted (`commands.c:1935`); domain: guidance |
| `width` | number \| undefined | New-run default: 100 | Positive integer layout width | default: applied when omitted (`commands.c:1908`); domain: guidance |
| `wind` | number \| undefined | New-run default: 1.3 for profile 0, 2 for profile 1 | −100–100 | default: applied when omitted (`commands.c:1936`); domain: guidance |
| `x` | number \| undefined | New-run default: 8 | Integer layout coordinates | default: applied when omitted (`commands.c:1906`); domain: guidance |
| `y` | number \| undefined | New-run default: 12 | Integer layout coordinates | default: applied when omitted (`commands.c:1907`); domain: guidance |

## Components

### text/direct-ink

| Field | Value |
|---|---|
| Name | Direct Ink |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 0 |
| Source identity | `text/kinetic/immediate` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/direct-ink"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/direct-ink","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/direct-ink"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/direct-ink","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/direct-ink","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/ink-dissolve

| Field | Value |
|---|---|
| Name | Ink Dissolve |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 1 |
| Source identity | `text/kinetic/fade` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/ink-dissolve"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ink-dissolve","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/ink-dissolve"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/ink-dissolve","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ink-dissolve","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/glyph-rain

| Field | Value |
|---|---|
| Name | Glyph Rain |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 2 |
| Source identity | `text/kinetic/rain` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/glyph-rain"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/glyph-rain","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/glyph-rain"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/glyph-rain","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/glyph-rain","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/cipher-resolve

| Field | Value |
|---|---|
| Name | Cipher Resolve |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 3 |
| Source identity | `text/kinetic/scramble` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/cipher-resolve"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/cipher-resolve","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/cipher-resolve"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/cipher-resolve","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/cipher-resolve","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/station-board

| Field | Value |
|---|---|
| Name | Station Board |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 4 |
| Source identity | `text/kinetic/flipboard` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/station-board"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/station-board","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/station-board"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/station-board","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/station-board","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/ribbon-left

| Field | Value |
|---|---|
| Name | Ribbon Left |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 5 |
| Source identity | `text/kinetic/sweep-left` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/ribbon-left"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ribbon-left","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/ribbon-left"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/ribbon-left","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ribbon-left","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/ribbon-right

| Field | Value |
|---|---|
| Name | Ribbon Right |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 6 |
| Source identity | `text/kinetic/sweep-right` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/ribbon-right"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ribbon-right","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/ribbon-right"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/ribbon-right","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ribbon-right","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/travelling-line

| Field | Value |
|---|---|
| Name | Travelling Line |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 7 |
| Source identity | `text/kinetic/marquee` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/travelling-line"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/travelling-line","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/travelling-line"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/travelling-line","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/travelling-line","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/satellite-type

| Field | Value |
|---|---|
| Name | Satellite Type |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 8 |
| Source identity | `text/kinetic/orbit` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/satellite-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/satellite-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/satellite-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/satellite-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/satellite-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/star-map-type

| Field | Value |
|---|---|
| Name | Star Map Type |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 9 |
| Source identity | `text/kinetic/constellation` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/star-map-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/star-map-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/star-map-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/star-map-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/star-map-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/prism-stitch

| Field | Value |
|---|---|
| Name | Prism Stitch |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 10 |
| Source identity | `text/kinetic/prism-stitch` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/prism-stitch"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/prism-stitch","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/prism-stitch"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/prism-stitch","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/prism-stitch","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/gravity-loom

| Field | Value |
|---|---|
| Name | Gravity Loom |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 11 |
| Source identity | `text/kinetic/gravity-loom` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/gravity-loom"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/gravity-loom","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/gravity-loom"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/gravity-loom","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/gravity-loom","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/scanline-type

| Field | Value |
|---|---|
| Name | Scanline Type |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 12 |
| Source identity | `text/kinetic/scanline` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/scanline-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/scanline-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/scanline-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/scanline-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/scanline-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/elastic-type

| Field | Value |
|---|---|
| Name | Elastic Type |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 13 |
| Source identity | `text/kinetic/elastic` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/elastic-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/elastic-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/elastic-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/elastic-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/elastic-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/keystep

| Field | Value |
|---|---|
| Name | Keystep |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 14 |
| Source identity | `text/kinetic/typewriter` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/keystep"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/keystep","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/keystep"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/keystep","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/keystep","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/curtain-type

| Field | Value |
|---|---|
| Name | Curtain Type |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 15 |
| Source identity | `text/kinetic/curtain` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/curtain-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/curtain-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/curtain-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/curtain-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/curtain-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/glyph-fall

| Field | Value |
|---|---|
| Name | Glyph Fall |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 16 |
| Source identity | `text/kinetic/fall` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/glyph-fall"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/glyph-fall","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/glyph-fall"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/glyph-fall","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/glyph-fall","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/ash-type

| Field | Value |
|---|---|
| Name | Ash Type |
| Contract | `TextTransition` |
| Profile | 0 |
| Algorithm | 17 |
| Source identity | `text/kinetic/ash` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/ash-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ash-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/ash-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/ash-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ash-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/instant-ink

| Field | Value |
|---|---|
| Name | Instant Ink |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 0 |
| Source identity | `text/atelier/instant` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/instant-ink"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/instant-ink","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/instant-ink"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/instant-ink","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/instant-ink","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/velvet-dissolve

| Field | Value |
|---|---|
| Name | Velvet Dissolve |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 1 |
| Source identity | `text/atelier/fade` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/velvet-dissolve"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/velvet-dissolve","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/velvet-dissolve"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/velvet-dissolve","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/velvet-dissolve","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/skyfall-type

| Field | Value |
|---|---|
| Name | Skyfall Type |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 2 |
| Source identity | `text/atelier/rain` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/skyfall-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/skyfall-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/skyfall-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/skyfall-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/skyfall-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/static-resolve

| Field | Value |
|---|---|
| Name | Static Resolve |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 3 |
| Source identity | `text/atelier/scramble` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/static-resolve"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/static-resolve","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/static-resolve"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/static-resolve","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/static-resolve","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/departure-board

| Field | Value |
|---|---|
| Name | Departure Board |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 4 |
| Source identity | `text/atelier/flipboard` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/departure-board"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/departure-board","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/departure-board"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/departure-board","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/departure-board","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/weft-left

| Field | Value |
|---|---|
| Name | Weft Left |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 5 |
| Source identity | `text/atelier/sweep-left` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/weft-left"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/weft-left","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/weft-left"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/weft-left","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/weft-left","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/weft-right

| Field | Value |
|---|---|
| Name | Weft Right |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 6 |
| Source identity | `text/atelier/sweep-right` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/weft-right"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/weft-right","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/weft-right"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/weft-right","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/weft-right","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/rising-ink

| Field | Value |
|---|---|
| Name | Rising Ink |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 18 |
| Source identity | `text/atelier/lift` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/rising-ink"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/rising-ink","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/rising-ink"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/rising-ink","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/rising-ink","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/falling-ink

| Field | Value |
|---|---|
| Name | Falling Ink |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 16 |
| Source identity | `text/atelier/fall` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/falling-ink"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/falling-ink","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/falling-ink"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/falling-ink","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/falling-ink","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/ticker-type

| Field | Value |
|---|---|
| Name | Ticker Type |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 7 |
| Source identity | `text/atelier/marquee` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/ticker-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ticker-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/ticker-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/ticker-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ticker-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/iris-type

| Field | Value |
|---|---|
| Name | Iris Type |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 19 |
| Source identity | `text/atelier/iris` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/iris-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/iris-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/iris-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/iris-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/iris-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/constellation-type

| Field | Value |
|---|---|
| Name | Constellation Type |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 9 |
| Source identity | `text/atelier/constellation` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/constellation-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/constellation-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/constellation-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/constellation-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/constellation-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/prism-weave

| Field | Value |
|---|---|
| Name | Prism Weave |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 20 |
| Source identity | `text/atelier/prism-weave` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/prism-weave"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/prism-weave","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/prism-weave"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/prism-weave","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/prism-weave","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/ink-tide

| Field | Value |
|---|---|
| Name | Ink Tide |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 21 |
| Source identity | `text/atelier/ink-tide` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/ink-tide"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ink-tide","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/ink-tide"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/ink-tide","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/ink-tide","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/comet-stitch

| Field | Value |
|---|---|
| Name | Comet Stitch |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 22 |
| Source identity | `text/atelier/comet-stitch` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/comet-stitch"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/comet-stitch","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/comet-stitch"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/comet-stitch","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/comet-stitch","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/orbital-type

| Field | Value |
|---|---|
| Name | Orbital Type |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 8 |
| Source identity | `text/atelier/orbit` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/orbital-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/orbital-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/orbital-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/orbital-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/orbital-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/folded-type

| Field | Value |
|---|---|
| Name | Folded Type |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 23 |
| Source identity | `text/atelier/fold` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/folded-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/folded-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/folded-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/folded-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/folded-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`

### text/zipper-type

| Field | Value |
|---|---|
| Name | Zipper Type |
| Contract | `TextTransition` |
| Profile | 1 |
| Algorithm | 24 |
| Source identity | `text/atelier/zipper` |
| Commands | [`text`](#parameters-of-text) |

Accepted by the native library:

**Minimal text command**

```json
{"op":"text","id":1,"effect":"text/zipper-type"}
```

**Value at the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/zipper-type","durationMs":60000}
```

Refused by the native library:

**Identity used on the window command of another family**

```json
{"op":"window","id":1,"effect":"text/zipper-type"}
```

Diagnostic: `Unknown window transition`

**Value outside the finite choices of phase**

```json
{"op":"text","id":1,"effect":"text/zipper-type","phase":"unlisted"}
```

Diagnostic: `Invalid choice: phase`

**Value above the stated maximum of durationMs**

```json
{"op":"text","id":1,"effect":"text/zipper-type","durationMs":60001}
```

Diagnostic: `Invalid duration: durationMs`
