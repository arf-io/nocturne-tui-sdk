# Weather components

26 identities with the native contract `ParticleEmitter`. An identity is the value of the `effect` field of `emitter`, `weather-author`. Back to the [catalogue](Catalogue.md).

Each default and domain comes from the command guidance, from values the engine reads back, or from commands the engine accepts and refuses. The Basis column says which. The engine reads back a different starting value for 17 of these identities; each is listed in its entry.

An observed default is a value the engine reads back identically in two scenes that differ in seed and viewport size. A default applied when omitted is the value the engine uses when the field is left out: the command without the field and the same command naming the value leave identical documents. A required parameter is refused when omitted. An observed domain is the range the engine accepts: it accepts the edge values and refuses values just beyond them. A file and line in the Basis column point to the native statement that applies the default or checks the domain.

## Parameters of emitter

| Parameter | Type | Default | Domain | Basis |
|---|---|---|---|---|
| `alpha` | number \| undefined | Leaf default: 0.95 | 0..1 | guidance |
| `angularVelocity` | Vector3 \| undefined | Leaf default: Unauthored | Each −720..720 degrees/second; authored motion supported for leaves/snow | guidance |
| `backTint` | number \| undefined | Leaf default: 0.3 | 0..1 | guidance |
| `birthFadeMs` | number \| undefined | Leaf default: 120 | 0..60000 milliseconds | guidance |
| `birthOrientation` | Vector3 \| undefined | Leaf default: `[0,0,0]` | Each −3600..3600 degrees; active X, then Y, then Z rotations | guidance |
| `colliders` | ColliderSelection \| undefined | Leaf default: Default floor selection | Explicit object with `floor` Boolean and named surface ID array | guidance |
| `colliders.floor` | boolean \| undefined | Observed default: true | Boolean: true or false | default: engine readback; domain: declared type |
| `colliders.surfaces` | readonly number[] \| undefined | Observed default: [] | Up to 16 distinct integer surface IDs from 1 to 16, each naming an existing surface | default: engine readback; domain: accepted and refused commands (`geometry.c:146`, `geometry.c:150`, `geometry.c:152`, `geometry.c:153`) |
| `collision` | boolean \| undefined | Leaf default: `true` | Boolean | guidance |
| `coreMs` | number \| undefined | Leaf default: 120 | 0..10000 milliseconds | guidance |
| `count` | number \| undefined | Native default: 100 | Integer 0..100000 scheduled births; not a guarantee that this many particles fit concurrently | guidance |
| `curl` | number \| undefined | Leaf default: 0 | −2..2 | guidance |
| `cycles` | number \| undefined | Native default: 1 | Integer 1..10000; rate-based emission requires one cycle | guidance |
| `deathFadeMs` | number \| undefined | Leaf default: 700 | 0..60000 milliseconds | guidance |
| `deposit` | boolean \| undefined | Leaf default: `true` | Boolean; requires collision enabled | guidance |
| `distribution` | "legacy" \| "uniform" \| undefined | Leaf default: `legacy` | `legacy` or `uniform` shape sampling | guidance |
| `drag` | number \| undefined | Leaf default: 1.4 | 0..30; native relative-air movement coefficient | guidance |
| `effect` | string \| undefined | Native default: `weather/autumn-drift` | A current native particle-effect catalogue identity | guidance |
| `endStyle` | EndStyle \| undefined | Leaf default: `drain` | `drain`, `settle`, `dissolve`, `gust`, `quench`, `disperse`; the effect must support the selected ending | guidance |
| `extent` | Vector3 \| undefined | Leaf default: `[28,6,22]` | Each 0..2000; shape extent in the birth frame | guidance |
| `farDistance` | number \| undefined | Leaf default: 10000 | 0.01..10000; strictly beyond near distance | guidance |
| `farFadeDistance` | number \| undefined | Leaf default: 0 | 0..10000; no greater than far minus near distance | guidance |
| `flutterAmount` | number \| undefined | Leaf default: 0.5 | 0..10; effect-dependent flutter amount | guidance |
| `flutterHz` | number \| undefined | Leaf default: 1.4 | 0..30 cycles/second | guidance |
| `gapMs` | number \| undefined | Native default: 0 | 0..60000 milliseconds between cycles | guidance |
| `gravity` | Vector3 \| undefined | Leaf default: `[0,-4,0]` | Each −256..256; scene units/second² | guidance |
| `heat` | number \| undefined | Leaf default: 12 | 0..64; effect-dependent heat control | guidance |
| `id` | number | Native default: Required | Integer 1..65535; unique existing emitter ownership | guidance |
| `initialOrientation` | Vector3 \| undefined | Leaf default: Unauthored | Each −3600..3600 degrees; authored motion supported for leaves/snow | guidance |
| `lifetimeMaxMs` | number \| undefined | Leaf default: 8000,14000 | Minimum at least 1 ms; maximum 3600000 ms; ordered bounds | guidance |
| `lifetimeMinMs` | number \| undefined | Leaf default: 8000,14000 | Minimum at least 1 ms; maximum 3600000 ms; ordered bounds | guidance |
| `lift` | number \| undefined | Leaf default: 0.3 | 0..20; native movement coefficient | guidance |
| `material` | number \| undefined | Leaf default: 1 | Integer 0..15; native material slot | guidance |
| `nearDistance` | number \| undefined | Leaf default: 0.001 | 0.001..1000 | guidance |
| `position` | Vector3 \| undefined | Leaf default: `[0,18,0]` | Each component −16000..16000; world-space pivot | guidance |
| `radius` | number \| undefined | Leaf default: 6 | 0.1..200; effect-dependent radial scale | guidance |
| `rate` | number \| undefined | Native default: 0 | 0..10000; a positive value selects rate-based emission; do not author together with `count` | guidance |
| `runningTimeMs` | number \| undefined | Native default: 8000 | 0..86400000 milliseconds; zero supports burst schedules | guidance |
| `sampling` | Sampling \| undefined | Leaf default: `braille` | `cell`, `half`, `braille`, `hybrid` | guidance |
| `schedule` | "uniform" \| "seeded-jitter" \| undefined | Native default: `uniform` | `uniform` or `seeded-jitter` | guidance |
| `seed` | number \| undefined | Native default: Hash of scene seed XOR emitter ID | uint32; explicit seeds reproduce the configured random sequence | guidance |
| `shape` | "point" \| "box" \| "sphere" \| "disc" \| "line" \| undefined | Leaf default: `box` | `point`, `box`, `sphere`, `disc`, `line` | guidance |
| `shapeWeights` | Vector3 \| undefined | Leaf default: `[1,0,0]` | Each 0..1; sum must be positive | guidance |
| `sizeMax` | number \| undefined | Leaf default: 0.6,1.4 | 0.005..64; minimum must not exceed maximum | guidance |
| `sizeMin` | number \| undefined | Leaf default: 0.6,1.4 | 0.005..64; minimum must not exceed maximum | guidance |
| `spread` | Vector3 \| undefined | Leaf default: `[1,1,1]` | Each 0..128; initial velocity variation | guidance |
| `startTimeUs` | number \| undefined | Native default: Current scene time | Microseconds, not before the current time, within the 24-hour scene range | guidance |
| `surfaceAlpha` | number \| undefined | Leaf default: 0.22 | 0..1; leaf surface setting | guidance |
| `tailMs` | number \| undefined | Leaf default: 3000 | 0..3600000 milliseconds | guidance |
| `topology` | 0 \| 1 \| 2 \| 3 \| 4 \| 5 \| undefined | Leaf default: 0 | Integer 0..5; geometry treatment, with profile-specific defaults | guidance |
| `trailMs` | number \| undefined | Leaf default: 120 | 0..2000 milliseconds | guidance |
| `tumble` | Vector3 \| undefined | Leaf default: `[45,65,90]` | Each −720..720; procedural rotation control | guidance |
| `twoSided` | boolean \| undefined | Leaf default: `true` | Boolean | guidance |
| `veinContrast` | number \| undefined | Leaf default: 0.75 | 0..1 | guidance |
| `velocity` | Vector3 \| undefined | Leaf default: `[0,-1,0]` | Each −256..256; initial scene units/second | guidance |
| `wind` | Vector3 \| undefined | Leaf default: `[1.5,0,0.8]` | Each −256..256; air velocity in scene units/second | guidance |
| `windPeriodSeconds` | number \| undefined | Leaf default: 6 | 0.1..120 seconds | guidance |
| `windScale` | number \| undefined | Leaf default: 12 | 0.1..1000; spatial wind scale | guidance |
| `windVariation` | Vector3 \| undefined | Leaf default: `[0.8,0.15,1]` | Each 0..128; variation amplitudes | guidance |

