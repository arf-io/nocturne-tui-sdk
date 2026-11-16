# Surface field components

4 identities with the native contract `SurfaceField`. An identity is the value of the `effect` field of `field`. Back to the [catalogue](Catalogue.md).

Each default and domain comes from the command guidance, from values the engine reads back, or from commands the engine accepts and refuses. The Basis column says which.

An observed default is a value the engine reads back identically in two scenes that differ in seed and viewport size. A default applied when omitted is the value the engine uses when the field is left out: the command without the field and the same command naming the value leave identical documents. A required parameter is refused when omitted. A default read back from info is what info reports after the command without the field. An observed domain is the range the engine accepts: it accepts the edge values and refuses values just beyond them. A file and line in the Basis column point to the native statement that applies the default or checks the domain.

## Parameters of field

| Parameter | Type | Default | Domain | Basis |
|---|---|---|---|---|
| `continuous` | boolean \| undefined | Observed default: false | Boolean: true or false | default: engine readback; domain: declared type |
| `effect` | string \| undefined | Applied when omitted: "surface-field/silk-tide" | A SurfaceField identity from the catalogue, 4 identities | default: applied when omitted (`commands.c:1490`); domain: catalogue |
| `falloff` | number \| undefined | Observed default: 2 | Observed: integers from 1 to 8 | default: engine readback; domain: refusal probes |
| `frequency` | number \| undefined | Observed default: 100 | Observed: numbers from 0 to 1000 | default: engine readback; domain: refusal probes |
| `interference` | number \| undefined | Observed default: 0 | Observed: numbers from 0 to 1 | default: engine readback; domain: refusal probes |
| `lifeMs` | number \| undefined | Observed default: 3000 | Observed: numbers from 0 to 60000 | default: engine readback; domain: refusal probes |
| `material` | number \| undefined | Observed default: 1 | Observed: integers from 0 to 15 | default: engine readback; domain: refusal probes |
| `optics` | "source" \| "legacy" \| undefined | Observed default: "legacy" | One of "source", "legacy" | default: engine readback; domain: declared type |
| `paint` | "source" \| "field" \| undefined | Observed default: "field" | One of "source", "field" | default: engine readback; domain: declared type |
| `phase` | number \| undefined | Observed default: 0 | Observed: numbers from -3600 to 3600 | default: engine readback; domain: refusal probes |
| `rings` | number \| undefined | Observed default: 0 | Observed: integers from 1 to 16 | default: engine readback; domain: refusal probes |
| `seed` | number \| undefined | Applied when omitted: nrHash(scene seed XOR field id); with paint "source", the field id for algorithms 0 and 1 and 2030 otherwise (observed 4064474032 with seed 2030 at 160×48; 412505799 with seed 4242 at 100×30) | Observed: integers from 0 to 4294967295 | default: applied when omitted (`commands.c:313`, `commands.c:1503`); domain: refusal probes |
| `speed` | number \| undefined | Observed default: 8 | Observed: numbers from 0 to 100 | default: engine readback; domain: refusal probes |
| `strength` | number \| undefined | Observed default: 0.65 | Observed: numbers from 0 to 1 | default: engine readback; domain: refusal probes |
| `surface` | { x: number; y: number; width: number; height: number; } \| undefined | Applied when omitted: none; info reads back null | Object with members height, width, x, y | default: read back from info (`commands.c:1519`); domain: declared type |
| `surface.height` | number | required | Observed in a declared surface: numbers from 0.05 to 2147483647 | default: refused when omitted (`commands.c:1519`); domain: accepted and refused commands (`commands.c:1519`) |
| `surface.width` | number | required | Observed in a declared surface: numbers from 0.05 to 2147483647 | default: refused when omitted (`commands.c:1519`); domain: accepted and refused commands (`commands.c:1519`) |
| `surface.x` | number | required | Observed in a declared surface: numbers from -2147483648 to 2147483647 | default: refused when omitted (`commands.c:1519`); domain: accepted and refused commands (`commands.c:1519`) |
| `surface.y` | number | required | Observed in a declared surface: numbers from -2147483648 to 2147483647 | default: refused when omitted (`commands.c:1519`); domain: accepted and refused commands (`commands.c:1519`) |
| `velocity` | readonly [number, number] \| undefined | Observed default: [0,0] | Observed: two numbers [x, y], x from -100 to 100 and y from -100 to 100 | default: engine readback; domain: accepted and refused commands (`commands.c:1518`) |
| `width` | number \| undefined | Observed default: 1.4 | Observed: numbers from 0.05 to 2147483647 | default: engine readback; domain: refusal probes |
| `x` | number \| undefined | Applied when omitted: Half the scene width (observed 80 with seed 2030 at 160×48; 50 with seed 4242 at 100×30) | Observed: numbers from -2147483648 to 2147483647 | default: applied when omitted (`commands.c:1492`); domain: refusal probes |
| `y` | number \| undefined | Applied when omitted: Half the scene height (observed 24 with seed 2030 at 160×48; 15 with seed 4242 at 100×30) | Observed: numbers from -2147483648 to 2147483647 | default: applied when omitted (`commands.c:1492`); domain: refusal probes |