## Parameters of weather-author

| Parameter | Type | Default | Domain | Basis |
|---|---|---|---|---|
| `birth` | (Pick<EmitterOptions, "shape" \| "distribution" \| "position" \| "extent" \| "velocity" \| "spread" \| "initialOrientation" \| "angularVelocity"> & { orientation?: Vector3 \| undefined; }) \| undefined | Applied when omitted: {}: each member takes the default in its own row | Object with members angularVelocity, distribution, extent, initialOrientation, orientation, position, shape, spread, velocity | default: applied when omitted (`commands.c:636`); domain: declared type |
| `birth.angularVelocity` | Vector3 \| undefined | Leaf default: Unauthored | Each −720..720 degrees/second; authored motion supported for leaves/snow | weather-author projection |
| `birth.distribution` | "legacy" \| "uniform" \| undefined | Leaf default: `legacy` | `legacy` or `uniform` shape sampling | weather-author projection |
| `birth.extent` | Vector3 \| undefined | Leaf default: `[28,6,22]` | Each 0..2000; shape extent in the birth frame | weather-author projection |
| `birth.initialOrientation` | Vector3 \| undefined | Leaf default: Unauthored | Each −3600..3600 degrees; authored motion supported for leaves/snow | weather-author projection |
| `birth.orientation` | Vector3 \| undefined | Leaf default: `[0,0,0]` | Each −3600..3600 degrees; active X, then Y, then Z rotations | weather-author projection |
| `birth.position` | Vector3 \| undefined | Leaf default: `[0,18,0]` | Each component −16000..16000; world-space pivot | weather-author projection |
| `birth.shape` | "point" \| "box" \| "sphere" \| "disc" \| "line" \| undefined | Leaf default: `box` | `point`, `box`, `sphere`, `disc`, `line` | weather-author projection |
| `birth.spread` | Vector3 \| undefined | Leaf default: `[1,1,1]` | Each 0..128; initial velocity variation | weather-author projection |
| `birth.velocity` | Vector3 \| undefined | Leaf default: `[0,-1,0]` | Each −256..256; initial scene units/second | weather-author projection |
| `collision` | { enabled?: boolean \| undefined; deposit?: boolean \| undefined; } \| undefined | Applied when omitted: {}: each member takes the default in its own row | Object with members deposit, enabled | default: applied when omitted (`commands.c:636`); domain: declared type |
| `collision.deposit` | boolean \| undefined | Leaf default: `true` | Boolean; requires collision enabled | weather-author projection |
| `collision.enabled` | boolean \| undefined | Leaf default: `true` | Boolean | weather-author projection |
| `effect` | string | required | A current native particle-effect catalogue identity | default: refused when omitted (`commands.c:607`); domain: weather-author projection |
| `emission` | Pick<EmitterOptions, "schedule" \| "seed" \| "count" \| "rate" \| "runningTimeMs" \| "startTimeUs" \| "cycles" \| "gapMs"> \| undefined | Applied when omitted: {}: each member takes the default in its own row | Object with members count, cycles, gapMs, rate, runningTimeMs, schedule, seed, startTimeUs | default: applied when omitted (`commands.c:636`); domain: declared type |
| `emission.count` | number \| undefined | Native default: 100 | Integer 0..100000 scheduled births; not a guarantee that this many particles fit concurrently | weather-author projection |
| `emission.cycles` | number \| undefined | Native default: 1 | Integer 1..10000; rate-based emission requires one cycle | weather-author projection |
| `emission.gapMs` | number \| undefined | Native default: 0 | 0..60000 milliseconds between cycles | weather-author projection |
| `emission.rate` | number \| undefined | Native default: 0 | 0..10000; a positive value selects rate-based emission; do not author together with `count` | weather-author projection |
| `emission.runningTimeMs` | number \| undefined | Native default: 8000 | 0..86400000 milliseconds; zero supports burst schedules | weather-author projection |
| `emission.schedule` | "uniform" \| "seeded-jitter" \| undefined | Native default: `uniform` | `uniform` or `seeded-jitter` | weather-author projection |
| `emission.seed` | number \| undefined | Native default: Hash of scene seed XOR emitter ID | uint32; explicit seeds reproduce the configured random sequence | weather-author projection |
| `emission.startTimeUs` | number \| undefined | Native default: Current scene time | Microseconds, not before the current time, within the 24-hour scene range | weather-author projection |
| `forces` | Pick<EmitterOptions, "gravity" \| "wind" \| "windVariation" \| "drag" \| "lift" \| "flutterHz" \| "flutterAmount" \| "tumble" \| "heat" \| "windScale" \| "windPeriodSeconds"> \| undefined | Applied when omitted: {}: each member takes the default in its own row | Object with members drag, flutterAmount, flutterHz, gravity, heat, lift, tumble, wind, windPeriodSeconds, windScale, windVariation | default: applied when omitted (`commands.c:636`); domain: declared type |
| `forces.drag` | number \| undefined | Leaf default: 1.4 | 0..30; native relative-air movement coefficient | weather-author projection |
| `forces.flutterAmount` | number \| undefined | Leaf default: 0.5 | 0..10; effect-dependent flutter amount | weather-author projection |
| `forces.flutterHz` | number \| undefined | Leaf default: 1.4 | 0..30 cycles/second | weather-author projection |
| `forces.gravity` | Vector3 \| undefined | Leaf default: `[0,-4,0]` | Each −256..256; scene units/second² | weather-author projection |
| `forces.heat` | number \| undefined | Leaf default: 12 | 0..64; effect-dependent heat control | weather-author projection |
| `forces.lift` | number \| undefined | Leaf default: 0.3 | 0..20; native movement coefficient | weather-author projection |
| `forces.tumble` | Vector3 \| undefined | Leaf default: `[45,65,90]` | Each −720..720; procedural rotation control | weather-author projection |
| `forces.wind` | Vector3 \| undefined | Leaf default: `[1.5,0,0.8]` | Each −256..256; air velocity in scene units/second | weather-author projection |
| `forces.windPeriodSeconds` | number \| undefined | Leaf default: 6 | 0.1..120 seconds | weather-author projection |
| `forces.windScale` | number \| undefined | Leaf default: 12 | 0.1..1000; spatial wind scale | weather-author projection |
| `forces.windVariation` | Vector3 \| undefined | Leaf default: `[0.8,0.15,1]` | Each 0..128; variation amplitudes | weather-author projection |
| `id` | number | Native default: Required | Integer 1..65535; unique existing emitter ownership | weather-author projection |
| `lifecycle` | Pick<EmitterOptions, "lifetimeMinMs" \| "lifetimeMaxMs" \| "endStyle" \| "tailMs"> \| undefined | Applied when omitted: {}: each member takes the default in its own row | Object with members endStyle, lifetimeMaxMs, lifetimeMinMs, tailMs | default: applied when omitted (`commands.c:636`); domain: declared type |
| `lifecycle.endStyle` | EndStyle \| undefined | Leaf default: `drain` | `drain`, `settle`, `dissolve`, `gust`, `quench`, `disperse`; the effect must support the selected ending | weather-author projection |
| `lifecycle.lifetimeMaxMs` | number \| undefined | Leaf default: 8000,14000 | Minimum at least 1 ms; maximum 3600000 ms; ordered bounds | weather-author projection |
| `lifecycle.lifetimeMinMs` | number \| undefined | Leaf default: 8000,14000 | Minimum at least 1 ms; maximum 3600000 ms; ordered bounds | weather-author projection |
| `lifecycle.tailMs` | number \| undefined | Leaf default: 3000 | 0..3600000 milliseconds | weather-author projection |
| `particle` | Pick<EmitterOptions, "material" \| "shapeWeights" \| "sizeMin" \| "sizeMax" \| "alpha" \| "radius" \| "topology" \| "trailMs" \| "birthFadeMs" \| "deathFadeMs" \| "coreMs" \| ... 8 more ... \| "surfaceAlpha"> \| undefined | Applied when omitted: {}: each member takes the default in its own row | Object with members alpha, backTint, birthFadeMs, coreMs, curl, deathFadeMs, farDistance, farFadeDistance, material, nearDistance, radius, sampling, shapeWeights, sizeMax, sizeMin, surfaceAlpha, topology, trailMs, twoSided, veinContrast | default: applied when omitted (`commands.c:636`); domain: declared type |
| `particle.alpha` | number \| undefined | Leaf default: 0.95 | 0..1 | weather-author projection |
| `particle.backTint` | number \| undefined | Leaf default: 0.3 | 0..1 | weather-author projection |
| `particle.birthFadeMs` | number \| undefined | Leaf default: 120 | 0..60000 milliseconds | weather-author projection |
| `particle.coreMs` | number \| undefined | Leaf default: 120 | 0..10000 milliseconds | weather-author projection |
| `particle.curl` | number \| undefined | Leaf default: 0 | −2..2 | weather-author projection |
| `particle.deathFadeMs` | number \| undefined | Leaf default: 700 | 0..60000 milliseconds | weather-author projection |
| `particle.farDistance` | number \| undefined | Leaf default: 10000 | 0.01..10000; strictly beyond near distance | weather-author projection |
| `particle.farFadeDistance` | number \| undefined | Leaf default: 0 | 0..10000; no greater than far minus near distance | weather-author projection |
| `particle.material` | number \| undefined | Leaf default: 1 | Integer 0..15; native material slot | weather-author projection |
| `particle.nearDistance` | number \| undefined | Leaf default: 0.001 | 0.001..1000 | weather-author projection |
| `particle.radius` | number \| undefined | Leaf default: 6 | 0.1..200; effect-dependent radial scale | weather-author projection |
| `particle.sampling` | Sampling \| undefined | Leaf default: `braille` | `cell`, `half`, `braille`, `hybrid` | weather-author projection |
| `particle.shapeWeights` | Vector3 \| undefined | Leaf default: `[1,0,0]` | Each 0..1; sum must be positive | weather-author projection |
| `particle.sizeMax` | number \| undefined | Leaf default: 0.6,1.4 | 0.005..64; minimum must not exceed maximum | weather-author projection |
| `particle.sizeMin` | number \| undefined | Leaf default: 0.6,1.4 | 0.005..64; minimum must not exceed maximum | weather-author projection |
| `particle.surfaceAlpha` | number \| undefined | Leaf default: 0.22 | 0..1; leaf surface setting | weather-author projection |
| `particle.topology` | 0 \| 1 \| 2 \| 3 \| 4 \| 5 \| undefined | Leaf default: 0 | Integer 0..5; geometry treatment, with profile-specific defaults | weather-author projection |
| `particle.trailMs` | number \| undefined | Leaf default: 120 | 0..2000 milliseconds | weather-author projection |
| `particle.twoSided` | boolean \| undefined | Leaf default: `true` | Boolean | weather-author projection |
| `particle.veinContrast` | number \| undefined | Leaf default: 0.75 | 0..1 | weather-author projection |
| `schema` | "nocturne.weather-authoring/v1" | required | One of "nocturne.weather-authoring/v1" | default: refused when omitted (`commands.c:606`); domain: declared type |

## Components

### weather/pearl-bloom

| Field | Value |
|---|---|
| Name | Pearl Bloom |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 4 |
| Source identity | `weather/studio.nova` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/pearl-bloom"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/pearl-bloom"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/pearl-bloom","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/pearl-bloom"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/pearl-bloom","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/pearl-bloom","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/corona-flare

| Field | Value |
|---|---|
| Name | Corona Flare |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 4 |
| Source identity | `weather/observatory.nova` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/corona-flare"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/corona-flare"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/corona-flare","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/corona-flare"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/corona-flare","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/corona-flare","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/pinfire

| Field | Value |
|---|---|
| Name | Pinfire |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 6 |
| Source identity | `weather/observatory.sparks` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `24`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/pinfire"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/pinfire"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/pinfire","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/pinfire"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/pinfire","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/pinfire","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/lantern-motes

| Field | Value |
|---|---|
| Name | Lantern Motes |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 3 |
| Source identity | `weather/observatory.embers` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `240`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/lantern-motes"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/lantern-motes"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/lantern-motes","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/lantern-motes"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/lantern-motes","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/lantern-motes","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/rain-threads

| Field | Value |
|---|---|
| Name | Rain Threads |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 1 |
| Source identity | `weather/observatory.rain` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `800`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/rain-threads"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/rain-threads"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/rain-threads","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/rain-threads"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/rain-threads","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/rain-threads","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/snow-dust