## Components

### surface-field/silk-tide

| Field | Value |
|---|---|
| Name | Silk Tide |
| Contract | `SurfaceField` |
| Profile | 0 |
| Algorithm | 0 |
| Source identity | `weather/studio.ripples` |
| Commands | [`field`](#parameters-of-field) |

Accepted by the native library:

**Minimal field command**

```json
{"op":"field","effect":"surface-field/silk-tide"}
```

Refused by the native library:

**Identity used on the text command of another family**

```json
{"op":"text","id":1,"effect":"surface-field/silk-tide"}
```

Diagnostic: `Unknown text effect`

**Value outside the finite choices of optics**

```json
{"op":"field","effect":"surface-field/silk-tide","optics":"unlisted"}
```

Diagnostic: `Invalid choice: optics`

### surface-field/satin-rings

| Field | Value |
|---|---|
| Name | Satin Rings |
| Contract | `SurfaceField` |
| Profile | 0 |
| Algorithm | 1 |
| Source identity | `weather/observatory.ripples` |
| Commands | [`field`](#parameters-of-field) |

Accepted by the native library:

**Minimal field command**

```json
{"op":"field","effect":"surface-field/satin-rings"}
```

Refused by the native library:

**Identity used on the text command of another family**

```json
{"op":"text","id":1,"effect":"surface-field/satin-rings"}
```

Diagnostic: `Unknown text effect`

**Value outside the finite choices of optics**

```json
{"op":"field","effect":"surface-field/satin-rings","optics":"unlisted"}
```

Diagnostic: `Invalid choice: optics`

### surface-field/opal-fronts

| Field | Value |
|---|---|
| Name | Opal Fronts |
| Contract | `SurfaceField` |
| Profile | 0 |
| Algorithm | 2 |
| Source identity | `weather/kinetic.ripples` |
| Commands | [`field`](#parameters-of-field) |

Accepted by the native library:

**Minimal field command**

```json
{"op":"field","effect":"surface-field/opal-fronts"}
```

Refused by the native library:

**Identity used on the text command of another family**

```json
{"op":"text","id":1,"effect":"surface-field/opal-fronts"}
```

Diagnostic: `Unknown text effect`

**Value outside the finite choices of optics**

```json
{"op":"field","effect":"surface-field/opal-fronts","optics":"unlisted"}
```

Diagnostic: `Invalid choice: optics`

### surface-field/interference-tide

| Field | Value |
|---|---|
| Name | Interference Tide |
| Contract | `SurfaceField` |
| Profile | 0 |
| Algorithm | 3 |
| Source identity | `weather/atelier.ripples` |
| Commands | [`field`](#parameters-of-field) |

Accepted by the native library:

**Minimal field command**

```json
{"op":"field","effect":"surface-field/interference-tide"}
```

Refused by the native library:

**Identity used on the text command of another family**

```json
{"op":"text","id":1,"effect":"surface-field/interference-tide"}
```

Diagnostic: `Unknown text effect`

**Value outside the finite choices of optics**

```json
{"op":"field","effect":"surface-field/interference-tide","optics":"unlisted"}
```

Diagnostic: `Invalid choice: optics`