| Field | Value |
|---|---|
| Name | Snow Dust |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 2 |
| Source identity | `weather/observatory.snow` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `240`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/snow-dust"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/snow-dust"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/snow-dust","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/snow-dust"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/snow-dust","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/snow-dust","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/chrysanthemum

| Field | Value |
|---|---|
| Name | Chrysanthemum |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 4 |
| Source identity | `weather/kinetic.nova` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/chrysanthemum"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/chrysanthemum"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/chrysanthemum","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/chrysanthemum"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/chrysanthemum","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/chrysanthemum","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/branchlight

| Field | Value |
|---|---|
| Name | Branchlight |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 6 |
| Source identity | `weather/kinetic.sparks` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `24`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/branchlight"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/branchlight"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/branchlight","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/branchlight"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/branchlight","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/branchlight","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/hearth-spray

| Field | Value |
|---|---|
| Name | Hearth Spray |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 3 |
| Source identity | `weather/kinetic.embers` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `240`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/hearth-spray"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/hearth-spray"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/hearth-spray","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/hearth-spray"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/hearth-spray","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/hearth-spray","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/wire-rain

| Field | Value |
|---|---|
| Name | Wire Rain |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 1 |
| Source identity | `weather/kinetic.rain` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `800`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/wire-rain"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/wire-rain"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/wire-rain","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/wire-rain"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/wire-rain","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/wire-rain","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/pearl-flurry

| Field | Value |
|---|---|
| Name | Pearl Flurry |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 2 |
| Source identity | `weather/kinetic.snow` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `240`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/pearl-flurry"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/pearl-flurry"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/pearl-flurry","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/pearl-flurry"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/pearl-flurry","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/pearl-flurry","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/fractured-sun

| Field | Value |
|---|---|
| Name | Fractured Sun |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 4 |
| Source identity | `weather/atelier.nova` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/fractured-sun"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/fractured-sun"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/fractured-sun","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/fractured-sun"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/fractured-sun","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/fractured-sun","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/livewire

| Field | Value |
|---|---|
| Name | Livewire |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 6 |
| Source identity | `weather/atelier.sparks` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `24`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/livewire"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/livewire"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/livewire","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/livewire"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/livewire","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/livewire","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/copper-cinders

| Field | Value |
|---|---|
| Name | Copper Cinders |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 3 |
| Source identity | `weather/atelier.embers` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `240`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/copper-cinders"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/copper-cinders"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/copper-cinders","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/copper-cinders"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/copper-cinders","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/copper-cinders","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/slantfall

| Field | Value |
|---|---|
| Name | Slantfall |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 1 |
| Source identity | `weather/atelier.rain` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `800`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/slantfall"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/slantfall"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/slantfall","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/slantfall"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/slantfall","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/slantfall","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/crystalline-drift

| Field | Value |
|---|---|
| Name | Crystalline Drift |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 2 |
| Source identity | `weather/atelier.snow` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `240`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/crystalline-drift"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/crystalline-drift"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/crystalline-drift","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/crystalline-drift"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/crystalline-drift","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/crystalline-drift","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/ejecta-shell

| Field | Value |
|---|---|
| Name | Ejecta Shell |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 5 |
| Source identity | `weather/world.nova` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/ejecta-shell"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/ejecta-shell"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/ejecta-shell","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/ejecta-shell"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/ejecta-shell","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/ejecta-shell","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/starburst

| Field | Value |
|---|---|
| Name | Starburst |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 4 |
| Source identity | `weather/world.firework` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/starburst"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/starburst"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/starburst","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/starburst"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/starburst","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/starburst","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/forked-voltage

| Field | Value |
|---|---|
| Name | Forked Voltage |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 6 |
| Source identity | `weather/world.sparks` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `24`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/forked-voltage"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/forked-voltage"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/forked-voltage","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/forked-voltage"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/forked-voltage","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/forked-voltage","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/solar-cinders

| Field | Value |
|---|---|
| Name | Solar Cinders |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 3 |
| Source identity | `weather/world.embers` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `240`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/solar-cinders"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/solar-cinders"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/solar-cinders","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/solar-cinders"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/solar-cinders","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/solar-cinders","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/leaf-ribbon

| Field | Value |
|---|---|
| Name | Leaf Ribbon |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 0 |
| Source identity | `weather/world.leaves` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/leaf-ribbon"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/leaf-ribbon"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/leaf-ribbon","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/leaf-ribbon"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/leaf-ribbon","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/leaf-ribbon","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/storm-volume

| Field | Value |
|---|---|
| Name | Storm Volume |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 1 |
| Source identity | `weather/world.rain` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `800`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/storm-volume"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/storm-volume"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/storm-volume","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/storm-volume"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/storm-volume","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/storm-volume","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/snowfall-volume

| Field | Value |
|---|---|
| Name | Snowfall Volume |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 2 |
| Source identity | `weather/world.snow` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `240`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/snowfall-volume"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/snowfall-volume"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/snowfall-volume","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/snowfall-volume"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/snowfall-volume","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/snowfall-volume","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/pressure-shell

| Field | Value |
|---|---|
| Name | Pressure Shell |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 5 |
| Source identity | `weather/world.ripples` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/pressure-shell"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/pressure-shell"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/pressure-shell","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/pressure-shell"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/pressure-shell","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/pressure-shell","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/thermal-cinders

| Field | Value |
|---|---|
| Name | Thermal Cinders |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 3 |
| Source identity | `weather/thermal.embers` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Starting values read back from the engine that differ from the default in the table above: `count` = `240`.

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/thermal-cinders"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/thermal-cinders"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/thermal-cinders","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/thermal-cinders"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/thermal-cinders","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/thermal-cinders","count":100001}
```

Diagnostic: `Invalid integer parameter: count`

### weather/autumn-drift

| Field | Value |
|---|---|
| Name | Autumn Drift |
| Contract | `ParticleEmitter` |
| Profile | 0 |
| Algorithm | 0 |
| Source identity | `weather/thermal.leaves` |
| Commands | [`emitter`](#parameters-of-emitter), [`weather-author`](#parameters-of-weather-author) |

Accepted by the native library:

**Minimal emitter command**

```json
{"op":"emitter","id":1,"effect":"weather/autumn-drift"}
```

**Minimal weather-author command**

```json
{"op":"weather-author","schema":"nocturne.weather-authoring/v1","id":1,"effect":"weather/autumn-drift"}
```

**Value at the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/autumn-drift","count":100000}
```

Refused by the native library:

**Identity used on the field command of another family**

```json
{"op":"field","effect":"weather/autumn-drift"}
```

Diagnostic: `Unknown native surface field`

**Value outside the finite choices of shape**

```json
{"op":"emitter","id":1,"effect":"weather/autumn-drift","shape":"unlisted"}
```

Diagnostic: `Invalid choice: shape`

**Value above the stated maximum of count**

```json
{"op":"emitter","id":1,"effect":"weather/autumn-drift","count":100001}
```

Diagnostic: `Invalid integer parameter: count`
