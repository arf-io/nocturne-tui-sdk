# Command reference

Every command is a JSON object with an `op` field. The engine validates each value and the final state of the transaction. `undefined` means the property is optional and can be omitted; it is not a JSON value. Nested field paths describe the shape of an object, not dotted JSON keys. Where a type is abbreviated, the complete list of choices follows it. A `number` type does not accept every number: the engine also checks resource and relational rules.

Use a `batch` for commands that must apply together. The [field index](command-inventory.json) lists the same operations and types. The [field guidance](command-help.json) gives defaults and descriptions. See the [SDK contract](Contract.md) for shared behavior.

## accessibility

- **`reducedMotion`**: ``boolean | undefined``
- **`screenReader`**: ``boolean | undefined``

## ack-intent

- **`id`**: ``number``

## ack-status

- **`id`**: ``number``

## aggregate-reemit

- **`count`**: ``number``
- **`tileIndex`**: ``number``
- **`velocity`**: ``Vector3``

## area

- **`alpha`**: ``number | undefined``

  New-area default: 0.4.

  0..1 coverage.
- **`border`**: ``Border | undefined``

  New-area default: `rounded`.

  none, rounded, square, double or heavy.
- **`fadeMs`**: ``number | undefined``

  New-area default: 500.

  0..60000 milliseconds; retained notification fade timing.
- **`gapMs`**: ``number | undefined``

  New-area default: 300.

  0..60000 milliseconds; retained notification gap timing.
- **`height`**: ``number | undefined``

  New-area default: 4.

  Positive integer through 2147483647; authored cell height.
- **`hideEmpty`**: ``boolean | undefined``

  New-area default: false.

  Boolean; controls empty-area presentation rather than deleting ownership.
- **`id`**: ``number``

  New-area default: Required.

  Integer 1..65535; identifies one of the 16 area slots.
- **`layout`**: ``"ordered" | "queue" | "direct" | undefined``

  New-area default: `ordered`.

  ordered, queue or direct notification arrangement.
- **`margin`**: ``number | undefined``

  New-area default: 0.

  Integer 0..8; retained area margin setting.
- **`material`**: ``number | undefined``

  New-area default: 2.

  Integer 0..15; native material slot.
- **`padding`**: ``number | undefined``

  New-area default: 1.

  Integer 0..8; interior spacing.
- **`parent`**: ``number | undefined``

  New-area default: 0.

  Integer 0..65535; zero has no parent, otherwise the parent must exist. Self-parenting and cycles reject.
- **`speedX`**: ``number | undefined``

  New-area default: 8.

  −100..100; horizontal notification motion control.
- **`speedY`**: ``number | undefined``

  New-area default: 1.

  −30..30; vertical notification motion control.
- **`width`**: ``number | undefined``

  New-area default: 80.

  Positive integer through 2147483647; authored cell width, independent of clipping.
- **`x`**: ``number | undefined``

  New-area default: 0.

  Integer layout coordinates −2147483648..2147483647; parent offsets and negative-y anchoring affect effective geometry.
- **`y`**: ``number | undefined``

  New-area default: 0.

  Integer layout coordinates −2147483648..2147483647; parent offsets and negative-y anchoring affect effective geometry.

## atelier-style

- **`branches`**: ``number | undefined``
- **`coreMs`**: ``number | undefined``
- **`coreRadius`**: ``number | undefined``
- **`count`**: ``number | undefined``
- **`drag`**: ``number | undefined``
- **`ejecta`**: ``number | undefined``
- **`eventId`**: ``number | undefined``
- **`glitterHz`**: ``number | undefined``
- **`gravity`**: ``number | undefined``
- **`id`**: ``number``
- **`intensity`**: ``number | undefined``
- **`jaggedness`**: ``number | undefined``
- **`lifeMs`**: ``number | undefined``
- **`paint`**: ``"source" | "material" | undefined``
- **`reducedMotion`**: ``boolean | undefined``
- **`rise`**: ``number | undefined``
- **`seed`**: ``number | undefined``
- **`shockwave`**: ``number | undefined``
- **`speed`**: ``number | undefined``
- **`trailMs`**: ``number | undefined``
- **`turbulence`**: ``number | undefined``

## batch

- **`commands`**: ``readonly SceneEdit[]``

## bind

- **`binding`**: ``ValueBinding | null``

  Default: Required.

  Replacement descriptor object or explicit null to detach. Replacement immediately applies the retained value to the new target; incompatible values reject atomically. Old target property is preserved.
- **`binding.family`**: ``"widget" / "electrical-arc" / "accessibility" / "material" / "emitter" / "camera" / "window" / "area" / "text" / "floor" / "state" / "node" / "indicator" / "prompt" / "environment" / "field" / "float-body" / "surface-foam" / "mesh" / "triangle" / "cell-art" / "surface-wave" / "flow" / "surface"``

  Default: Required in descriptor.

  Native target family, with family-specific fields and value types. Choose from material, emitter, widget, camera, window, text, area, floor, state, node, indicator, prompt, environment, field, flow, surface, surface-wave, float-body, surface-foam, mesh, triangle, cell-art, accessibility or electrical-arc.
- **`binding.field`**: ``"data" / "alpha" | "speed" | "jitter" | "flicker" | "delayMs" | "holdMs" | "fadeMs" | "repeatMs" / "reducedMotion" | "screenReader" / MaterialValueField / EmitterValueField / "min" | "max" | "value" | "material" | "alpha" | "sampling" | "active" | "selected" | "x" | "y" | `data.${number}` | "backgroundMaterial" | "enabled" | "width" | "height" | "padding" | ... 7 more ... | "revealMs" / "roll" | "position.x" | "position.y" | "position.z" | "yaw" | "pitch" | "near" | "far" | "fov" | "span" | "orthographic" / "material" | "roll" | "shape" | "alpha" | "scatter" | "position.x" | "position.y" | "position.z" | "width" | "height" | "padding" | "border" | "yaw" | "pitch" | "minColumns" | ... 12 more ... | "group" / "material" | "layout" | "gapMs" | "alpha" | "parent" | "fadeMs" | "x" | "y" | "width" | "height" | "padding" | "border" | "margin" | "speedX" | "speedY" | "hideEmpty" / TextValueField / FloorValueField / "active" / "color" | "position.x" | "position.y" | "position.z" | "padding" | "minColumns" | "maxColumns" | "pinned" | "shaPrefix" | "showKind" | "showStatus" | "showSha" | "showDetail" / "material" | "area" | "cursor" | "x" | "y" | "stepMs" / "alpha" | "active" | "padding" | "mode" | "border" | "minRows" | "maxRows" / "background" | "sampling" | "stars" | "starFar" | "style" | "presentation" | "occlusionTint" | "occludedDots" / "material" | "interference" | "continuous" | "speed" | "x" | "y" | "velocity.x" | "velocity.y" | "width" | "phase" | "strength" | "lifeMs" | "rings" | "falloff" | "frequency" | "surface.x" | "surface.y" | "surface.width" | "surface.height" / "gravity" | "drag" | "radius" | "visible" | "color" | "position.x" | "position.y" | "position.z" | "velocity.x" | "velocity.y" | "velocity.z" | "mass" | "fluidDensity" | "surfaceId" | ... 5 more ... | "hull.inertia.z" / "color" | "velocity.x" | "velocity.z" | "enabled" | "sourceRate" | "curvatureThreshold" | "decay" | "impactGain" / "alpha" | "sampling" | "color" / "alpha" | "color" | "thermal.power" | "thermal.ambientTemperature" | "thermal.conductance" / "alpha" | "x" | "y" | "layer" / `waves.${number}.phase` | `waves.${number}.amplitude` | `waves.${number}.kx` | `waves.${number}.kz` | `waves.${number}.omega` / "flux" / "fadeMs" | "restitution" | "friction" | "settleSpeed" | "reentrainWindSpeed" | "maxIndividual" | "maxTiles" | "overflow" | "retentionMs" | "evaporation" | "collisionEnabled" | ... 11 more ... | "water.evaporationUs" / "sequence" / "text" / "text" | "title" / "status" | "label" | "detail" | "kind" | "sha"``

  Finite choices: ``"data"``, ``"alpha"``, ``"speed"``, ``"jitter"``, ``"flicker"``, ``"delayMs"``, ``"holdMs"``, ``"fadeMs"``, ``"repeatMs"``, ``"reducedMotion"``, ``"screenReader"``, ``"hue"``, ``"index"``, ``"lightness"``, ``"brightness"``, ``"channels.l"``, ``"channels.c"``, ``"channels.h"``, ``"channels.a"``, ``"channels.b"``, ``"channels.s"``, ``"channels.v"``, ``"channels.r"``, ``"channels.g"``, ``"channels.m"``, ``"channels.y"``, ``"channels.k"``, ``"channels.i"``, ``"alpha.min"``, ``"alpha.max"``, ``"alpha.seed"``, ``"alpha.rate"``, ``"alpha.step"``, ``"alpha.initial"``, ``"alpha.periodMs"``, ``"alpha.boundary"``, ``"alpha.easing"``, ``"hue.min"``, ``"hue.max"``, ``"hue.seed"``, ``"hue.rate"``, ``"hue.step"``, ``"hue.initial"``, ``"hue.periodMs"``, ``"hue.boundary"``, ``"hue.easing"``, ``"index.min"``, ``"index.max"``, ``"index.seed"``, ``"index.rate"``, ``"index.step"``, ``"index.initial"``, ``"index.periodMs"``, ``"index.boundary"``, ``"index.easing"``, ``"lightness.min"``, ``"lightness.max"``, ``"lightness.seed"``, ``"lightness.rate"``, ``"lightness.step"``, ``"lightness.initial"``, ``"lightness.periodMs"``, ``"lightness.boundary"``, ``"lightness.easing"``, ``"brightness.min"``, ``"brightness.max"``, ``"brightness.seed"``, ``"brightness.rate"``, ``"brightness.step"``, ``"brightness.initial"``, ``"brightness.periodMs"``, ``"brightness.boundary"``, ``"brightness.easing"``, ``"channels.l.min"``, ``"channels.l.max"``, ``"channels.l.seed"``, ``"channels.l.rate"``, ``"channels.l.step"``, ``"channels.l.initial"``, ``"channels.l.periodMs"``, ``"channels.l.boundary"``, ``"channels.l.easing"``, ``"channels.c.min"``, ``"channels.c.max"``, ``"channels.c.seed"``, ``"channels.c.rate"``, ``"channels.c.step"``, ``"channels.c.initial"``, ``"channels.c.periodMs"``, ``"channels.c.boundary"``, ``"channels.c.easing"``, ``"channels.h.min"``, ``"channels.h.max"``, ``"channels.h.seed"``, ``"channels.h.rate"``, ``"channels.h.step"``, ``"channels.h.initial"``, ``"channels.h.periodMs"``, ``"channels.h.boundary"``, ``"channels.h.easing"``, ``"channels.a.min"``, ``"channels.a.max"``, ``"channels.a.seed"``, ``"channels.a.rate"``, ``"channels.a.step"``, ``"channels.a.initial"``, ``"channels.a.periodMs"``, ``"channels.a.boundary"``, ``"channels.a.easing"``, ``"channels.b.min"``, ``"channels.b.max"``, ``"channels.b.seed"``, ``"channels.b.rate"``, ``"channels.b.step"``, ``"channels.b.initial"``, ``"channels.b.periodMs"``, ``"channels.b.boundary"``, ``"channels.b.easing"``, ``"channels.s.min"``, ``"channels.s.max"``, ``"channels.s.seed"``, ``"channels.s.rate"``, ``"channels.s.step"``, ``"channels.s.initial"``, ``"channels.s.periodMs"``, ``"channels.s.boundary"``, ``"channels.s.easing"``, ``"channels.v.min"``, ``"channels.v.max"``, ``"channels.v.seed"``, ``"channels.v.rate"``, ``"channels.v.step"``, ``"channels.v.initial"``, ``"channels.v.periodMs"``, ``"channels.v.boundary"``, ``"channels.v.easing"``, ``"channels.r.min"``, ``"channels.r.max"``, ``"channels.r.seed"``, ``"channels.r.rate"``, ``"channels.r.step"``, ``"channels.r.initial"``, ``"channels.r.periodMs"``, ``"channels.r.boundary"``, ``"channels.r.easing"``, ``"channels.g.min"``, ``"channels.g.max"``, ``"channels.g.seed"``, ``"channels.g.rate"``, ``"channels.g.step"``, ``"channels.g.initial"``, ``"channels.g.periodMs"``, ``"channels.g.boundary"``, ``"channels.g.easing"``, ``"channels.m.min"``, ``"channels.m.max"``, ``"channels.m.seed"``, ``"channels.m.rate"``, ``"channels.m.step"``, ``"channels.m.initial"``, ``"channels.m.periodMs"``, ``"channels.m.boundary"``, ``"channels.m.easing"``, ``"channels.y.min"``, ``"channels.y.max"``, ``"channels.y.seed"``, ``"channels.y.rate"``, ``"channels.y.step"``, ``"channels.y.initial"``, ``"channels.y.periodMs"``, ``"channels.y.boundary"``, ``"channels.y.easing"``, ``"channels.k.min"``, ``"channels.k.max"``, ``"channels.k.seed"``, ``"channels.k.rate"``, ``"channels.k.step"``, ``"channels.k.initial"``, ``"channels.k.periodMs"``, ``"channels.k.boundary"``, ``"channels.k.easing"``, ``"channels.i.min"``, ``"channels.i.max"``, ``"channels.i.seed"``, ``"channels.i.rate"``, ``"channels.i.step"``, ``"channels.i.initial"``, ``"channels.i.periodMs"``, ``"channels.i.boundary"``, ``"channels.i.easing"``, ``"hueStep"``, ``"spacing"``, ``"scope"``, ``"blend"``, ``"material"``, ``"count"``, ``"rate"``, ``"runningTimeMs"``, ``"cycles"``, ``"gapMs"``, ``"drag"``, ``"lift"``, ``"flutterHz"``, ``"flutterAmount"``, ``"heat"``, ``"windScale"``, ``"windPeriodSeconds"``, ``"sizeMin"``, ``"sizeMax"``, ``"radius"``, ``"topology"``, ``"trailMs"``, ``"birthFadeMs"``, ``"deathFadeMs"``, ``"coreMs"``, ``"nearDistance"``, ``"farDistance"``, ``"farFadeDistance"``, ``"veinContrast"``, ``"curl"``, ``"backTint"``, ``"twoSided"``, ``"sampling"``, ``"surfaceAlpha"``, ``"lifetimeMinMs"``, ``"lifetimeMaxMs"``, ``"tailMs"``, ``"glitterHz"``, ``"glitterDepth"``, ``"coreAlpha"``, ``"residualMs"``, ``"residualAlpha"``, ``"position.x"``, ``"position.y"``, ``"position.z"``, ``"extent.x"``, ``"extent.y"``, ``"extent.z"``, ``"velocity.x"``, ``"velocity.y"``, ``"velocity.z"``, ``"spread.x"``, ``"spread.y"``, ``"spread.z"``, ``"initialOrientation.x"``, ``"initialOrientation.y"``, ``"initialOrientation.z"``, ``"angularVelocity.x"``, ``"angularVelocity.y"``, ``"angularVelocity.z"``, ``"gravity.x"``, ``"gravity.y"``, ``"gravity.z"``, ``"wind.x"``, ``"wind.y"``, ``"wind.z"``, ``"windVariation.x"``, ``"windVariation.y"``, ``"windVariation.z"``, ``"tumble.x"``, ``"tumble.y"``, ``"tumble.z"``, ``"shapeWeights.x"``, ``"shapeWeights.y"``, ``"shapeWeights.z"``, ``"birthOrientation.x"``, ``"birthOrientation.y"``, ``"birthOrientation.z"``, ``"deposit"``, ``"collision"``, ``"windX"``, ``"windY"``, ``"windZ"``, ``"min"``, ``"max"``, ``"value"``, ``"active"``, ``"selected"``, ``"x"``, ``"y"``, ``"backgroundMaterial"``, ``"enabled"``, ``"width"``, ``"height"``, ``"padding"``, ``"mode"``, ``"pulseMs"``, ``"cellAspect"``, ``"innerRadius"``, ``"startAngle"``, ``"sweepAngle"``, ``"border"``, ``"revealMs"``, ``"roll"``, ``"yaw"``, ``"pitch"``, ``"near"``, ``"far"``, ``"fov"``, ``"span"``, ``"orthographic"``, ``"shape"``, ``"scatter"``, ``"minColumns"``, ``"maxColumns"``, ``"chromeSize"``, ``"fadeStartRatio"``, ``"fadeEndRatio"``, ``"anchorX"``, ``"anchorY"``, ``"overshoot"``, ``"bend"``, ``"folds"``, ``"meshColumns"``, ``"meshRows"``, ``"durationMs"``, ``"group"``, ``"layout"``, ``"parent"``, ``"margin"``, ``"speedX"``, ``"speedY"``, ``"hideEmpty"``, ``"wind"``, ``"easing"``, ``"batchSize"``, ``"staggerMs"``, ``"jitterMs"``, ``"distance"``, ``"variation"``, ``"scrambleHz"``, ``"hueSpread"``, ``"reverseOrder"``, ``"randomOrder"``, ``"trailLength"``, ``"local"``, ``"phase"``, ``"visible"``, ``"restitution"``, ``"friction"``, ``"settleSpeed"``, ``"reentrainWindSpeed"``, ``"maxIndividual"``, ``"maxTiles"``, ``"overflow"``, ``"retentionMs"``, ``"cellSize"``, ``"evaporation"``, ``"color"``, ``"pinned"``, ``"shaPrefix"``, ``"showKind"``, ``"showStatus"``, ``"showSha"``, ``"showDetail"``, ``"area"``, ``"cursor"``, ``"stepMs"``, ``"minRows"``, ``"maxRows"``, ``"background"``, ``"stars"``, ``"starFar"``, ``"style"``, ``"presentation"``, ``"occlusionTint"``, ``"occludedDots"``, ``"interference"``, ``"continuous"``, ``"strength"``, ``"lifeMs"``, ``"rings"``, ``"falloff"``, ``"frequency"``, ``"surface.x"``, ``"surface.y"``, ``"surface.width"``, ``"surface.height"``, ``"gravity"``, ``"mass"``, ``"fluidDensity"``, ``"surfaceId"``, ``"hull.angularVelocity.x"``, ``"hull.angularVelocity.y"``, ``"hull.angularVelocity.z"``, ``"hull.inertia.x"``, ``"hull.inertia.y"``, ``"hull.inertia.z"``, ``"sourceRate"``, ``"curvatureThreshold"``, ``"decay"``, ``"impactGain"``, ``"thermal.power"``, ``"thermal.ambientTemperature"``, ``"thermal.conductance"``, ``"layer"``, ``"flux"``, ``"collisionEnabled"``, ``"renderVisible"``, ``"wetnessGain"``, ``"heatGain"``, ``"cooling"``, ``"thermalEvaporation"``, ``"wetnessDarkening"``, ``"heatColor"``, ``"heatTintStrength"``, ``"thickness.width"``, ``"thickness.speed"``, ``"water.capacity"``, ``"water.evaporationUs"``, ``"sequence"``, ``"text"``, ``"title"``, ``"status"``, ``"label"``, ``"detail"``, ``"kind"``, ``"sha"``.

  Default: Required in descriptor.

  Exact family-specific property name, at most 31 UTF-8 bytes. Nested property names such as position.x and channels.r are literal addresses. Unknown fields or incompatible numeric/boolean/string/JSON targets reject; consult the binding references below.
- **`binding.id`**: ``number / 0 | undefined / number | undefined``

  Default: 0 when omitted.

  Target identity; family-dependent domain. Most identified resources require 1..65535, field supports 1..4294967295, and singleton families use 0. Material uses its slot domain. Camera ignores the optional ID. Omission cannot create a missing identified resource.
- **`path`**: ``string``

  Default: Required.

  Absolute value identity beginning with `/`, at most 127 UTF-8 bytes. Define rejects duplicates; bind requires an existing path. Paths identify retained application values, not files.

## brake


## burst-style

- **`coreAlpha`**: ``number | undefined``
- **`coreMs`**: ``number | undefined``
- **`glitterDepth`**: ``number | undefined``
- **`glitterHz`**: ``number | undefined``
- **`id`**: ``number``
- **`residualAlpha`**: ``number | undefined``
- **`residualMs`**: ``number | undefined``

## camera

- **`far`**: ``number | undefined``

  Native reset default: 500.

  0.01..1000000 scene units; greater than near
- **`fov`**: ``number | undefined``

  Native reset default: 65.

  10..150 degrees
- **`moveSpeed`**: ``number | undefined``
- **`navigation`**: ``"orbit" | "fly" | "pan" | undefined``
- **`near`**: ``number | undefined``

  Native reset default: 0.15.

  0.001..100 scene units
- **`orthographic`**: ``boolean | undefined``

  Native reset default: `false`.

  Boolean
- **`pitch`**: ``number | undefined``

  Native reset default: −8.

  −89.9..89.9 degrees
- **`position`**: ``Vector3 | undefined``

  Native reset default: `[0,10,48]`.

  XYZ scene units, each −16000..16000
- **`profile`**: ``"default" | "original" | undefined``
- **`roll`**: ``number | undefined``

  Native reset default: 0.

  −36000..36000 degrees
- **`sensitivity`**: ``number | undefined``
- **`span`**: ``number | undefined``

  Native reset default: 65.

  0.1..2000; orthographic projection span
- **`target`**: ``Vector3 | undefined``
- **`turnSpeed`**: ``number | undefined``
- **`yaw`**: ``number | undefined``

  Native reset default: 0.

  −36000..36000 degrees

## camera-action

- **`action`**: ``"rotate" / "move" / "dolly" / "view" / "fit"``
- **`height`**: ``number | undefined``
- **`local`**: ``Vector3``
- **`name`**: ``"front" | "back" | "left" | "right" | "top" | "bottom" | "iso"``
- **`padding`**: ``number | undefined``
- **`pitch`**: ``number | undefined``
- **`points`**: ``Vector3[] | undefined``
- **`units`**: ``number``
- **`width`**: ``number | undefined``
- **`yaw`**: ``number | undefined``

## camera-controls

- **`anchor`**: ``Vector3 | null | undefined``
- **`crane`**: ``{ pivot?: Vector3 | undefined; boom?: Vector3 | undefined; } | undefined``
- **`crane.boom`**: ``Vector3 | undefined``
- **`crane.pivot`**: ``Vector3 | undefined``
- **`enabled`**: ``true | undefined / false``
- **`follow`**: ``{ target?: CameraFollowTarget | undefined; offset?: Vector3 | undefined; track?: boolean | undefined; } | undefined``
- **`follow.offset`**: ``Vector3 | undefined``
- **`follow.target`**: ``CameraFollowTarget | undefined``
- **`follow.target.id`**: ``number``
- **`follow.target.kind`**: ``"point" / "node"``
- **`follow.target.point`**: ``Vector3``
- **`follow.track`**: ``boolean | undefined``
- **`head`**: ``{ position?: Vector3 | undefined; rotation?: Vector3 | undefined; } | undefined``
- **`head.position`**: ``Vector3 | undefined``
- **`head.rotation`**: ``Vector3 | undefined``
- **`inputAxes`**: ``{ x?: CameraInputAxis | undefined; y?: CameraInputAxis | undefined; z?: CameraInputAxis | undefined; } | undefined``
- **`inputAxes.x`**: ``CameraInputAxis | undefined``
- **`inputAxes.x.action`**: ``CameraInputAction | undefined``
- **`inputAxes.x.enabled`**: ``boolean | undefined``
- **`inputAxes.x.invert`**: ``boolean | undefined``
- **`inputAxes.x.sensitivity`**: ``number | undefined``
- **`inputAxes.y`**: ``CameraInputAxis | undefined``
- **`inputAxes.y.action`**: ``CameraInputAction | undefined``
- **`inputAxes.y.enabled`**: ``boolean | undefined``
- **`inputAxes.y.invert`**: ``boolean | undefined``
- **`inputAxes.y.sensitivity`**: ``number | undefined``
- **`inputAxes.z`**: ``CameraInputAxis | undefined``
- **`inputAxes.z.action`**: ``CameraInputAction | undefined``
- **`inputAxes.z.enabled`**: ``boolean | undefined``
- **`inputAxes.z.invert`**: ``boolean | undefined``
- **`inputAxes.z.sensitivity`**: ``number | undefined``
- **`inputTarget`**: ``"head" | "body" | undefined``
- **`mode`**: ``CameraNavigationMode | undefined``
- **`rig`**: ``CameraRig | undefined``

## camera-input

- **`delta`**: ``Vector3``
- **`pan`**: ``boolean | undefined``

## cancel

- **`id`**: ``number``

  Default or requirement: Required.

  Integer 1..65535 identifying an existing emitter.
- **`style`**: ``"settle" | "dissolve" | "gust" | "quench" | "disperse" | undefined``

  Default or requirement: Existing non-drain style; drain becomes dissolve.

  Same endings except `drain`, which rejects for cancel.
- **`tailMs`**: ``number | undefined``

  Default or requirement: Emitter's existing tail; base emitter default 3000.

  0..3600000 milliseconds; converted to retained microseconds.

## cancel-schedule

- **`id`**: ``number``

  Default: Required.

  Identity of an existing pending command. Missing identities reject; cancellation neither executes the command nor reverses earlier work.

## cell-art

- **`alpha`**: ``number | undefined``
- **`cells`**: ``readonly (readonly [number, number, number])[] | undefined``
- **`height`**: ``number | undefined``
- **`id`**: ``number``
- **`layer`**: ``"background" | "overlay" | undefined``
- **`width`**: ``number | undefined``
- **`x`**: ``number | undefined``
- **`y`**: ``number | undefined``

## character-region

- **`region`**: ``CharacterRegion``
- **`region.cells`**: ``readonly number[] | undefined``
- **`region.id`**: ``string``
- **`region.indices`**: ``readonly number[] | undefined``
- **`region.path`**: ``string``
- **`region.rect`**: ``{ x: number; y: number; width: number; height: number; } | undefined``
- **`region.rect.height`**: ``number``
- **`region.rect.width`**: ``number``
- **`region.rect.x`**: ``number``
- **`region.rect.y`**: ``number``
- **`region.role`**: ``string | undefined``
- **`region.state`**: ``string | undefined``

## character-rule

- **`rule`**: ``CharacterRule``
- **`rule.background`**: ``number | undefined``
- **`rule.backgroundBlend`**: ``CharacterBlend | undefined``
- **`rule.backgroundEffects`**: ``readonly CharacterEffect[] | undefined``
- **`rule.backgroundEffects[].type`**: ``"alpha" | "hue" | "invert" | "grayscale" | "exposure" | "contrast" | "gamma" | "posterize" | "threshold"``
- **`rule.backgroundEffects[].value`**: ``number | undefined``
- **`rule.backgroundEffects[].where`**: ``"all" | "selected" | "unselected" | undefined``
- **`rule.backgroundOpacity`**: ``number | undefined``
- **`rule.compositeSpace`**: ``"oklch" | "oklab" | "srgb" | "linear-srgb" | undefined``
- **`rule.enabled`**: ``boolean | undefined``
- **`rule.foreground`**: ``number | undefined``
- **`rule.foregroundBlend`**: ``CharacterBlend | undefined``
- **`rule.foregroundEffects`**: ``readonly CharacterEffect[] | undefined``
- **`rule.foregroundEffects[].type`**: ``"alpha" | "hue" | "invert" | "grayscale" | "exposure" | "contrast" | "gamma" | "posterize" | "threshold"``
- **`rule.foregroundEffects[].value`**: ``number | undefined``
- **`rule.foregroundEffects[].where`**: ``"all" | "selected" | "unselected" | undefined``
- **`rule.foregroundOpacity`**: ``number | undefined``
- **`rule.id`**: ``string``
- **`rule.operator`**: ``CharacterOperator | undefined``
- **`rule.priority`**: ``number | undefined``
- **`rule.protectLocalInk`**: ``boolean | undefined``
- **`rule.selector`**: ``CharacterSelector | undefined``
- **`rule.selector.glyphs`**: ``string | undefined``
- **`rule.selector.ids`**: ``readonly number[] | undefined``
- **`rule.selector.indices`**: ``readonly number[] | undefined``
- **`rule.selector.inkOnly`**: ``boolean | undefined``
- **`rule.selector.path`**: ``string | undefined``
- **`rule.selector.pathPrefix`**: ``string | undefined``
- **`rule.selector.rect`**: ``{ x: number; y: number; width: number; height: number; } | undefined``
- **`rule.selector.rect.height`**: ``number``
- **`rule.selector.rect.width`**: ``number``
- **`rule.selector.rect.x`**: ``number``
- **`rule.selector.rect.y`**: ``number``
- **`rule.selector.role`**: ``string | readonly string[] | undefined``
- **`rule.selector.state`**: ``string | readonly string[] | undefined``
- **`rule.states`**: ``Readonly<Record<string, CharacterStyle>> | undefined``

## clear

- **`scope`**: ``"text" | "status" | "deposits" | "weather" | "graph" | undefined``

  Default: `weather`.

  `weather`, `deposits`, `graph`, `text` or `status`; the selected family has the retention/rejection rules below.

## clear-deposits

- **`emitterId`**: ``number | undefined``

  Default or requirement: 0.

  Integer 0..65535; zero selects all deposits and tiles, otherwise selects their recorded emitter identity.

## clear-instance

- **`id`**: ``number``

  Default or requirement: Required.

  Existing emitter ID, integer 1..65535; an allocated flow-spray emitter rejects.

## clear-surface

- **`id`**: ``number``
- **`scope`**: ``"all" | "response" | "deposits"``

## clear-surface-foam

- **`surfaceId`**: ``number``

## corona-style

- **`durationMs`**: ``number | undefined``
- **`id`**: ``number``
- **`intensity`**: ``number | undefined``
- **`paint`**: ``"source" | "material" | undefined``
- **`speed`**: ``number | undefined``
- **`width`**: ``number | undefined``

## define

- **`binding`**: ``JsonValueBinding / NumericValueBinding | undefined / BooleanValueBinding | undefined / StringValueBinding | undefined``

  Default: Unbound when omitted.

  Binding descriptor object; initializes the target immediately. Omit this member for an unbound definition. Null detachment belongs to bind. Invalid target existence, kind or domain rejects the whole definition.
- **`binding.family`**: ``"widget" / "electrical-arc" / "accessibility" / "material" / "emitter" / "camera" / "window" / "area" / "text" / "floor" / "state" / "node" / "indicator" / "prompt" / "environment" / "field" / "float-body" / "surface-foam" / "mesh" / "triangle" / "cell-art" / "surface-wave" / "flow" / "surface"``

  Default: Required in descriptor.

  Native target family, with family-specific fields and value types. Choose from material, emitter, widget, camera, window, text, area, floor, state, node, indicator, prompt, environment, field, flow, surface, surface-wave, float-body, surface-foam, mesh, triangle, cell-art, accessibility or electrical-arc.
- **`binding.field`**: ``"data" / "alpha" | "speed" | "jitter" | "flicker" | "delayMs" | "holdMs" | "fadeMs" | "repeatMs" / "reducedMotion" | "screenReader" / MaterialValueField / EmitterValueField / "min" | "max" | "value" | "material" | "alpha" | "sampling" | "active" | "selected" | "x" | "y" | `data.${number}` | "backgroundMaterial" | "enabled" | "width" | "height" | "padding" | ... 7 more ... | "revealMs" / "roll" | "position.x" | "position.y" | "position.z" | "yaw" | "pitch" | "near" | "far" | "fov" | "span" | "orthographic" / "material" | "roll" | "shape" | "alpha" | "scatter" | "position.x" | "position.y" | "position.z" | "width" | "height" | "padding" | "border" | "yaw" | "pitch" | "minColumns" | ... 12 more ... | "group" / "material" | "layout" | "gapMs" | "alpha" | "parent" | "fadeMs" | "x" | "y" | "width" | "height" | "padding" | "border" | "margin" | "speedX" | "speedY" | "hideEmpty" / TextValueField / FloorValueField / "active" / "color" | "position.x" | "position.y" | "position.z" | "padding" | "minColumns" | "maxColumns" | "pinned" | "shaPrefix" | "showKind" | "showStatus" | "showSha" | "showDetail" / "material" | "area" | "cursor" | "x" | "y" | "stepMs" / "alpha" | "active" | "padding" | "mode" | "border" | "minRows" | "maxRows" / "background" | "sampling" | "stars" | "starFar" | "style" | "presentation" | "occlusionTint" | "occludedDots" / "material" | "interference" | "continuous" | "speed" | "x" | "y" | "velocity.x" | "velocity.y" | "width" | "phase" | "strength" | "lifeMs" | "rings" | "falloff" | "frequency" | "surface.x" | "surface.y" | "surface.width" | "surface.height" / "gravity" | "drag" | "radius" | "visible" | "color" | "position.x" | "position.y" | "position.z" | "velocity.x" | "velocity.y" | "velocity.z" | "mass" | "fluidDensity" | "surfaceId" | ... 5 more ... | "hull.inertia.z" / "color" | "velocity.x" | "velocity.z" | "enabled" | "sourceRate" | "curvatureThreshold" | "decay" | "impactGain" / "alpha" | "sampling" | "color" / "alpha" | "color" | "thermal.power" | "thermal.ambientTemperature" | "thermal.conductance" / "alpha" | "x" | "y" | "layer" / `waves.${number}.phase` | `waves.${number}.amplitude` | `waves.${number}.kx` | `waves.${number}.kz` | `waves.${number}.omega` / "flux" / "fadeMs" | "restitution" | "friction" | "settleSpeed" | "reentrainWindSpeed" | "maxIndividual" | "maxTiles" | "overflow" | "retentionMs" | "evaporation" | "collisionEnabled" | ... 11 more ... | "water.evaporationUs" / "twoSided" | "deposit" | "collision" / "active" | "selected" | "enabled" / "orthographic" / "reverseOrder" | "randomOrder" | "local" / "hideEmpty" / "visible" | "enabled" / "pinned" | "showKind" | "showStatus" | "showSha" | "showDetail" / "cursor" / "collisionEnabled" | "renderVisible" / "visible" / "continuous" / "enabled" / "sequence" / "text" / "text" | "title" / "status" | "label" | "detail" | "kind" | "sha"``

  Finite choices: ``"data"``, ``"alpha"``, ``"speed"``, ``"jitter"``, ``"flicker"``, ``"delayMs"``, ``"holdMs"``, ``"fadeMs"``, ``"repeatMs"``, ``"reducedMotion"``, ``"screenReader"``, ``"hue"``, ``"index"``, ``"lightness"``, ``"brightness"``, ``"channels.l"``, ``"channels.c"``, ``"channels.h"``, ``"channels.a"``, ``"channels.b"``, ``"channels.s"``, ``"channels.v"``, ``"channels.r"``, ``"channels.g"``, ``"channels.m"``, ``"channels.y"``, ``"channels.k"``, ``"channels.i"``, ``"alpha.min"``, ``"alpha.max"``, ``"alpha.seed"``, ``"alpha.rate"``, ``"alpha.step"``, ``"alpha.initial"``, ``"alpha.periodMs"``, ``"alpha.boundary"``, ``"alpha.easing"``, ``"hue.min"``, ``"hue.max"``, ``"hue.seed"``, ``"hue.rate"``, ``"hue.step"``, ``"hue.initial"``, ``"hue.periodMs"``, ``"hue.boundary"``, ``"hue.easing"``, ``"index.min"``, ``"index.max"``, ``"index.seed"``, ``"index.rate"``, ``"index.step"``, ``"index.initial"``, ``"index.periodMs"``, ``"index.boundary"``, ``"index.easing"``, ``"lightness.min"``, ``"lightness.max"``, ``"lightness.seed"``, ``"lightness.rate"``, ``"lightness.step"``, ``"lightness.initial"``, ``"lightness.periodMs"``, ``"lightness.boundary"``, ``"lightness.easing"``, ``"brightness.min"``, ``"brightness.max"``, ``"brightness.seed"``, ``"brightness.rate"``, ``"brightness.step"``, ``"brightness.initial"``, ``"brightness.periodMs"``, ``"brightness.boundary"``, ``"brightness.easing"``, ``"channels.l.min"``, ``"channels.l.max"``, ``"channels.l.seed"``, ``"channels.l.rate"``, ``"channels.l.step"``, ``"channels.l.initial"``, ``"channels.l.periodMs"``, ``"channels.l.boundary"``, ``"channels.l.easing"``, ``"channels.c.min"``, ``"channels.c.max"``, ``"channels.c.seed"``, ``"channels.c.rate"``, ``"channels.c.step"``, ``"channels.c.initial"``, ``"channels.c.periodMs"``, ``"channels.c.boundary"``, ``"channels.c.easing"``, ``"channels.h.min"``, ``"channels.h.max"``, ``"channels.h.seed"``, ``"channels.h.rate"``, ``"channels.h.step"``, ``"channels.h.initial"``, ``"channels.h.periodMs"``, ``"channels.h.boundary"``, ``"channels.h.easing"``, ``"channels.a.min"``, ``"channels.a.max"``, ``"channels.a.seed"``, ``"channels.a.rate"``, ``"channels.a.step"``, ``"channels.a.initial"``, ``"channels.a.periodMs"``, ``"channels.a.boundary"``, ``"channels.a.easing"``, ``"channels.b.min"``, ``"channels.b.max"``, ``"channels.b.seed"``, ``"channels.b.rate"``, ``"channels.b.step"``, ``"channels.b.initial"``, ``"channels.b.periodMs"``, ``"channels.b.boundary"``, ``"channels.b.easing"``, ``"channels.s.min"``, ``"channels.s.max"``, ``"channels.s.seed"``, ``"channels.s.rate"``, ``"channels.s.step"``, ``"channels.s.initial"``, ``"channels.s.periodMs"``, ``"channels.s.boundary"``, ``"channels.s.easing"``, ``"channels.v.min"``, ``"channels.v.max"``, ``"channels.v.seed"``, ``"channels.v.rate"``, ``"channels.v.step"``, ``"channels.v.initial"``, ``"channels.v.periodMs"``, ``"channels.v.boundary"``, ``"channels.v.easing"``, ``"channels.r.min"``, ``"channels.r.max"``, ``"channels.r.seed"``, ``"channels.r.rate"``, ``"channels.r.step"``, ``"channels.r.initial"``, ``"channels.r.periodMs"``, ``"channels.r.boundary"``, ``"channels.r.easing"``, ``"channels.g.min"``, ``"channels.g.max"``, ``"channels.g.seed"``, ``"channels.g.rate"``, ``"channels.g.step"``, ``"channels.g.initial"``, ``"channels.g.periodMs"``, ``"channels.g.boundary"``, ``"channels.g.easing"``, ``"channels.m.min"``, ``"channels.m.max"``, ``"channels.m.seed"``, ``"channels.m.rate"``, ``"channels.m.step"``, ``"channels.m.initial"``, ``"channels.m.periodMs"``, ``"channels.m.boundary"``, ``"channels.m.easing"``, ``"channels.y.min"``, ``"channels.y.max"``, ``"channels.y.seed"``, ``"channels.y.rate"``, ``"channels.y.step"``, ``"channels.y.initial"``, ``"channels.y.periodMs"``, ``"channels.y.boundary"``, ``"channels.y.easing"``, ``"channels.k.min"``, ``"channels.k.max"``, ``"channels.k.seed"``, ``"channels.k.rate"``, ``"channels.k.step"``, ``"channels.k.initial"``, ``"channels.k.periodMs"``, ``"channels.k.boundary"``, ``"channels.k.easing"``, ``"channels.i.min"``, ``"channels.i.max"``, ``"channels.i.seed"``, ``"channels.i.rate"``, ``"channels.i.step"``, ``"channels.i.initial"``, ``"channels.i.periodMs"``, ``"channels.i.boundary"``, ``"channels.i.easing"``, ``"hueStep"``, ``"spacing"``, ``"scope"``, ``"blend"``, ``"material"``, ``"count"``, ``"rate"``, ``"runningTimeMs"``, ``"cycles"``, ``"gapMs"``, ``"drag"``, ``"lift"``, ``"flutterHz"``, ``"flutterAmount"``, ``"heat"``, ``"windScale"``, ``"windPeriodSeconds"``, ``"sizeMin"``, ``"sizeMax"``, ``"radius"``, ``"topology"``, ``"trailMs"``, ``"birthFadeMs"``, ``"deathFadeMs"``, ``"coreMs"``, ``"nearDistance"``, ``"farDistance"``, ``"farFadeDistance"``, ``"veinContrast"``, ``"curl"``, ``"backTint"``, ``"twoSided"``, ``"sampling"``, ``"surfaceAlpha"``, ``"lifetimeMinMs"``, ``"lifetimeMaxMs"``, ``"tailMs"``, ``"glitterHz"``, ``"glitterDepth"``, ``"coreAlpha"``, ``"residualMs"``, ``"residualAlpha"``, ``"position.x"``, ``"position.y"``, ``"position.z"``, ``"extent.x"``, ``"extent.y"``, ``"extent.z"``, ``"velocity.x"``, ``"velocity.y"``, ``"velocity.z"``, ``"spread.x"``, ``"spread.y"``, ``"spread.z"``, ``"initialOrientation.x"``, ``"initialOrientation.y"``, ``"initialOrientation.z"``, ``"angularVelocity.x"``, ``"angularVelocity.y"``, ``"angularVelocity.z"``, ``"gravity.x"``, ``"gravity.y"``, ``"gravity.z"``, ``"wind.x"``, ``"wind.y"``, ``"wind.z"``, ``"windVariation.x"``, ``"windVariation.y"``, ``"windVariation.z"``, ``"tumble.x"``, ``"tumble.y"``, ``"tumble.z"``, ``"shapeWeights.x"``, ``"shapeWeights.y"``, ``"shapeWeights.z"``, ``"birthOrientation.x"``, ``"birthOrientation.y"``, ``"birthOrientation.z"``, ``"deposit"``, ``"collision"``, ``"windX"``, ``"windY"``, ``"windZ"``, ``"min"``, ``"max"``, ``"value"``, ``"active"``, ``"selected"``, ``"x"``, ``"y"``, ``"backgroundMaterial"``, ``"enabled"``, ``"width"``, ``"height"``, ``"padding"``, ``"mode"``, ``"pulseMs"``, ``"cellAspect"``, ``"innerRadius"``, ``"startAngle"``, ``"sweepAngle"``, ``"border"``, ``"revealMs"``, ``"roll"``, ``"yaw"``, ``"pitch"``, ``"near"``, ``"far"``, ``"fov"``, ``"span"``, ``"orthographic"``, ``"shape"``, ``"scatter"``, ``"minColumns"``, ``"maxColumns"``, ``"chromeSize"``, ``"fadeStartRatio"``, ``"fadeEndRatio"``, ``"anchorX"``, ``"anchorY"``, ``"overshoot"``, ``"bend"``, ``"folds"``, ``"meshColumns"``, ``"meshRows"``, ``"durationMs"``, ``"group"``, ``"layout"``, ``"parent"``, ``"margin"``, ``"speedX"``, ``"speedY"``, ``"hideEmpty"``, ``"wind"``, ``"easing"``, ``"batchSize"``, ``"staggerMs"``, ``"jitterMs"``, ``"distance"``, ``"variation"``, ``"scrambleHz"``, ``"hueSpread"``, ``"reverseOrder"``, ``"randomOrder"``, ``"trailLength"``, ``"local"``, ``"phase"``, ``"visible"``, ``"restitution"``, ``"friction"``, ``"settleSpeed"``, ``"reentrainWindSpeed"``, ``"maxIndividual"``, ``"maxTiles"``, ``"overflow"``, ``"retentionMs"``, ``"cellSize"``, ``"evaporation"``, ``"color"``, ``"pinned"``, ``"shaPrefix"``, ``"showKind"``, ``"showStatus"``, ``"showSha"``, ``"showDetail"``, ``"area"``, ``"cursor"``, ``"stepMs"``, ``"minRows"``, ``"maxRows"``, ``"background"``, ``"stars"``, ``"starFar"``, ``"style"``, ``"presentation"``, ``"occlusionTint"``, ``"occludedDots"``, ``"interference"``, ``"continuous"``, ``"strength"``, ``"lifeMs"``, ``"rings"``, ``"falloff"``, ``"frequency"``, ``"surface.x"``, ``"surface.y"``, ``"surface.width"``, ``"surface.height"``, ``"gravity"``, ``"mass"``, ``"fluidDensity"``, ``"surfaceId"``, ``"hull.angularVelocity.x"``, ``"hull.angularVelocity.y"``, ``"hull.angularVelocity.z"``, ``"hull.inertia.x"``, ``"hull.inertia.y"``, ``"hull.inertia.z"``, ``"sourceRate"``, ``"curvatureThreshold"``, ``"decay"``, ``"impactGain"``, ``"thermal.power"``, ``"thermal.ambientTemperature"``, ``"thermal.conductance"``, ``"layer"``, ``"flux"``, ``"collisionEnabled"``, ``"renderVisible"``, ``"wetnessGain"``, ``"heatGain"``, ``"cooling"``, ``"thermalEvaporation"``, ``"wetnessDarkening"``, ``"heatColor"``, ``"heatTintStrength"``, ``"thickness.width"``, ``"thickness.speed"``, ``"water.capacity"``, ``"water.evaporationUs"``, ``"sequence"``, ``"text"``, ``"title"``, ``"status"``, ``"label"``, ``"detail"``, ``"kind"``, ``"sha"``.

  Default: Required in descriptor.

  Exact family-specific property name, at most 31 UTF-8 bytes. Nested property names such as position.x and channels.r are literal addresses. Unknown fields or incompatible numeric/boolean/string/JSON targets reject; consult the binding references below.
- **`binding.id`**: ``number / 0 | undefined / number | undefined``

  Default: 0 when omitted.

  Target identity; family-dependent domain. Most identified resources require 1..65535, field supports 1..4294967295, and singleton families use 0. Material uses its slot domain. Camera ignores the optional ID. Omission cannot create a missing identified resource.
- **`path`**: ``string``

  Default: Required.

  Absolute value identity beginning with `/`, at most 127 UTF-8 bytes. Define rejects duplicates; bind requires an existing path. Paths identify retained application values, not files.
- **`readonly`**: ``boolean | undefined``

  Default: false.

  Boolean flag preventing subsequent set operations. Owner-controlled rebinding and explicit removal remain available.
- **`type`**: ``"json" | undefined / "number" | undefined / "boolean" | undefined / "string" | undefined / "json"``

  Default: Inferred from value; number when omitted.

  `number`, `boolean`, `string` or `json`. Fixed until removal/redefinition; explicit JSON preserves any valid JSON root.
- **`value`**: ``readonly number[] / number | undefined / boolean / string / EventPayload / readonly EventPayload[] | { readonly [key: string]: EventPayload; } | null``

  Default: 0 for number; required for other kinds.

  Initial owned value. Finite unbound number within ±1e12; boolean/string/JSON must match their declared kind and storage budgets. Bound values must also satisfy the target contract.

## dismiss

- **`id`**: ``number``

## dock-page

- **`page`**: ``number``

## draft

- **`caret`**: ``number | undefined``
- **`emitWeather`**: ``boolean | undefined``
- **`text`**: ``string``

## edge

- **`from`**: ``number``
- **`kind`**: ``"contains" | "depends" | "parent" | "reference" | "produces" | "related" | undefined``
- **`to`**: ``number``

## electrical-arc

- **`alpha`**: ``number | undefined``
- **`delayMs`**: ``number | undefined``
- **`fadeMs`**: ``number | undefined``
- **`flicker`**: ``number | undefined``
- **`holdMs`**: ``number | undefined``
- **`id`**: ``number``
- **`jitter`**: ``number | undefined``
- **`material`**: ``number | undefined``
- **`points`**: ``readonly { position: readonly [number, number, number]; parent: number; }[]``
- **`points[].parent`**: ``number``
- **`points[].position`**: ``readonly [number, number, number]``
- **`repeatMs`**: ``number | undefined``
- **`seed`**: ``number | undefined``
- **`speed`**: ``number | undefined``

## emit-intent

- **`event`**: ``string``
- **`payload`**: ``EventPayload | undefined``
- **`value`**: ``number | undefined``

## emitter

- **`alpha`**: ``number | undefined``

  Leaf default: 0.95.

  0..1
- **`angularVelocity`**: ``Vector3 | undefined``

  Leaf default: Unauthored.

  Each −720..720 degrees/second; authored motion supported for leaves/snow
- **`backTint`**: ``number | undefined``

  Leaf default: 0.3.

  0..1
- **`birthFadeMs`**: ``number | undefined``

  Leaf default: 120.

  0..60000 milliseconds
- **`birthOrientation`**: ``Vector3 | undefined``

  Leaf default: `[0,0,0]`.

  Each −3600..3600 degrees; active X, then Y, then Z rotations
- **`colliders`**: ``ColliderSelection | undefined``

  Leaf default: Default floor selection.

  Explicit object with `floor` Boolean and named surface ID array
- **`colliders.floor`**: ``boolean | undefined``
- **`colliders.surfaces`**: ``readonly number[] | undefined``
- **`collision`**: ``boolean | undefined``

  Leaf default: `true`.

  Boolean
- **`coreMs`**: ``number | undefined``

  Leaf default: 120.

  0..10000 milliseconds
- **`count`**: ``number | undefined``

  Native default: 100.

  Integer 0..100000 scheduled births; not a guarantee that this many particles fit concurrently
- **`curl`**: ``number | undefined``

  Leaf default: 0.

  −2..2
- **`cycles`**: ``number | undefined``

  Native default: 1.

  Integer 1..10000; rate-based emission requires one cycle
- **`deathFadeMs`**: ``number | undefined``

  Leaf default: 700.

  0..60000 milliseconds
- **`deposit`**: ``boolean | undefined``

  Leaf default: `true`.

  Boolean; requires collision enabled
- **`distribution`**: ``"legacy" | "uniform" | undefined``

  Leaf default: `legacy`.

  `legacy` or `uniform` shape sampling
- **`drag`**: ``number | undefined``

  Leaf default: 1.4.

  0..30; native relative-air movement coefficient
- **`effect`**: ``string | undefined``

  Native default: `weather/autumn-drift`.

  A current native particle-effect catalogue identity
- **`endStyle`**: ``EndStyle | undefined``

  Leaf default: `drain`.

  `drain`, `settle`, `dissolve`, `gust`, `quench`, `disperse`; the effect must support the selected ending
- **`extent`**: ``Vector3 | undefined``

  Leaf default: `[28,6,22]`.

  Each 0..2000; shape extent in the birth frame
- **`farDistance`**: ``number | undefined``

  Leaf default: 10000.

  0.01..10000; strictly beyond near distance
- **`farFadeDistance`**: ``number | undefined``

  Leaf default: 0.

  0..10000; no greater than far minus near distance
- **`flutterAmount`**: ``number | undefined``

  Leaf default: 0.5.

  0..10; effect-dependent flutter amount
- **`flutterHz`**: ``number | undefined``

  Leaf default: 1.4.

  0..30 cycles/second
- **`gapMs`**: ``number | undefined``

  Native default: 0.

  0..60000 milliseconds between cycles
- **`gravity`**: ``Vector3 | undefined``

  Leaf default: `[0,-4,0]`.

  Each −256..256; scene units/second²
- **`heat`**: ``number | undefined``

  Leaf default: 12.

  0..64; effect-dependent heat control
- **`id`**: ``number``

  Native default: Required.

  Integer 1..65535; unique existing emitter ownership
- **`initialOrientation`**: ``Vector3 | undefined``

  Leaf default: Unauthored.

  Each −3600..3600 degrees; authored motion supported for leaves/snow
- **`lifetimeMaxMs`**: ``number | undefined``

  Leaf default: 8000,14000.

  Minimum at least 1 ms; maximum 3600000 ms; ordered bounds
- **`lifetimeMinMs`**: ``number | undefined``

  Leaf default: 8000,14000.

  Minimum at least 1 ms; maximum 3600000 ms; ordered bounds
- **`lift`**: ``number | undefined``

  Leaf default: 0.3.

  0..20; native movement coefficient
- **`material`**: ``number | undefined``

  Leaf default: 1.

  Integer 0..15; native material slot
- **`nearDistance`**: ``number | undefined``

  Leaf default: 0.001.

  0.001..1000
- **`position`**: ``Vector3 | undefined``

  Leaf default: `[0,18,0]`.

  Each component −16000..16000; world-space pivot
- **`radius`**: ``number | undefined``

  Leaf default: 6.

  0.1..200; effect-dependent radial scale
- **`rate`**: ``number | undefined``

  Native default: 0.

  0..10000; a positive value selects rate-based emission; do not author together with `count`
- **`runningTimeMs`**: ``number | undefined``

  Native default: 8000.

  0..86400000 milliseconds; zero supports burst schedules
- **`sampling`**: ``Sampling | undefined``

  Leaf default: `braille`.

  `cell`, `half`, `braille`, `hybrid`
- **`schedule`**: ``"uniform" | "seeded-jitter" | undefined``

  Native default: `uniform`.

  `uniform` or `seeded-jitter`
- **`seed`**: ``number | undefined``

  Native default: Hash of scene seed XOR emitter ID.

  uint32; explicit seeds reproduce the configured random sequence
- **`shape`**: ``"point" | "box" | "sphere" | "disc" | "line" | undefined``

  Leaf default: `box`.

  `point`, `box`, `sphere`, `disc`, `line`
- **`shapeWeights`**: ``Vector3 | undefined``

  Leaf default: `[1,0,0]`.

  Each 0..1; sum must be positive
- **`sizeMax`**: ``number | undefined``

  Leaf default: 0.6,1.4.

  0.005..64; minimum must not exceed maximum
- **`sizeMin`**: ``number | undefined``

  Leaf default: 0.6,1.4.

  0.005..64; minimum must not exceed maximum
- **`spread`**: ``Vector3 | undefined``

  Leaf default: `[1,1,1]`.

  Each 0..128; initial velocity variation
- **`startTimeUs`**: ``number | undefined``

  Native default: Current scene time.

  Microseconds, not before the current time, within the 24-hour scene range
- **`surfaceAlpha`**: ``number | undefined``

  Leaf default: 0.22.

  0..1; leaf surface setting
- **`tailMs`**: ``number | undefined``

  Leaf default: 3000.

  0..3600000 milliseconds
- **`topology`**: ``0 | 1 | 2 | 3 | 4 | 5 | undefined``

  Leaf default: 0.

  Integer 0..5; geometry treatment, with profile-specific defaults
- **`trailMs`**: ``number | undefined``

  Leaf default: 120.

  0..2000 milliseconds
- **`tumble`**: ``Vector3 | undefined``

  Leaf default: `[45,65,90]`.

  Each −720..720; procedural rotation control
- **`twoSided`**: ``boolean | undefined``

  Leaf default: `true`.

  Boolean
- **`veinContrast`**: ``number | undefined``

  Leaf default: 0.75.

  0..1
- **`velocity`**: ``Vector3 | undefined``

  Leaf default: `[0,-1,0]`.

  Each −256..256; initial scene units/second
- **`wind`**: ``Vector3 | undefined``

  Leaf default: `[1.5,0,0.8]`.

  Each −256..256; air velocity in scene units/second
- **`windPeriodSeconds`**: ``number | undefined``

  Leaf default: 6.

  0.1..120 seconds
- **`windScale`**: ``number | undefined``

  Leaf default: 12.

  0.1..1000; spatial wind scale
- **`windVariation`**: ``Vector3 | undefined``

  Leaf default: `[0.8,0.15,1]`.

  Each 0..128; variation amplitudes

## emitter-colliders

- **`colliders`**: ``ColliderSelection``
- **`colliders.floor`**: ``boolean | undefined``
- **`colliders.surfaces`**: ``readonly number[] | undefined``
- **`id`**: ``number``

## emitter-style

- **`backTint`**: ``number | undefined``
- **`id`**: ``number``
- **`sampling`**: ``Sampling | undefined``
- **`surfaceAlpha`**: ``number | undefined``
- **`twoSided`**: ``boolean | undefined``
- **`veinContrast`**: ``number | undefined``

## environment

- **`background`**: ``number | undefined``

  Initial default: `0x111018`.

  Integer 0..16777215, packed 24-bit RGB. It supplies the solid color or base tint of the procedural palette.
- **`occludedDots`**: ``OccludedDots | undefined``

  Initial default: `hidden`.

  `hidden` or `merge`; `hidden` keeps particles behind the front one out of the cell's dots, `merge` adds their dots to it.
- **`occlusionTint`**: ``number | undefined``

  Initial default: 1.

  0..1; how strongly braille particles hidden behind the front particle in a cell tint that cell's background. 1 is the full tint, 0 shows only the scene behind them.
- **`presentation`**: ``EnvironmentPresentation | undefined``
- **`sampling`**: ``"cell" | "half" | "braille" | "hybrid" | undefined``

  Initial default: `hybrid`.

  `cell`, `half`, `braille` or `hybrid`; shared environment sampling policy. Component-specific sampling remains separate.
- **`skyDensity`**: ``number | undefined``
- **`skyExposure`**: ``number | undefined``
- **`skyRadius`**: ``number | undefined``
- **`starFar`**: ``number | undefined``

  Initial default: 150.

  20..1000 world units; star distance limit around the camera, with distance-dependent exposure/fade.
- **`starProfile`**: ``"source" | "default" | undefined``
- **`stars`**: ``number | undefined``

  Initial default: 150.

  Integer 0..2000; controls seeded star density. Zero disables star drawing. This is not a promise of that exact number of visible stars.
- **`style`**: ``"linear" | "solid" | "wave" | "plasma" | "caustic" | "contours" | undefined``

  Initial default: `solid`.

  `solid`, `linear`, `plasma`, `wave`, `caustic` or `contours`; selects the screen-space background formula.
- **`textChroma`**: ``number | undefined``
- **`textLightness`**: ``number | undefined``
- **`trailMs`**: ``number | undefined``
- **`worldSeed`**: ``number | undefined``

## export-surface-fluid

- **`surfaceId`**: ``number``

## field

- **`continuous`**: ``boolean | undefined``
- **`effect`**: ``string | undefined``
- **`falloff`**: ``number | undefined``
- **`frequency`**: ``number | undefined``
- **`interference`**: ``number | undefined``
- **`lifeMs`**: ``number | undefined``
- **`material`**: ``number | undefined``
- **`optics`**: ``"source" | "legacy" | undefined``
- **`paint`**: ``"source" | "field" | undefined``
- **`phase`**: ``number | undefined``
- **`rings`**: ``number | undefined``
- **`seed`**: ``number | undefined``
- **`speed`**: ``number | undefined``
- **`strength`**: ``number | undefined``
- **`surface`**: ``{ x: number; y: number; width: number; height: number; } | undefined``
- **`surface.height`**: ``number``
- **`surface.width`**: ``number``
- **`surface.x`**: ``number``
- **`surface.y`**: ``number``
- **`velocity`**: ``readonly [number, number] | undefined``
- **`width`**: ``number | undefined``
- **`x`**: ``number | undefined``
- **`y`**: ``number | undefined``

## flight

- **`cruise`**: ``{ speed: number; heading?: { yaw: number; pitch: number; } | undefined; }``
- **`cruise.heading`**: ``{ yaw: number; pitch: number; } | undefined``
- **`cruise.heading.pitch`**: ``number``
- **`cruise.heading.yaw`**: ``number``
- **`cruise.speed`**: ``number``
- **`orbit`**: ``{ mode?: "escape" | "falling" | "stable" | undefined; target?: Vector3 | undefined; periodSeconds?: number | undefined; radialRate?: number | undefined; bank?: number | undefined; }``
- **`orbit.bank`**: ``number | undefined``
- **`orbit.mode`**: ``"escape" | "falling" | "stable" | undefined``
- **`orbit.periodSeconds`**: ``number | undefined``
- **`orbit.radialRate`**: ``number | undefined``
- **`orbit.target`**: ``Vector3 | undefined``
- **`profile`**: ``"original" | undefined / "original"``
- **`steps`**: ``readonly MotionStep[]``
- **`steps[].bank`**: ``number | undefined``

  −85..85 degrees
- **`steps[].coordinated`**: ``boolean | undefined``

  Boolean
- **`steps[].durationMs`**: ``number``

  Positive, at most 3600000 milliseconds
- **`steps[].kind`**: ``"orbit" | "cruise" | "turn" | "climb" | "dive" | "roll" | "escape" | "falling"``
- **`steps[].pitch`**: ``number | undefined``

  −89..89 degrees
- **`steps[].radius`**: ``number | undefined``

  1..2000 scene units
- **`steps[].roll`**: ``number | undefined``

  −3600..3600 degrees
- **`steps[].speed`**: ``number | undefined``

  −100..100; movement speed control
- **`steps[].target`**: ``Vector3 | undefined``

  XYZ, each −10000..10000 scene units
- **`steps[].yaw`**: ``number | undefined``

  −3600..3600 degrees

## float-body

- **`color`**: ``number | undefined``
- **`drag`**: ``number | undefined``
- **`fluidDensity`**: ``number | undefined``
- **`gravity`**: ``number | undefined``
- **`id`**: ``number``
- **`mass`**: ``number | undefined``
- **`position`**: ``Vector3 | undefined``
- **`radius`**: ``number | undefined``
- **`surfaceId`**: ``number | undefined``
- **`velocity`**: ``Vector3 | undefined``
- **`visible`**: ``boolean | undefined``

## float-hull

- **`angularVelocity`**: ``[number, number, number] | undefined``
- **`centerOfMass`**: ``[number, number, number] | undefined``
- **`faces`**: ``[number, number, number][]``
- **`id`**: ``number``
- **`inertia`**: ``[number, number, number]``
- **`orientation`**: ``[number, number, number, number] | undefined``
- **`vertices`**: ``[number, number, number][]``

## floor

- **`alpha`**: ``number | undefined``

  Initial default: 0.15.

  0..1; opacity of the visible floor guide. Individual and aggregate deposits have their own opacity calculation.
- **`cellSize`**: ``number | undefined``

  Initial default: 3.

  0.1..100 world units; X/Z bucket size for floor aggregates and their drawn footprint.
- **`enabled`**: ``boolean | undefined``

  Initial default: true.

  Boolean; enables the floor receiver for eligible particle collisions.
- **`evaporation`**: ``number | undefined``

  Initial default: 0.04.

  0..10; wetness reduction per simulation second, clamped at zero. This is distinct from deposit expiry.
- **`fadeMs`**: ``number | undefined``

  Initial default: 0.

  0..60000 milliseconds; fade interval at the end of a nonzero retention period. Must fit within that period.
- **`friction`**: ``number | undefined``

  Initial default: 0.65.

  0..1; scales tangential bounce velocity by `1-friction`.
- **`height`**: ``number | undefined``

  Initial default: 0.

  −1000..1000 world units; horizontal collision plane and guide height.
- **`maxIndividual`**: ``number | undefined``

  Initial default: 256.

  Integer 0..512; individual-deposit limit for the floor receiver, subject to the shared scene pool.
- **`maxTiles`**: ``number | undefined``

  Initial default: 128.

  Integer 0..256; aggregate-tile limit for the floor receiver, subject to the shared scene pool.
- **`overflow`**: ``"reject-new" | "merge-to-field" | undefined``

  Initial default: `merge-to-field`.

  `reject-new` or `merge-to-field`; selects rejection or compatible aggregation when individual deposits cannot be allocated.
- **`reentrainWindSpeed`**: ``number | undefined``

  Initial default: 6.

  0..256; tangential wind magnitude above which an eligible individual deposit can return to live motion; zero disables this re-entrainment path.
- **`restitution`**: ``number | undefined``

  Initial default: 0.18.

  0..1; scales the outgoing vertical speed on bounce.
- **`retentionMs`**: ``number | undefined``

  Initial default: 0.

  0..86400000 milliseconds; zero disables timed expiry, otherwise deposits/tiles expire at their retained age limit.
- **`sampling`**: ``Sampling | undefined``

  Initial default: `half`.

  `cell`, `half`, `braille` or `hybrid`; floor presentation policy, including its aggregate drawing.
- **`settleSpeed`**: ``number | undefined``

  Initial default: 0.6.

  0..30; participates in the effect-dependent collision settling condition. It is not a universal hard speed cutoff.
- **`visible`**: ``boolean | undefined``

  Initial default: false.

  Boolean; draws the floor guide independently of whether collisions are enabled.

## flow

- **`flux`**: ``number``
- **`id`**: ``number``
- **`stages`**: ``readonly { name: string; delayUs?: number | undefined; tailUs?: number | undefined; }[]``
- **`stages[].delayUs`**: ``number | undefined``
- **`stages[].name`**: ``string``
- **`stages[].tailUs`**: ``number | undefined``

## flow-rate

- **`flux`**: ``number``
- **`id`**: ``number``

## flow-sink

- **`capacity`**: ``number``
- **`evaporationUs`**: ``number | undefined``
- **`flowId`**: ``number``
- **`fraction`**: ``number``
- **`surfaceId`**: ``number``

## flow-spray

- **`emitterId`**: ``number``
- **`flowId`**: ``number``
- **`fraction`**: ``number``
- **`particleVolume`**: ``number``

## flow-surface

- **`flowId`**: ``number``
- **`referenceFlux`**: ``number``
- **`stage`**: ``string``
- **`surfaceId`**: ``number``

## flow-thickness

- **`direction`**: ``Vector3 | undefined``
- **`maxDepth`**: ``number``
- **`speed`**: ``number``
- **`surfaceId`**: ``number``
- **`width`**: ``number``

## flow-thickness-settings

- **`speed`**: ``number | undefined / number``
- **`surfaceId`**: ``number``
- **`width`**: ``number / number | undefined``

## forces

- **`drag`**: ``number | undefined``
- **`gravity`**: ``Vector3 | undefined``
- **`heat`**: ``number | undefined``
- **`id`**: ``number``
- **`wind`**: ``Vector3 | undefined``
- **`windVariation`**: ``Vector3 | undefined``

## gather

- **`group`**: ``number | undefined``

## indicator

- **`area`**: ``number | undefined``

  Integer 0–65535; default 0
- **`cursor`**: ``boolean | undefined``

  Boolean; default false
- **`id`**: ``number``

  Required integer 1–65535; updates the same identified slot
- **`material`**: ``number | undefined``

  Integer 0–15; default 2
- **`sequence`**: ``string | undefined``

  Nonempty, at most 128 Unicode scalars; JSON default `"/|\\-"`
- **`stepMs`**: ``number | undefined``

  Positive duration, at most 60000 ms, whole-microsecond representation; default 120 ms
- **`x`**: ``number | undefined``

  Integer layout coordinates; default 0
- **`y`**: ``number | undefined``

  Integer layout coordinates; default 0

## input

- **`text`**: ``string``

## inspector-scroll

- **`rows`**: ``number``

## key

- **`alt`**: ``boolean | undefined``
- **`ctrl`**: ``boolean | undefined``
- **`key`**: ``string``
- **`meta`**: ``boolean | undefined``
- **`shift`**: ``boolean | undefined``
- **`unit`**: ``"scalar" | "grapheme" | undefined``

## kinetic-style

- **`arcJitter`**: ``number | undefined``
- **`arcReach`**: ``number | undefined``
- **`arcSegments`**: ``number | undefined``
- **`branches`**: ``number | undefined``
- **`brightness`**: ``number | undefined``
- **`coreMs`**: ``number | undefined``
- **`count`**: ``number | undefined``
- **`drag`**: ``number | undefined``
- **`emberSpread`**: ``number | undefined``
- **`eventId`**: ``number | undefined``
- **`explosionForce`**: ``number | undefined``
- **`flickerHz`**: ``number | undefined``
- **`glyphs`**: ``string | undefined``
- **`gravity`**: ``number | undefined``
- **`id`**: ``number``
- **`launchSpeed`**: ``number | undefined``
- **`lifeMs`**: ``number | undefined``
- **`paint`**: ``"source" | "material" | undefined``
- **`seed`**: ``number | undefined``
- **`shockwave`**: ``number | undefined``
- **`trailMs`**: ``number | undefined``
- **`wind`**: ``number | undefined``

## layout

- **`collision`**: ``number | undefined``
- **`damping`**: ``number | undefined``
- **`depthGap`**: ``number | undefined``
- **`dimensions`**: ``2 | 3 | undefined``
- **`edgeWeights`**: ``{ from: number; to: number; kind?: "contains" | "depends" | "parent" | "reference" | "produces" | "related" | undefined; weight: number; }[] | undefined``
- **`edgeWeights[].from`**: ``number``
- **`edgeWeights[].kind`**: ``"contains" | "depends" | "parent" | "reference" | "produces" | "related" | undefined``
- **`edgeWeights[].to`**: ``number``
- **`edgeWeights[].weight`**: ``number``
- **`iterations`**: ``number | undefined``
- **`layerGap`**: ``number | undefined``
- **`linkLength`**: ``number | undefined``
- **`mode`**: ``"radial" | "layered" | "force" | undefined``
- **`nodeGap`**: ``number | undefined``
- **`nodeSizes`**: ``{ id: number; width?: number | undefined; height?: number | undefined; }[] | undefined``
- **`nodeSizes[].height`**: ``number | undefined``
- **`nodeSizes[].id`**: ``number``
- **`nodeSizes[].width`**: ``number | undefined``
- **`orientation`**: ``"TB" | "LR" | undefined``
- **`profile`**: ``"source" | undefined``
- **`repulsion`**: ``number | undefined``
- **`seed`**: ``number | undefined``
- **`spacing`**: ``number | undefined``
- **`spring`**: ``number | undefined``
- **`sweeps`**: ``number | undefined``
- **`timeStep`**: ``number | undefined``

## look

- **`pitch`**: ``number | undefined``
- **`roll`**: ``number | undefined``
- **`yaw`**: ``number | undefined``

## material

- **`alpha`**: ``Channel | undefined``

  Scalar or track in 0–1
- **`alpha.boundary`**: ``Boundary | undefined``

  Omitted member: Retain existing boundary.

  clamp, loop, reverse, random or smooth-random; fresh alpha clamps, gradient index loops.
- **`alpha.easing`**: ``Easing | undefined``

  Omitted member: Retain existing easing.

  linear, ease-in, ease-out, smooth, smoother, sine or step; fresh tracks use linear.
- **`alpha.initial`**: ``number | undefined``

  Omitted member: Retain existing initial value.

  Target channel domain; base value at scene time zero before index offset and boundary/easing.
- **`alpha.max`**: ``number | undefined``

  Omitted member: Retain existing range.

  Target channel domain, ordered bounds; equal bounds produce the minimum constant.
- **`alpha.min`**: ``number | undefined``

  Omitted member: Retain existing range.

  Target channel domain, ordered bounds; equal bounds produce the minimum constant.
- **`alpha.periodMs`**: ``number | undefined``

  Omitted member: Retain existing period.

  Positive, at most 3600000 milliseconds, exactly representable in whole microseconds; fresh tracks use 1000 ms.
- **`alpha.rate`**: ``number | undefined``

  Omitted member: Retain existing rate.

  −10000..10000 target units per period; not necessarily units per second.
- **`alpha.seed`**: ``number | undefined``

  Omitted member: Retain existing seed.

  Integer 0..4294967295; fresh tracks use 1; supplies deterministic random-boundary values.
- **`alpha.step`**: ``number | undefined``

  Omitted member: Retain existing step.

  −10000..10000 target units per sampled index; uniform material scope uses index zero.
- **`blend`**: ``string | undefined``

  One of the named modes below
- **`channels`**: ``Record<string, Channel> | undefined``

  Space-specific scalar values or track objects
- **`colors`**: ``readonly number[] | undefined``

  1–64 integer RGB24 values, each 0–0xffffff
- **`gradient`**: ``readonly (readonly number[])[] | undefined``

  At most 16 stops, exactly three numbers per stop
- **`hueStep`**: ``number | undefined``

  −360–360 degrees of authored hue offset
- **`id`**: ``number | undefined``

  Integer 0–15; omitted ID is 0
- **`index`**: ``Channel | undefined``

  Scalar/track in −10000–10000, used for gradient sampling
- **`index.boundary`**: ``Boundary | undefined``

  Omitted member: Retain existing boundary.

  clamp, loop, reverse, random or smooth-random; fresh alpha clamps, gradient index loops.
- **`index.easing`**: ``Easing | undefined``

  Omitted member: Retain existing easing.

  linear, ease-in, ease-out, smooth, smoother, sine or step; fresh tracks use linear.
- **`index.initial`**: ``number | undefined``

  Omitted member: Retain existing initial value.

  Target channel domain; base value at scene time zero before index offset and boundary/easing.
- **`index.max`**: ``number | undefined``

  Omitted member: Retain existing range.

  Target channel domain, ordered bounds; equal bounds produce the minimum constant.
- **`index.min`**: ``number | undefined``

  Omitted member: Retain existing range.

  Target channel domain, ordered bounds; equal bounds produce the minimum constant.
- **`index.periodMs`**: ``number | undefined``

  Omitted member: Retain existing period.

  Positive, at most 3600000 milliseconds, exactly representable in whole microseconds; fresh tracks use 1000 ms.
- **`index.rate`**: ``number | undefined``

  Omitted member: Retain existing rate.

  −10000..10000 target units per period; not necessarily units per second.
- **`index.seed`**: ``number | undefined``

  Omitted member: Retain existing seed.

  Integer 0..4294967295; fresh tracks use 1; supplies deterministic random-boundary values.
- **`index.step`**: ``number | undefined``

  Omitted member: Retain existing step.

  −10000..10000 target units per sampled index; uniform material scope uses index zero.
- **`pattern`**: ``MaterialPatternOptions | null | undefined``
- **`pattern.angleMilliDegrees`**: ``number | undefined``
- **`pattern.baseRgb`**: ``number | undefined``
- **`pattern.brightnessFalloffMilli`**: ``number | undefined``
- **`pattern.brightnessMilli`**: ``number | undefined``
- **`pattern.cellAspectMilli`**: ``number | undefined``
- **`pattern.colorMode`**: ``"palette" | "hsv" | "rgb-sine" | undefined``
- **`pattern.focusMode`**: ``"none" | "row" | "column" | "radial" | "diagonal-band" | undefined``
- **`pattern.focusXQ8`**: ``number | undefined``
- **`pattern.focusYQ8`**: ``number | undefined``
- **`pattern.gradientWrap`**: ``"loop" | "mirror" | "hard-stops" | undefined``
- **`pattern.hueOffsetDegrees`**: ``number | undefined``
- **`pattern.inkRgb`**: ``number | undefined``
- **`pattern.interpolation`**: ``"linear" | "eased" | undefined``
- **`pattern.kind`**: ``"linear" | "solid" | "diagonal" | "wave" | "rotating-linear" | "plasma" | "concentric" | "moire" | "aurora" | "interference" | "chevrons" | "diamond" | undefined``
- **`pattern.motion`**: ``boolean | undefined``
- **`pattern.originXCells`**: ``number | undefined``
- **`pattern.originYCells`**: ``number | undefined``
- **`pattern.palette`**: ``readonly number[] | undefined``
- **`pattern.periodMs`**: ``number | undefined``
- **`pattern.phase1024`**: ``number | undefined``
- **`pattern.pivotXQ8`**: ``number | undefined``
- **`pattern.pivotYQ8`**: ``number | undefined``
- **`pattern.reverse`**: ``boolean | undefined``
- **`pattern.rotationMode`**: ``"fixed" | "continuous" | "pendulum" | undefined``
- **`pattern.rotationPeriodMs`**: ``number | undefined``
- **`pattern.saturationFalloffMilli`**: ``number | undefined``
- **`pattern.saturationMilli`**: ``number | undefined``
- **`pattern.scaleQ8`**: ``number | undefined``
- **`pattern.seed`**: ``number | undefined``
- **`pattern.speedFalloffMilli`**: ``number | undefined``
- **`pattern.swingMilliDegrees`**: ``number | undefined``
- **`pattern.waveAmplitudeMilli`**: ``number | undefined``
- **`scope`**: ``"uniform" | "characters" | undefined``

  uniform or characters
- **`space`**: ``ColorSpace | undefined``

  One of the eight spaces above
- **`spacing`**: ``number | undefined``

  −100–100; spatial offset for gradient sampling

## material-thermal

- **`capacity`**: ``number``
- **`conductance`**: ``number | undefined``
- **`contactFraction`**: ``number | undefined``
- **`id`**: ``number``
- **`temperature`**: ``number``

## mesh

- **`append`**: ``boolean | undefined``
- **`sampling`**: ``Sampling | undefined``
- **`subdivisions`**: ``number | undefined``
- **`triangles`**: ``readonly MeshTriangle[] | undefined``
- **`triangles[].a`**: ``Vector3``
- **`triangles[].alpha`**: ``number | undefined``
- **`triangles[].b`**: ``Vector3``
- **`triangles[].c`**: ``Vector3``
- **`triangles[].color`**: ``number | undefined``
- **`triangles[].surfaceId`**: ``number | undefined``

## mesh-style

- **`alpha`**: ``number | undefined``
- **`color`**: ``number | undefined``
- **`sampling`**: ``Sampling | undefined``
- **`triangleIndex`**: ``number``

## model-import

- **`append`**: ``boolean | undefined``
- **`coordinates`**: ``"right-handed-y-up"``
- **`materials`**: ``readonly { color: number; alpha?: number | undefined; }[]``
- **`materials[].alpha`**: ``number | undefined``
- **`materials[].color`**: ``number``
- **`sampling`**: ``Sampling | undefined``
- **`schema`**: ``"nocturne.model/v1"``
- **`transform`**: ``{ position?: Vector3 | undefined; orientation?: Vector3 | undefined; scale?: Vector3 | undefined; } | undefined``
- **`transform.orientation`**: ``Vector3 | undefined``
- **`transform.position`**: ``Vector3 | undefined``
- **`transform.scale`**: ``Vector3 | undefined``
- **`triangles`**: ``readonly { indices: readonly [number, number, number]; material: number; surfaceId?: number | undefined; }[]``
- **`triangles[].indices`**: ``readonly [number, number, number]``
- **`triangles[].material`**: ``number``
- **`triangles[].surfaceId`**: ``number | undefined``
- **`units`**: ``"meters" | "centimeters" | "millimeters"``
- **`vertices`**: ``readonly Vector3[]``

## model-view

- **`controls`**: ``SceneArtControls | undefined``
- **`controls.accent`**: ``number | undefined``
- **`controls.background`**: ``number | undefined``
- **`controls.cameraX`**: ``number | undefined``
- **`controls.cameraY`**: ``number | undefined``
- **`controls.cameraZ`**: ``number | undefined``
- **`controls.detail`**: ``0 | 1 | 2 | undefined``
- **`controls.discTilt`**: ``number | undefined``
- **`controls.flow`**: ``number | undefined``
- **`controls.fov`**: ``number | undefined``
- **`controls.ink`**: ``number | undefined``
- **`controls.pitch`**: ``number | undefined``
- **`controls.projection`**: ``0 | 1 | undefined``
- **`controls.redshift`**: ``number | undefined``
- **`controls.roll`**: ``number | undefined``
- **`controls.sampling`**: ``0 | 1 | undefined``
- **`controls.secondary`**: ``number | undefined``
- **`controls.seed`**: ``number | undefined``
- **`controls.span`**: ``number | undefined``
- **`controls.travel`**: ``number | undefined``
- **`controls.waterAlpha`**: ``number | undefined``
- **`controls.yaw`**: ``number | undefined``
- **`height`**: ``number | undefined``
- **`width`**: ``number | undefined``

## node

- **`color`**: ``number | undefined``

  New-node default: 0.

  RGB24 integer 0..16777215; zero uses automatic kind-derived renderer color.
- **`detail`**: ``string | undefined``

  New-node default: Empty.

  Up to 512 Unicode scalars of retained detail source.
- **`id`**: ``number``

  New-node default: Required.

  Integer 1..65535; stable node resource identity.
- **`kind`**: ``string | undefined``

  New-node default: Empty.

  Up to 47 UTF-8 bytes; source classification, not a reserved callback name.
- **`label`**: ``string | undefined``

  New-node default: Empty.

  Up to 256 Unicode scalars of retained label source.
- **`maxColumns`**: ``number | undefined``

  New-node default: 44.

  Integer 8..2147483647; upper card text-width control.
- **`minColumns`**: ``number | undefined``

  New-node default: 22.

  Integer 8..2147483647; must fit border/padding and not exceed maxColumns.
- **`padding`**: ``number | undefined``

  New-node default: 1.

  Integer 0..8; interior text spacing.
- **`pinned`**: ``boolean | undefined``

  New-node default: false.

  Boolean retained layout pin state.
- **`position`**: ``Vector3 | undefined``

  New-node default: Slot-dependent three-column grid.

  XYZ world coordinates, each −16000..16000; explicit placement resets the target pose.
- **`sha`**: ``string | undefined``

  New-node default: Empty.

  Up to 128 UTF-8 bytes; display metadata, not automatic object-integrity verification.
- **`shaPrefix`**: ``number | undefined``

  New-node default: 0.

  Integer 0..128; zero displays the full retained hash text, otherwise limits the displayed prefix.
- **`showDetail`**: ``boolean | undefined``

  New-node default: true.

  Boolean presentation flags; hiding a field preserves its retained source.
- **`showKind`**: ``boolean | undefined``

  New-node default: true.

  Boolean presentation flags; hiding a field preserves its retained source.
- **`showSha`**: ``boolean | undefined``

  New-node default: true.

  Boolean presentation flags; hiding a field preserves its retained source.
- **`showStatus`**: ``boolean | undefined``

  New-node default: true.

  Boolean presentation flags; hiding a field preserves its retained source.
- **`status`**: ``string | undefined``

  New-node default: Empty.

  Up to 127 UTF-8 bytes of retained status source.

## notification-action

- **`actionId`**: ``number``
- **`id`**: ``number``

## observatory-overlay

- **`enabled`**: ``false / true | undefined``
- **`fallMs`**: ``number | undefined``
- **`flatNavigation`**: ``boolean | undefined``
- **`hueStep`**: ``number | undefined``
- **`kind`**: ``"text" | "dag" | "spatial-menu" | "warp" | undefined``
- **`textHueSpeed`**: ``number | undefined``

## observatory-style

- **`durationMs`**: ``number | undefined``
- **`id`**: ``number``
- **`intensity`**: ``number | undefined``
- **`paint`**: ``"source" | "material" | undefined``
- **`seed`**: ``number | undefined``
- **`speed`**: ``number | undefined``

## paste

- **`text`**: ``string``

## path-travel

- **`closed`**: ``boolean | undefined``
- **`distance`**: ``number | undefined``
- **`id`**: ``number``
- **`mode`**: ``"clamp" | "loop" | "reverse" | undefined``
- **`points`**: ``readonly Vector3[]``
- **`speed`**: ``number | undefined``
- **`target`**: ``{ family: "camera"; id: 0; } | { family: "emitter" | "window" | "node"; id: number; }``
- **`target.family`**: ``"camera" / "emitter" | "window" | "node"``
- **`target.id`**: ``0 / number``

## pause

- **`paused`**: ``boolean``

  Default or requirement: Required by the typed interface.

  Boolean; `true` stops clock advancement, `false` permits it. At the raw native command boundary omission retains the existing value.

## pointer

- **`alt`**: ``boolean | undefined``
- **`button`**: ``0 | 1 | 2 | undefined``
- **`phase`**: ``"cancel" | "move" | "down" | "up" | undefined``
- **`shift`**: ``boolean | undefined``
- **`x`**: ``number``
- **`y`**: ``number``

## prompt

- **`accent`**: ``string | number | undefined``
- **`active`**: ``boolean | undefined``

  Prompt activation state
- **`alpha`**: ``number | undefined``

  Prompt coverage
- **`ambiguousWidth`**: ``1 | 2 | undefined``

  1 or 2 terminal cells
- **`background`**: ``string | number | undefined``
- **`border`**: ``Border | undefined``

  `none`, `rounded`, `square`, `double`, or `heavy`
- **`direction`**: ``"ltr" | "rtl" | "auto" | undefined``

  `ltr`, `rtl`, or `auto` for directional presentation
- **`foreground`**: ``string | number | undefined``
- **`huePeriodMs`**: ``number | undefined``
- **`hueSpeed`**: ``number | undefined``
- **`hueStep`**: ``number | undefined``
- **`inlineRows`**: ``number | undefined``
- **`inlineWidth`**: ``number | undefined``
- **`layout`**: ``"scalar" | "grapheme" | "bidi" | undefined``

  `scalar`, `grapheme`, or `bidi`
- **`lineNumbers`**: ``boolean | undefined``
- **`margin`**: ``number | undefined``
- **`maxChars`**: ``number | undefined``
- **`maxRows`**: ``number | undefined``

  Prompt row allocation bounds
- **`minRows`**: ``number | undefined``

  Prompt row allocation bounds
- **`mode`**: ``PromptMode | undefined``

  `marquee`, `grow`, `vim-inline`, or `vim-full`
- **`padding`**: ``number | undefined``

  Prompt interior spacing
- **`paddingX`**: ``number | undefined``
- **`paddingY`**: ``number | undefined``
- **`presentation`**: ``"compact" | "framed" | undefined``
- **`selected`**: ``boolean | undefined``
- **`selectionColor`**: ``string | number | undefined``

## prompt-appearance

- **`cursor`**: ``PromptCursorAppearance | undefined``
- **`cursor.blinkMs`**: ``number | undefined``
- **`cursor.color`**: ``string | undefined``
- **`cursor.colorMode`**: ``"fixed" | "pulse" | "cycle" | undefined``
- **`cursor.colorPeriodMs`**: ``number | undefined``
- **`cursor.duty`**: ``number | undefined``
- **`cursor.glyph`**: ``string | undefined``
- **`cursor.secondaryColor`**: ``string | undefined``
- **`cursor.shape`**: ``"half" | "braille" | "none" | "inherit" | "block" | "underline" | "bar" | "custom" | undefined``
- **`weather`**: ``PromptTypingWeather | undefined``
- **`weather.intensity`**: ``number | undefined``
- **`weather.lifeMs`**: ``number | undefined``
- **`weather.paste`**: ``"off" | "each" | "burst" | undefined``
- **`weather.speed`**: ``number | undefined``
- **`weather.style`**: ``"off" | "embers" | "sparks" | "nova" | "rain" | "snow" | "ripples" | undefined``

## prompt-source

- **`enabled`**: ``boolean | undefined``
- **`glyphs`**: ``readonly number[] | undefined``
- **`layer`**: ``PromptSourceLayer | null | undefined``
- **`layer.alpha`**: ``PromptSourceAlpha | undefined``
- **`layer.alpha.bg`**: ``number | undefined``
- **`layer.alpha.fg`**: ``number | undefined``
- **`layer.frame`**: ``"visible" | "invisible" | undefined``
- **`layer.order`**: ``0 | undefined``
- **`layer.region`**: ``PromptSourceRegion | undefined``
- **`layer.region.height`**: ``number``
- **`layer.region.widget`**: ``number``
- **`layer.region.width`**: ``number``
- **`layer.region.x`**: ``number``
- **`layer.region.y`**: ``number``
- **`layer.z`**: ``"above" | undefined``
- **`palette`**: ``readonly number[] | undefined``
- **`starPalette`**: ``readonly number[] | undefined``
- **`values`**: ``FirstPromptValues | undefined``
- **`values.angleDegrees`**: ``number | undefined``
- **`values.baseColor`**: ``number | undefined``
- **`values.baseHueDegrees`**: ``number | undefined``
- **`values.borderStyle`**: ``number | undefined``
- **`values.brightnessPermille`**: ``number | undefined``
- **`values.cellAspectPermille`**: ``number | undefined``
- **`values.colorMode`**: ``number | undefined``
- **`values.cursorMode`**: ``number | undefined``
- **`values.densityPermille`**: ``number | undefined``
- **`values.effect`**: ``number | undefined``
- **`values.focusRow`**: ``number | undefined``
- **`values.foregroundColor`**: ``number | undefined``
- **`values.glyphCount`**: ``number | undefined``
- **`values.glyphSet`**: ``number | undefined``
- **`values.gradientPeriodMs`**: ``number | undefined``
- **`values.grainPermille`**: ``number | undefined``
- **`values.hueBrightnessPermille`**: ``number | undefined``
- **`values.hueDegreesPerSecond`**: ``number | undefined``
- **`values.hueSaturationPermille`**: ``number | undefined``
- **`values.hueStepDegrees`**: ``number | undefined``
- **`values.layout`**: ``1 | undefined``
- **`values.modalOpen`**: ``number | undefined``
- **`values.motion`**: ``number | undefined``
- **`values.neighborBrightnessPermille`**: ``number | undefined``
- **`values.neighborSaturationPermille`**: ``number | undefined``
- **`values.neighborSpeedPermille`**: ``number | undefined``
- **`values.originX`**: ``number | undefined``
- **`values.originY`**: ``number | undefined``
- **`values.paletteCount`**: ``number | undefined``
- **`values.phaseDegrees`**: ``number | undefined``
- **`values.pixelMode`**: ``number | undefined``
- **`values.promptBands`**: ``number | undefined``
- **`values.saturationPermille`**: ``number | undefined``
- **`values.scaleCells`**: ``number | undefined``
- **`values.seed`**: ``number | undefined``
- **`values.selection`**: ``number | undefined``
- **`values.starAttackPermille`**: ``number | undefined``
- **`values.starDutyPermille`**: ``number | undefined``
- **`values.starFloorPermille`**: ``number | undefined``
- **`values.starPaletteCount`**: ``number | undefined``
- **`values.starPeakPermille`**: ``number | undefined``
- **`values.starPeriodMinMs`**: ``number | undefined``
- **`values.starPeriodRangeMs`**: ``number | undefined``
- **`values.stars`**: ``number | undefined``
- **`values.textScrimPermille`**: ``number | undefined``
- **`values.valuePermille`**: ``number | undefined``
- **`values.waveAmplitudePermille`**: ``number | undefined``

## purge-status

- **`id`**: ``number``

## remove-atelier-style

- **`id`**: ``number``

## remove-cell-art

- **`id`**: ``number``

## remove-character-region

- **`id`**: ``string``

## remove-character-rule

- **`id`**: ``string``

## remove-corona-style

- **`id`**: ``number``

## remove-electrical-arc

- **`id`**: ``number``

## remove-field

- **`id`**: ``number``

## remove-float-body

- **`id`**: ``number``

## remove-float-hull

- **`id`**: ``number``

## remove-flow-surface

- **`surfaceId`**: ``number``

## remove-flow-thickness

- **`surfaceId`**: ``number``

## remove-kinetic-style

- **`id`**: ``number``

## remove-material-thermal

- **`id`**: ``number``

## remove-model-view


## remove-observatory-style

- **`id`**: ``number``

## remove-path-travel

- **`id`**: ``number``

## remove-scene-art


## remove-source-stage-component

- **`id`**: ``number``

## remove-studio-style

- **`id`**: ``number``

## remove-style-rule

- **`id`**: ``number``

## remove-surface-thermal-link

- **`id`**: ``number``

## remove-surface-water-link

- **`id`**: ``number``

## remove-thermal-style

- **`id`**: ``number``

## remove-trigger

- **`id`**: ``number``

## remove-value

- **`path`**: ``string``

  Default: Required.

  Absolute identity beginning with `/`, at most 127 UTF-8 bytes. Existing trigger, style-rule or scheduled consumers prevent removal. An absent valid path is a no-op. Successful removal preserves the target component's last authored property.

## remove-window-application


## remove-window-content

- **`id`**: ``number``

## remove-window-texture

- **`id`**: ``number``

## remove-world-style

- **`id`**: ``number``

## reset

- **`preservePrompt`**: ``boolean | undefined``

  Default: false.

  Boolean; copies the existing Prompt structure back after defaults initialize.
- **`seed`**: ``number | undefined``

  Default: Current scene seed.

  Integer 0..4294967295; replaces the seed used by scene defaults.

## resize

- **`height`**: ``number``
- **`width`**: ``number``

## resume

- **`id`**: ``number``

  Default or requirement: Required.

  Integer 1..65535 identifying an existing emitter.

## ribbon

- **`alpha`**: ``number | undefined``
- **`append`**: ``boolean | undefined``
- **`closed`**: ``boolean | undefined``
- **`color`**: ``number | undefined``
- **`interpolation`**: ``"linear" | undefined / "catmull-rom"``
- **`miterLimit`**: ``number | undefined``
- **`points`**: ``readonly Vector3[]``
- **`sampling`**: ``Sampling | undefined``
- **`subdivisions`**: ``number | undefined``
- **`surfaceId`**: ``number | undefined``
- **`up`**: ``Vector3 | undefined``
- **`width`**: ``number | undefined``
- **`widths`**: ``readonly number[]``

## scene-art

- **`controls`**: ``SceneArtControls | undefined``
- **`controls.accent`**: ``number | undefined``
- **`controls.background`**: ``number | undefined``
- **`controls.cameraX`**: ``number | undefined``
- **`controls.cameraY`**: ``number | undefined``
- **`controls.cameraZ`**: ``number | undefined``
- **`controls.detail`**: ``0 | 1 | 2 | undefined``
- **`controls.discTilt`**: ``number | undefined``
- **`controls.flow`**: ``number | undefined``
- **`controls.fov`**: ``number | undefined``
- **`controls.ink`**: ``number | undefined``
- **`controls.pitch`**: ``number | undefined``
- **`controls.projection`**: ``0 | 1 | undefined``
- **`controls.redshift`**: ``number | undefined``
- **`controls.roll`**: ``number | undefined``
- **`controls.sampling`**: ``0 | 1 | undefined``
- **`controls.secondary`**: ``number | undefined``
- **`controls.seed`**: ``number | undefined``
- **`controls.span`**: ``number | undefined``
- **`controls.travel`**: ``number | undefined``
- **`controls.waterAlpha`**: ``number | undefined``
- **`controls.yaw`**: ``number | undefined``
- **`detail`**: ``SceneArtDetailControls | undefined``
- **`detail.choppiness`**: ``number | undefined``
- **`detail.crossSwell`**: ``number | undefined``
- **`detail.foam`**: ``number | undefined``
- **`detail.joinRiver`**: ``0 | 1 | undefined``
- **`detail.waveHeight`**: ``number | undefined``
- **`detail.wavelength`**: ``number | undefined``
- **`detail.waveSpeed`**: ``number | undefined``
- **`detail.windAngle`**: ``number | undefined``
- **`height`**: ``number | undefined``
- **`scene`**: ``SceneArtName | undefined``
- **`timeMs`**: ``number | null | undefined``
- **`width`**: ``number | undefined``

## schedule

- **`atUs`**: ``number``

  Default: Required.

  Absolute integer scene microseconds, 0..86400000000, at or after the current clock. Past times and fractions reject. Execution belongs to clock advancement; rendering does not fire it.
- **`command`**: ``SceneEdit | { op: "batch"; commands: readonly SceneEdit[]; }``

  Default: Required.

  Owned native command object or allowed batch, at most 4095 UTF-8 bytes. Invalid current-state dependencies and operations excluded from scheduling reject; see the transaction reference for the allowed-operation contract.
- **`id`**: ``number``

  Default: Required.

  Integer 1..65535; unique among pending commands. Reusing a pending identity rejects.

## select

- **`anchor`**: ``number | undefined``
- **`caret`**: ``number | undefined``
- **`durationMs`**: ``number | undefined``
- **`id`**: ``number``
- **`unit`**: ``"scalar" | "grapheme" | undefined``

## set

- **`expression`**: ``string | number | boolean | NumericPath | NumericIntent | NumericPayloadPath | NumericAdd | NumericSubtract | ... 26 more ... | null``

  Finite choices: ``false``, ``true``.
- **`expression.abs`**: ``NumericExpression``
- **`expression.add`**: ``NumericOperands``
- **`expression.and`**: ``DataOperands``
- **`expression.array`**: ``readonly DataExpression[]``
- **`expression.ceil`**: ``NumericExpression``
- **`expression.clamp`**: ``{ value: NumericExpression; min: NumericExpression; max: NumericExpression; }``
- **`expression.clamp.max`**: ``NumericExpression``
- **`expression.clamp.min`**: ``NumericExpression``
- **`expression.clamp.value`**: ``NumericExpression``
- **`expression.concat`**: ``DataOperands``
- **`expression.convert`**: ``{ value: NumericExpression; from: NumericUnit; to: NumericUnit; }``
- **`expression.convert.from`**: ``NumericUnit``
- **`expression.convert.to`**: ``NumericUnit``
- **`expression.convert.value`**: ``NumericExpression``
- **`expression.divide`**: ``readonly [NumericExpression, NumericExpression]``
- **`expression.equal`**: ``readonly [DataExpression, DataExpression]``
- **`expression.floor`**: ``NumericExpression``
- **`expression.greaterOrEqual`**: ``readonly [DataExpression, DataExpression]``
- **`expression.greaterThan`**: ``readonly [DataExpression, DataExpression]``
- **`expression.if`**: ``{ condition: DataExpression; then: DataExpression; else: DataExpression; }``
- **`expression.if.condition`**: ``DataExpression``
- **`expression.if.else`**: ``DataExpression``
- **`expression.if.then`**: ``DataExpression``
- **`expression.intentField`**: ``NumericIntentField``
- **`expression.intentPath`**: ``string``
- **`expression.lerp`**: ``{ from: NumericExpression; to: NumericExpression; amount: NumericExpression; }``
- **`expression.lerp.amount`**: ``NumericExpression``
- **`expression.lerp.from`**: ``NumericExpression``
- **`expression.lerp.to`**: ``NumericExpression``
- **`expression.lessOrEqual`**: ``readonly [DataExpression, DataExpression]``
- **`expression.lessThan`**: ``readonly [DataExpression, DataExpression]``
- **`expression.literal`**: ``EventPayload``
- **`expression.max`**: ``NumericOperands``
- **`expression.min`**: ``NumericOperands``
- **`expression.multiply`**: ``NumericOperands``
- **`expression.negate`**: ``NumericExpression``
- **`expression.not`**: ``DataExpression``
- **`expression.object`**: ``{ readonly [key: string]: DataExpression; }``
- **`expression.or`**: ``DataOperands``
- **`expression.path`**: ``string``
- **`expression.pointer`**: ``string | undefined``
- **`expression.remap`**: ``{ value: NumericExpression; inMin: NumericExpression; inMax: NumericExpression; outMin: NumericExpression; outMax: NumericExpression; }``
- **`expression.remap.inMax`**: ``NumericExpression``
- **`expression.remap.inMin`**: ``NumericExpression``
- **`expression.remap.outMax`**: ``NumericExpression``
- **`expression.remap.outMin`**: ``NumericExpression``
- **`expression.remap.value`**: ``NumericExpression``
- **`expression.round`**: ``NumericExpression``
- **`expression.subtract`**: ``readonly [NumericExpression, NumericExpression]``
- **`intentId`**: ``number | undefined``
- **`path`**: ``string``
- **`value`**: ``EventPayload``

## source-modal

- **`action`**: ``"push" / "edit" / "dismiss" | "clear" / "associate"``
- **`boxId`**: ``number``
- **`componentIds`**: ``readonly number[]``
- **`context`**: ``string / string | undefined``
- **`entry`**: ``SourceModalEntry``
- **`entry.atMs`**: ``number``
- **`entry.body`**: ``string``
- **`entry.dismissible`**: ``boolean``
- **`entry.id`**: ``string``
- **`entry.kind`**: ``SourceModalKind``
- **`entry.title`**: ``string``
- **`query`**: ``string | undefined``
- **`selected`**: ``number | undefined``
- **`workspace`**: ``string | undefined``

## source-stage

- **`config`**: ``SourceStageConfig | undefined``
- **`config.glyphs`**: ``readonly number[] | undefined``
- **`config.novaGlyphs`**: ``readonly number[] | undefined``
- **`config.palette`**: ``readonly number[] | undefined``
- **`config.starPalette`**: ``readonly number[] | undefined``
- **`config.values`**: ``SourceStageValues | undefined``
- **`config.values.angle`**: ``number | undefined``
- **`config.values.baseColor`**: ``number | undefined``
- **`config.values.brightness`**: ``number | undefined``
- **`config.values.brightnessFalloff`**: ``number | undefined``
- **`config.values.cellAspect`**: ``number | undefined``
- **`config.values.colorMode`**: ``0 | 1 | 2 | undefined``
- **`config.values.focusMode`**: ``0 | 1 | 2 | 3 | 4 | undefined``
- **`config.values.focusX`**: ``number | undefined``
- **`config.values.focusY`**: ``number | undefined``
- **`config.values.gradientWrap`**: ``0 | 1 | 2 | undefined``
- **`config.values.height`**: ``number | undefined``
- **`config.values.hueOffset`**: ``number | undefined``
- **`config.values.inkColor`**: ``number | undefined``
- **`config.values.interpolation`**: ``0 | 1 | undefined``
- **`config.values.motion`**: ``0 | 1 | undefined``
- **`config.values.novaChance`**: ``number | undefined``
- **`config.values.novaCycleMs`**: ``number | undefined``
- **`config.values.novaDurationMs`**: ``number | undefined``
- **`config.values.novaGlyphCount`**: ``number | undefined``
- **`config.values.originX`**: ``number | undefined``
- **`config.values.originY`**: ``number | undefined``
- **`config.values.paletteCount`**: ``number | undefined``
- **`config.values.pattern`**: ``0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | undefined``
- **`config.values.periodMs`**: ``number | undefined``
- **`config.values.phase`**: ``number | undefined``
- **`config.values.pivotX`**: ``number | undefined``
- **`config.values.pivotY`**: ``number | undefined``
- **`config.values.pixelMode`**: ``0 | 1 | 2 | 3 | undefined``
- **`config.values.quantize`**: ``0 | 1 | 2 | undefined``
- **`config.values.reverse`**: ``0 | 1 | undefined``
- **`config.values.rippleLifeMs`**: ``number | undefined``
- **`config.values.rippleOpacity`**: ``number | undefined``
- **`config.values.rippleRings`**: ``number | undefined``
- **`config.values.rippleSpeed`**: ``number | undefined``
- **`config.values.rippleWidth`**: ``number | undefined``
- **`config.values.rotationMode`**: ``0 | 1 | 2 | undefined``
- **`config.values.rotationPeriodMs`**: ``number | undefined``
- **`config.values.saturation`**: ``number | undefined``
- **`config.values.saturationFalloff`**: ``number | undefined``
- **`config.values.scale`**: ``number | undefined``
- **`config.values.seed`**: ``number | undefined``
- **`config.values.speedFalloff`**: ``number | undefined``
- **`config.values.starAttack`**: ``number | undefined``
- **`config.values.starColorCount`**: ``number | undefined``
- **`config.values.starDensity`**: ``number | undefined``
- **`config.values.starDuty`**: ``number | undefined``
- **`config.values.starGlyphCount`**: ``number | undefined``
- **`config.values.starMinMs`**: ``number | undefined``
- **`config.values.starPeak`**: ``number | undefined``
- **`config.values.starRangeMs`**: ``number | undefined``
- **`config.values.stars`**: ``0 | 1 | undefined``
- **`config.values.swing`**: ``number | undefined``
- **`config.values.waveAmplitude`**: ``number | undefined``
- **`config.values.width`**: ``number | undefined``
- **`enabled`**: ``boolean | undefined``
- **`events`**: ``readonly SourceStageImpulse[] | undefined``
- **`events[].atMs`**: ``number``
- **`events[].id`**: ``number | undefined``
- **`events[].kind`**: ``0 | 1 | undefined``
- **`events[].strength`**: ``number | undefined``
- **`events[].x`**: ``number``
- **`events[].y`**: ``number``
- **`timeMs`**: ``number | undefined``

## source-stage-component

- **`bg`**: ``number | undefined``
- **`bgOpacity`**: ``number | undefined``
- **`changedMs`**: ``number | undefined``
- **`colorAnimation`**: ``number | undefined``
- **`data`**: ``readonly number[] | undefined``
- **`durationMs`**: ``number | undefined``
- **`fg`**: ``number | undefined``
- **`fgOpacity`**: ``number | undefined``
- **`fromValue`**: ``number | undefined``
- **`glyph`**: ``number | undefined``
- **`height`**: ``number``
- **`hueBase`**: ``number | undefined``
- **`hueBrightness`**: ``number | undefined``
- **`hueSaturation`**: ``number | undefined``
- **`hueSpeed`**: ``number | undefined``
- **`hueStep`**: ``number | undefined``
- **`id`**: ``number``
- **`kind`**: ``SourceStageKind``
- **`legacyFlags`**: ``number | undefined``
- **`materialId`**: ``number | undefined``
- **`revealMs`**: ``number | undefined``
- **`state`**: ``number | undefined``
- **`style`**: ``number | undefined``
- **`text`**: ``string | undefined``
- **`value`**: ``number | undefined``
- **`width`**: ``number``
- **`x`**: ``number | undefined``
- **`y`**: ``number | undefined``
- **`zoom`**: ``number | undefined``

## state-register

- **`active`**: ``boolean | undefined``
- **`id`**: ``number``
- **`path`**: ``string``
- **`role`**: ``string``
- **`target`**: ``StateTarget``
- **`target.family`**: ``IdentifiedStyleFamily / SingletonStyleFamily``
- **`target.id`**: ``number / 0``

## state-unregister

- **`id`**: ``number``

## state-update

- **`active`**: ``boolean | undefined``
- **`id`**: ``number``
- **`role`**: ``string | undefined``

## status

- **`actions`**: ``readonly NotificationAction[] | undefined``

  At most four uniquely identified action records
- **`actions[].dismiss`**: ``boolean | undefined``
- **`actions[].event`**: ``string``
- **`actions[].id`**: ``number``
- **`actions[].label`**: ``string``
- **`actions[].value`**: ``number | undefined``
- **`area`**: ``number | undefined``

  Owning layout/clipping area
- **`coalesce`**: ``"count" | "none" | "replace-queued" | undefined``

  none, count, replace-queued; default none; merging requires a nonempty key
- **`durationMs`**: ``number | undefined``

  Fixed dwell; default 6000 ms; zero prevents automatic expiry
- **`dwellPerCharacterMs`**: ``number | undefined``

  Integer 0–60000 ms per retained scalar
- **`id`**: ``number | undefined``

  Optional explicit message identity
- **`important`**: ``boolean | undefined``

  Default false; important history requires explicit acknowledgment
- **`key`**: ``string | undefined``

  Optional grouping key, at most 63 UTF-8 bytes, scoped to area
- **`maxDurationMs`**: ``number | undefined``

  Derived-dwell bounds; defaults 1000 and 60000 ms; each 0–86400000 ms
- **`minDurationMs`**: ``number | undefined``

  Derived-dwell bounds; defaults 1000 and 60000 ms; each 0–86400000 ms
- **`mode`**: ``StatusMode | undefined``

  static, horizontal, vertical, fade, pop, horizontal-fade, vertical-fade; default static
- **`priority`**: ``number | undefined``

  Integer 0–100; chooses next queued record, not preemption
- **`startTimeUs`**: ``number | undefined``

  Exact integer native timestamp, 0–86400000000; defaults to current time
- **`text`**: ``string``

  Required retained message source
- **`x`**: ``number | undefined``

  Area-relative layout placement
- **`y`**: ``number | undefined``

  Area-relative layout placement

## stop

- **`id`**: ``number``

  Default or requirement: Required.

  Integer 1..65535 identifying an existing emitter.
- **`style`**: ``EndStyle | undefined``

  Default or requirement: Emitter's existing end style.

  `drain`, `settle`, `dissolve`, `gust`, `quench` or `disperse`; the effect must support the selected ending.
- **`tailMs`**: ``number | undefined``

  Default or requirement: Emitter's existing tail; base emitter default 3000.

  0..3600000 milliseconds; converted to retained microseconds.

## stop-surface-fluid

- **`surfaceId`**: ``number``

## studio-style

- **`cellAspect`**: ``number | undefined``
- **`glyphs`**: ``string | undefined``
- **`id`**: ``number``
- **`novaDurationMs`**: ``number | undefined``
- **`paint`**: ``"source" | "material" | undefined``
- **`palette`**: ``number[] | undefined``
- **`rippleOpacity`**: ``number | undefined``
- **`rippleRings`**: ``number | undefined``
- **`rippleSpeed`**: ``number | undefined``
- **`rippleWidth`**: ``number | undefined``
- **`seed`**: ``number | undefined``
- **`starPalette`**: ``number[] | undefined``
- **`strength`**: ``number | undefined``
- **`waveScale`**: ``number | undefined``

## style-rule

- **`enabled`**: ``boolean | undefined``
- **`id`**: ``number``
- **`priority`**: ``number | undefined``
- **`selector`**: ``StateSelector<"electrical-arc"> / StateSelector<"widget"> / StateSelector<"window"> / StateSelector<"emitter"> / StateSelector<"text"> / StateSelector<"area"> / StateSelector<"indicator"> / StateSelector<"node"> / StateSelector<"floor"> / StateSelector<"mesh"> / StateSelector<"prompt">``
- **`selector.family`**: ``"electrical-arc" / "widget" / "window" / "emitter" / "text" / "area" / "indicator" / "node" / "floor" / "mesh" / "prompt"``
- **`selector.id`**: ``number | undefined / 0 | undefined``
- **`selector.path`**: ``string``
- **`selector.pathPrefix`**: ``string | undefined``
- **`selector.role`**: ``string | undefined``
- **`selector.states`**: ``Partial<StateFlags> | undefined``
- **`selector.states.active`**: ``boolean | undefined``
- **`selector.states.disabled`**: ``boolean | undefined``
- **`selector.states.hover`**: ``boolean | undefined``
- **`selector.states.pressed`**: ``boolean | undefined``
- **`selector.states.selected`**: ``boolean | undefined``
- **`style`**: ``WindowAppearance / WidgetAppearance / EmitterAppearance / { material?: number | undefined; } / { color?: number | undefined; } / { alpha?: AppearanceScalar | undefined; sampling?: Sampling | undefined; } / { alpha?: AppearanceScalar | undefined; sampling?: Sampling | undefined; color?: number | undefined; } / { alpha?: AppearanceScalar | undefined; }``
- **`style.alpha`**: ``AppearanceScalar | undefined``
- **`style.alpha.inputMax`**: ``number``
- **`style.alpha.inputMin`**: ``number``
- **`style.alpha.outputMax`**: ``number``
- **`style.alpha.outputMin`**: ``number``
- **`style.alpha.path`**: ``string``
- **`style.backgroundMaterial`**: ``number | undefined``
- **`style.color`**: ``number | undefined``
- **`style.material`**: ``number | undefined``
- **`style.sampling`**: ``Sampling | "inherit" | undefined / Sampling | undefined``
- **`style.surfaceAlpha`**: ``AppearanceScalar | undefined``
- **`style.surfaceAlpha.inputMax`**: ``number``
- **`style.surfaceAlpha.inputMin`**: ``number``
- **`style.surfaceAlpha.outputMax`**: ``number``
- **`style.surfaceAlpha.outputMin`**: ``number``
- **`style.surfaceAlpha.path`**: ``string``
- **`style.veinContrast`**: ``AppearanceScalar | undefined``
- **`style.veinContrast.inputMax`**: ``number``
- **`style.veinContrast.inputMin`**: ``number``
- **`style.veinContrast.outputMax`**: ``number``
- **`style.veinContrast.outputMin`**: ``number``
- **`style.veinContrast.path`**: ``string``
- **`when`**: ``AppearanceCondition | undefined``
- **`when.all`**: ``readonly ({ all: readonly (... | { any: readonly (... | ... | { not: ... | ... | ... | { path: string; comparison: "equal" | "above" | "below" | "not-equal" | "at-least" | "at-most"; value: number; hysteresis?: number | undefined; } | { ...; }; } | { ...; } | { ...; })[]; } | { ...; } | { ...; } | { ...; })[]; } | {...``
- **`when.any`**: ``readonly ({ all: readonly (... | { any: readonly (... | ... | { not: ... | ... | ... | { path: string; comparison: "equal" | "above" | "below" | "not-equal" | "at-least" | "at-most"; value: number; hysteresis?: number | undefined; } | { ...; }; } | { ...; } | { ...; })[]; } | { ...; } | { ...; } | { ...; })[]; } | {...``
- **`when.comparison`**: ``"equal" | "above" | "below" | "not-equal" | "at-least" | "at-most" / "between"``
- **`when.hysteresis`**: ``number | undefined``
- **`when.max`**: ``number``
- **`when.min`**: ``number``
- **`when.not`**: ``{ all: readonly (... | { any: readonly (... | ... | { not: ... | ... | ... | { path: string; comparison: "equal" | "above" | "below" | "not-equal" | "at-least" | "at-most"; value: number; hysteresis?: number | undefined; } | { ...; }; } | { ...; } | { ...; })[]; } | { ...; } | { ...; } | { ...; })[]; } | { ...; } | ...``
- **`when.path`**: ``string``
- **`when.value`**: ``number``
- **`whenExpression`**: ``AppearanceExpression``
- **`whenExpression.abs`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.add`**: ``readonly [number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }, number | ... 15 more ... | { ...; }, .....``
- **`whenExpression.and`**: ``readonly [string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null, string | ... 31 more ... | null, ...(string | ... 31 more ... |...``
- **`whenExpression.array`**: ``readonly (string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null)[]``
- **`whenExpression.ceil`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.clamp`**: ``{ value: number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }; min: number | ... 15 more ... | { ...; }...``
- **`whenExpression.clamp.max`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.clamp.min`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.clamp.value`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.concat`**: ``readonly [string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null, string | ... 31 more ... | null, ...(string | ... 31 more ... |...``
- **`whenExpression.convert`**: ``{ value: number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }; from: NumericUnit; to: NumericUnit; }``
- **`whenExpression.convert.from`**: ``NumericUnit``
- **`whenExpression.convert.to`**: ``NumericUnit``
- **`whenExpression.convert.value`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.divide`**: ``readonly [number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }, number | ... 15 more ... | { ...; }]``
- **`whenExpression.equal`**: ``readonly [string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null, string | ... 31 more ... | null]``
- **`whenExpression.floor`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.greaterOrEqual`**: ``readonly [string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null, string | ... 31 more ... | null]``
- **`whenExpression.greaterThan`**: ``readonly [string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null, string | ... 31 more ... | null]``
- **`whenExpression.if`**: ``{ condition: string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null; then: string | ... 31 more ... | null; else: string | ... 31...``
- **`whenExpression.if.condition`**: ``string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null``

  Finite choices: ``false``, ``true``.
- **`whenExpression.if.else`**: ``string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null``

  Finite choices: ``false``, ``true``.
- **`whenExpression.if.then`**: ``string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null``

  Finite choices: ``false``, ``true``.
- **`whenExpression.lerp`**: ``{ from: number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }; to: number | ... 15 more ... | { ...; }; ...``
- **`whenExpression.lerp.amount`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.lerp.from`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.lerp.to`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.lessOrEqual`**: ``readonly [string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null, string | ... 31 more ... | null]``
- **`whenExpression.lessThan`**: ``readonly [string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null, string | ... 31 more ... | null]``
- **`whenExpression.literal`**: ``EventPayload``
- **`whenExpression.max`**: ``readonly [number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }, number | ... 15 more ... | { ...; }, .....``
- **`whenExpression.min`**: ``readonly [number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }, number | ... 15 more ... | { ...; }, .....``
- **`whenExpression.multiply`**: ``readonly [number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }, number | ... 15 more ... | { ...; }, .....``
- **`whenExpression.negate`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.not`**: ``string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null``

  Finite choices: ``false``, ``true``.
- **`whenExpression.object`**: ``{ readonly [x: string]: string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null; }``
- **`whenExpression.or`**: ``readonly [string | number | boolean | DataLiteral | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; ... 25 more ...; convert?: undefined; } | ... 27 more ... | null, string | ... 31 more ... | null, ...(string | ... 31 more ... |...``
- **`whenExpression.path`**: ``string``
- **`whenExpression.pointer`**: ``string | undefined``
- **`whenExpression.remap`**: ``{ value: number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }; inMin: number | ... 15 more ... | { ...;...``
- **`whenExpression.remap.inMax`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.remap.inMin`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.remap.outMax`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.remap.outMin`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.remap.value`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.round`**: ``number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }``
- **`whenExpression.subtract`**: ``readonly [number | { path: string; pointer?: string | undefined; object?: undefined; intentField?: undefined; intentPath?: undefined; literal?: undefined; concat?: undefined; and?: undefined; or?: undefined; ... 22 more ...; convert?: undefined; } | ... 14 more ... | { ...; }, number | ... 15 more ... | { ...; }]``

## surface

- **`collisionEnabled`**: ``boolean | undefined``

  Default: true.

  Contact-query admission
- **`cooling`**: ``number | undefined``

  Default: 0.1.

  0–10; normalized heat loss per second
- **`evaporation`**: ``number | undefined``

  Default: 0.04.

  0–10; normalized wetness loss per second
- **`fadeMs`**: ``number | undefined``

  Default: 0.

  0–60000 ms; cannot exceed nonzero retention
- **`friction`**: ``number | undefined``

  Default: 0.65.

  0–1; tangential velocity loss
- **`heatColor`**: ``number | undefined``

  Default: 0xff8844.

  RGB24 integer
- **`heatGain`**: ``number | undefined``

  Default: 0.02.

  0–10; normalized heat response gain
- **`heatTintStrength`**: ``number | undefined``

  Default: 0.4.

  0–1; color tint at full heat
- **`id`**: ``number``

  Default: required.

  Integer 1–16
- **`maxIndividual`**: ``number | undefined``

  Default: 256.

  Integer 0–512; deposit admission
- **`maxTiles`**: ``number | undefined``

  Default: 128.

  Integer 0–256; aggregate admission
- **`overflow`**: ``"reject-new" | "merge-to-field" | undefined``

  Default: merge-to-field.

  merge-to-field or reject-new
- **`reentrainWindSpeed`**: ``number | undefined``

  Default: 6.

  0–256; tangential wind threshold, zero disables
- **`renderVisible`**: ``boolean | undefined``

  Default: true.

  Assigned mesh visibility
- **`restitution`**: ``number | undefined``

  Default: 0.18.

  0–1; reflected normal velocity fraction
- **`retentionMs`**: ``number | undefined``

  Default: 0.

  0–86400000 ms; zero retains until clear
- **`settleSpeed`**: ``number | undefined``

  Default: 0.6.

  0–30; contact settle control
- **`thermalEvaporation`**: ``number | undefined``

  Default: 0.25.

  0–10; extra wetness loss per heat unit
- **`wetnessDarkening`**: ``number | undefined``

  Default: 0.35.

  0–1; darkening at full wetness
- **`wetnessGain`**: ``number | undefined``

  Default: 0.03.

  0–10; normalized response gain

## surface-fluid

- **`mass`**: ``number``
- **`surfaceId`**: ``number``
- **`velocity`**: ``Vector3 | undefined``

## surface-fluid-angular

- **`inertia`**: ``number``
- **`omega`**: ``Vector3 | undefined``
- **`orientation`**: ``readonly [number, number, number, number] | undefined``
- **`pivot`**: ``Vector3 | undefined``
- **`surfaceId`**: ``number``

## surface-foam

- **`color`**: ``number | undefined``
- **`curvatureThreshold`**: ``number | undefined``
- **`decay`**: ``number | undefined``
- **`enabled`**: ``boolean | undefined``
- **`impactGain`**: ``number | undefined``
- **`sourceRate`**: ``number | undefined``
- **`surfaceId`**: ``number``

## surface-foam-transport

- **`surfaceId`**: ``number``
- **`velocity`**: ``[number, number]``

## surface-thermal

- **`ambientTemperature`**: ``number | undefined``
- **`capacity`**: ``number``
- **`conductance`**: ``number | undefined``
- **`power`**: ``number | undefined``
- **`temperature`**: ``number``
- **`triangleIndex`**: ``number``

## surface-thermal-link

- **`conductance`**: ``number``
- **`fromTriangle`**: ``number``
- **`id`**: ``number``
- **`toTriangle`**: ``number``

## surface-thermal-power

- **`power`**: ``number``
- **`triangleIndex`**: ``number``

## surface-thermal-settings

- **`ambientTemperature`**: ``number | undefined / number``
- **`conductance`**: ``number | undefined / number``
- **`power`**: ``number | undefined / number``
- **`triangleIndex`**: ``number``

## surface-thermal-transfer

- **`energy`**: ``number``
- **`fromTriangle`**: ``number``
- **`toTriangle`**: ``number``

## surface-water

- **`capacity`**: ``number``
- **`evaporationUs`**: ``number | undefined``
- **`surfaceId`**: ``number``

## surface-water-add

- **`triangleIndex`**: ``number``
- **`volume`**: ``number``

## surface-water-link

- **`fromTriangle`**: ``number``
- **`heatCapacityPerVolume`**: ``number | undefined``
- **`id`**: ``number``
- **`rate`**: ``number``
- **`toTriangle`**: ``number``

## surface-water-reemit

- **`emitterId`**: ``number``
- **`triangleIndex`**: ``number``
- **`volume`**: ``number``

## surface-water-settings

- **`capacity`**: ``number | undefined / number``
- **`evaporationUs`**: ``number | undefined / number``
- **`surfaceId`**: ``number``

## surface-water-thermal

- **`latentHeatPerVolume`**: ``number``
- **`triangleIndex`**: ``number``

## surface-water-transfer

- **`fromTriangle`**: ``number``
- **`heatCapacityPerVolume`**: ``number | undefined``
- **`toTriangle`**: ``number``
- **`volume`**: ``number``

## surface-waves

- **`surfaceId`**: ``number``
- **`waves`**: ``readonly WaveRow[]``

## text

- **`alphabet`**: ``string | undefined``

  1–256 printable Unicode scalars for substitutions
- **`batchSize`**: ``number | undefined``

  Integer 1–128
- **`cycles`**: ``number | undefined``

  0–50
- **`delayMs`**: ``number | undefined``

  Start delay, 0–60000 ms
- **`distance`**: ``number | undefined``

  0–100
- **`durationMs`**: ``number | undefined``

  Treatment duration, 0–60000 ms
- **`easing`**: ``"back" | Easing | "cubic" | "bounce" | undefined``

  linear, ease-in, ease-out, smooth, smoother, sine, step, cubic, back, bounce
- **`effect`**: ``string | undefined``

  Exact text-family catalogue identity; unknown/wrong-family names reject
- **`hueSpread`**: ``number | undefined``

  −360–360 degrees
- **`id`**: ``number``

  Required integer 1–65535; caller-reserved text resource
- **`jitterMs`**: ``number | undefined``

  Authored progression jitter, 0–10000 ms
- **`local`**: ``boolean | undefined``

  Boolean local presentation option
- **`material`**: ``number | undefined``

  Integer 0–15
- **`overshoot`**: ``number | undefined``

  0–3
- **`phase`**: ``"show" | "hide" | undefined``

  show or hide
- **`phaseModel`**: ``"source" | "reverse-show" | "source-paint" | undefined``
- **`randomOrder`**: ``boolean | undefined``

  Boolean seeded random progression order
- **`reverseOrder`**: ``boolean | undefined``

  Boolean reverse progression order
- **`scatter`**: ``number | undefined``

  0–120
- **`scrambleHz`**: ``number | undefined``

  0–120 Hz
- **`seed`**: ``number | undefined``

  Unsigned 32-bit integer, including 0 and 4294967295
- **`staggerMs`**: ``number | undefined``

  Per-glyph progression offset, 0–10000 ms
- **`text`**: ``string | undefined``

  Retained Unicode source within native text capacity
- **`trailLength`**: ``number | undefined``

  Integer 0–8
- **`variation`**: ``number | undefined``

  0–2
- **`width`**: ``number | undefined``

  Positive integer layout width
- **`wind`**: ``number | undefined``

  −100–100
- **`x`**: ``number | undefined``

  Integer layout coordinates
- **`y`**: ``number | undefined``

  Integer layout coordinates

## thermal-style

- **`id`**: ``number``
- **`lifeMs`**: ``number | undefined``
- **`paint`**: ``"source" | "material" | undefined``
- **`seed`**: ``number | undefined``

## time

- **`budget`**: ``number | undefined``

  Default or requirement: 240.

  Integer 1..4096; maximum simulation steps for this command.
- **`timeUs`**: ``number``

  Default or requirement: Existing target at the raw boundary.

  Integer microseconds, 0..86400000000, at least the current scene time. Supply an explicit target in application code.

## trigger

- **`action`**: ``"set" | "increment" | undefined``
- **`comparison`**: ``"equal" | "above" | "below" | undefined``
- **`cooldownMs`**: ``number | undefined``
- **`debounceMs`**: ``number | undefined``
- **`edge`**: ``"falling" | "rising" | "change" | "level" | undefined``
- **`event`**: ``string | undefined``
- **`expression`**: ``string | number | boolean | NumericPath | NumericIntent | NumericPayloadPath | NumericAdd | NumericSubtract | ... 26 more ... | null``

  Finite choices: ``false``, ``true``.
- **`expression.abs`**: ``NumericExpression``
- **`expression.add`**: ``NumericOperands``
- **`expression.and`**: ``DataOperands``
- **`expression.array`**: ``readonly DataExpression[]``
- **`expression.ceil`**: ``NumericExpression``
- **`expression.clamp`**: ``{ value: NumericExpression; min: NumericExpression; max: NumericExpression; }``
- **`expression.clamp.max`**: ``NumericExpression``
- **`expression.clamp.min`**: ``NumericExpression``
- **`expression.clamp.value`**: ``NumericExpression``
- **`expression.concat`**: ``DataOperands``
- **`expression.convert`**: ``{ value: NumericExpression; from: NumericUnit; to: NumericUnit; }``
- **`expression.convert.from`**: ``NumericUnit``
- **`expression.convert.to`**: ``NumericUnit``
- **`expression.convert.value`**: ``NumericExpression``
- **`expression.divide`**: ``readonly [NumericExpression, NumericExpression]``
- **`expression.equal`**: ``readonly [DataExpression, DataExpression]``
- **`expression.floor`**: ``NumericExpression``
- **`expression.greaterOrEqual`**: ``readonly [DataExpression, DataExpression]``
- **`expression.greaterThan`**: ``readonly [DataExpression, DataExpression]``
- **`expression.if`**: ``{ condition: DataExpression; then: DataExpression; else: DataExpression; }``
- **`expression.if.condition`**: ``DataExpression``
- **`expression.if.else`**: ``DataExpression``
- **`expression.if.then`**: ``DataExpression``
- **`expression.intentField`**: ``NumericIntentField``
- **`expression.intentPath`**: ``string``
- **`expression.lerp`**: ``{ from: NumericExpression; to: NumericExpression; amount: NumericExpression; }``
- **`expression.lerp.amount`**: ``NumericExpression``
- **`expression.lerp.from`**: ``NumericExpression``
- **`expression.lerp.to`**: ``NumericExpression``
- **`expression.lessOrEqual`**: ``readonly [DataExpression, DataExpression]``
- **`expression.lessThan`**: ``readonly [DataExpression, DataExpression]``
- **`expression.literal`**: ``EventPayload``
- **`expression.max`**: ``NumericOperands``
- **`expression.min`**: ``NumericOperands``
- **`expression.multiply`**: ``NumericOperands``
- **`expression.negate`**: ``NumericExpression``
- **`expression.not`**: ``DataExpression``
- **`expression.object`**: ``{ readonly [key: string]: DataExpression; }``
- **`expression.or`**: ``DataOperands``
- **`expression.path`**: ``string``
- **`expression.pointer`**: ``string | undefined``
- **`expression.remap`**: ``{ value: NumericExpression; inMin: NumericExpression; inMax: NumericExpression; outMin: NumericExpression; outMax: NumericExpression; }``
- **`expression.remap.inMax`**: ``NumericExpression``
- **`expression.remap.inMin`**: ``NumericExpression``
- **`expression.remap.outMax`**: ``NumericExpression``
- **`expression.remap.outMin`**: ``NumericExpression``
- **`expression.remap.value`**: ``NumericExpression``
- **`expression.round`**: ``NumericExpression``
- **`expression.subtract`**: ``readonly [NumericExpression, NumericExpression]``
- **`hysteresis`**: ``number | undefined``
- **`id`**: ``number``
- **`source`**: ``string``
- **`target`**: ``string``
- **`threshold`**: ``number | undefined``
- **`value`**: ``number | undefined``
- **`valueFrom`**: ``"intentValue"``
- **`when`**: ``ValueCondition``
- **`when.all`**: ``readonly ValueCondition[]``
- **`when.any`**: ``readonly ValueCondition[]``
- **`when.comparison`**: ``"equal" | "above" | "below" | "not-equal" | "at-least" | "at-most" / "between"``
- **`when.hysteresis`**: ``number | undefined``
- **`when.intentValue`**: ``{ comparison: "equal" | "above" | "below" | "not-equal" | "at-least" | "at-most"; value: number; hysteresis?: 0 | undefined; } / { comparison: "between"; min: number; max: number; hysteresis?: 0 | undefined; }``
- **`when.intentValue.comparison`**: ``"equal" | "above" | "below" | "not-equal" | "at-least" | "at-most" / "between"``
- **`when.intentValue.hysteresis`**: ``0 | undefined``
- **`when.intentValue.max`**: ``number``
- **`when.intentValue.min`**: ``number``
- **`when.intentValue.value`**: ``number``
- **`when.max`**: ``number``
- **`when.min`**: ``number``
- **`when.not`**: ``ValueCondition``
- **`when.path`**: ``string``
- **`when.value`**: ``number``
- **`whenExpression`**: ``DataExpression``
- **`whenExpression.abs`**: ``NumericExpression``
- **`whenExpression.add`**: ``NumericOperands``
- **`whenExpression.and`**: ``DataOperands``
- **`whenExpression.array`**: ``readonly DataExpression[]``
- **`whenExpression.ceil`**: ``NumericExpression``
- **`whenExpression.clamp`**: ``{ value: NumericExpression; min: NumericExpression; max: NumericExpression; }``
- **`whenExpression.clamp.max`**: ``NumericExpression``
- **`whenExpression.clamp.min`**: ``NumericExpression``
- **`whenExpression.clamp.value`**: ``NumericExpression``
- **`whenExpression.concat`**: ``DataOperands``
- **`whenExpression.convert`**: ``{ value: NumericExpression; from: NumericUnit; to: NumericUnit; }``
- **`whenExpression.convert.from`**: ``NumericUnit``
- **`whenExpression.convert.to`**: ``NumericUnit``
- **`whenExpression.convert.value`**: ``NumericExpression``
- **`whenExpression.divide`**: ``readonly [NumericExpression, NumericExpression]``
- **`whenExpression.equal`**: ``readonly [DataExpression, DataExpression]``
- **`whenExpression.floor`**: ``NumericExpression``
- **`whenExpression.greaterOrEqual`**: ``readonly [DataExpression, DataExpression]``
- **`whenExpression.greaterThan`**: ``readonly [DataExpression, DataExpression]``
- **`whenExpression.if`**: ``{ condition: DataExpression; then: DataExpression; else: DataExpression; }``
- **`whenExpression.if.condition`**: ``DataExpression``
- **`whenExpression.if.else`**: ``DataExpression``
- **`whenExpression.if.then`**: ``DataExpression``
- **`whenExpression.intentField`**: ``NumericIntentField``
- **`whenExpression.intentPath`**: ``string``
- **`whenExpression.lerp`**: ``{ from: NumericExpression; to: NumericExpression; amount: NumericExpression; }``
- **`whenExpression.lerp.amount`**: ``NumericExpression``
- **`whenExpression.lerp.from`**: ``NumericExpression``
- **`whenExpression.lerp.to`**: ``NumericExpression``
- **`whenExpression.lessOrEqual`**: ``readonly [DataExpression, DataExpression]``
- **`whenExpression.lessThan`**: ``readonly [DataExpression, DataExpression]``
- **`whenExpression.literal`**: ``EventPayload``
- **`whenExpression.max`**: ``NumericOperands``
- **`whenExpression.min`**: ``NumericOperands``
- **`whenExpression.multiply`**: ``NumericOperands``
- **`whenExpression.negate`**: ``NumericExpression``
- **`whenExpression.not`**: ``DataExpression``
- **`whenExpression.object`**: ``{ readonly [key: string]: DataExpression; }``
- **`whenExpression.or`**: ``DataOperands``
- **`whenExpression.path`**: ``string``
- **`whenExpression.pointer`**: ``string | undefined``
- **`whenExpression.remap`**: ``{ value: NumericExpression; inMin: NumericExpression; inMax: NumericExpression; outMin: NumericExpression; outMax: NumericExpression; }``
- **`whenExpression.remap.inMax`**: ``NumericExpression``
- **`whenExpression.remap.inMin`**: ``NumericExpression``
- **`whenExpression.remap.outMax`**: ``NumericExpression``
- **`whenExpression.remap.outMin`**: ``NumericExpression``
- **`whenExpression.remap.value`**: ``NumericExpression``
- **`whenExpression.round`**: ``NumericExpression``
- **`whenExpression.subtract`**: ``readonly [NumericExpression, NumericExpression]``

## waterfall

- **`alpha`**: ``number | undefined``
- **`channelStage`**: ``string``
- **`channelSurfaceId`**: ``number``
- **`color`**: ``number | undefined``
- **`drop`**: ``number``
- **`flowId`**: ``number``
- **`referenceFlux`**: ``number``
- **`sheetStage`**: ``string``
- **`sheetSurfaceId`**: ``number``

## weather-author

- **`birth`**: ``(Pick<EmitterOptions, "shape" | "distribution" | "position" | "extent" | "velocity" | "spread" | "initialOrientation" | "angularVelocity"> & { orientation?: Vector3 | undefined; }) | undefined``
- **`birth.angularVelocity`**: ``Vector3 | undefined``
- **`birth.distribution`**: ``"legacy" | "uniform" | undefined``
- **`birth.extent`**: ``Vector3 | undefined``
- **`birth.initialOrientation`**: ``Vector3 | undefined``
- **`birth.orientation`**: ``Vector3 | undefined``
- **`birth.position`**: ``Vector3 | undefined``
- **`birth.shape`**: ``"point" | "box" | "sphere" | "disc" | "line" | undefined``
- **`birth.spread`**: ``Vector3 | undefined``
- **`birth.velocity`**: ``Vector3 | undefined``
- **`collision`**: ``{ enabled?: boolean | undefined; deposit?: boolean | undefined; } | undefined``
- **`collision.deposit`**: ``boolean | undefined``
- **`collision.enabled`**: ``boolean | undefined``
- **`effect`**: ``string``
- **`emission`**: ``Pick<EmitterOptions, "schedule" | "seed" | "count" | "rate" | "runningTimeMs" | "startTimeUs" | "cycles" | "gapMs"> | undefined``
- **`emission.count`**: ``number | undefined``
- **`emission.cycles`**: ``number | undefined``
- **`emission.gapMs`**: ``number | undefined``
- **`emission.rate`**: ``number | undefined``
- **`emission.runningTimeMs`**: ``number | undefined``
- **`emission.schedule`**: ``"uniform" | "seeded-jitter" | undefined``
- **`emission.seed`**: ``number | undefined``
- **`emission.startTimeUs`**: ``number | undefined``
- **`forces`**: ``Pick<EmitterOptions, "gravity" | "wind" | "windVariation" | "drag" | "lift" | "flutterHz" | "flutterAmount" | "tumble" | "heat" | "windScale" | "windPeriodSeconds"> | undefined``
- **`forces.drag`**: ``number | undefined``
- **`forces.flutterAmount`**: ``number | undefined``
- **`forces.flutterHz`**: ``number | undefined``
- **`forces.gravity`**: ``Vector3 | undefined``
- **`forces.heat`**: ``number | undefined``
- **`forces.lift`**: ``number | undefined``
- **`forces.tumble`**: ``Vector3 | undefined``
- **`forces.wind`**: ``Vector3 | undefined``
- **`forces.windPeriodSeconds`**: ``number | undefined``
- **`forces.windScale`**: ``number | undefined``
- **`forces.windVariation`**: ``Vector3 | undefined``
- **`id`**: ``number``
- **`lifecycle`**: ``Pick<EmitterOptions, "lifetimeMinMs" | "lifetimeMaxMs" | "endStyle" | "tailMs"> | undefined``
- **`lifecycle.endStyle`**: ``EndStyle | undefined``
- **`lifecycle.lifetimeMaxMs`**: ``number | undefined``
- **`lifecycle.lifetimeMinMs`**: ``number | undefined``
- **`lifecycle.tailMs`**: ``number | undefined``
- **`particle`**: ``Pick<EmitterOptions, "material" | "shapeWeights" | "sizeMin" | "sizeMax" | "alpha" | "radius" | "topology" | "trailMs" | "birthFadeMs" | "deathFadeMs" | "coreMs" | ... 8 more ... | "surfaceAlpha"> | undefined``
- **`particle.alpha`**: ``number | undefined``
- **`particle.backTint`**: ``number | undefined``
- **`particle.birthFadeMs`**: ``number | undefined``
- **`particle.coreMs`**: ``number | undefined``
- **`particle.curl`**: ``number | undefined``
- **`particle.deathFadeMs`**: ``number | undefined``
- **`particle.farDistance`**: ``number | undefined``
- **`particle.farFadeDistance`**: ``number | undefined``
- **`particle.material`**: ``number | undefined``
- **`particle.nearDistance`**: ``number | undefined``
- **`particle.radius`**: ``number | undefined``
- **`particle.sampling`**: ``Sampling | undefined``
- **`particle.shapeWeights`**: ``Vector3 | undefined``
- **`particle.sizeMax`**: ``number | undefined``
- **`particle.sizeMin`**: ``number | undefined``
- **`particle.surfaceAlpha`**: ``number | undefined``
- **`particle.topology`**: ``0 | 1 | 2 | 3 | 4 | 5 | undefined``
- **`particle.trailMs`**: ``number | undefined``
- **`particle.twoSided`**: ``boolean | undefined``
- **`particle.veinContrast`**: ``number | undefined``
- **`schema`**: ``"nocturne.weather-authoring/v1"``

## wheel

- **`delta`**: ``number``
- **`shift`**: ``boolean | undefined``
- **`x`**: ``number | undefined``
- **`y`**: ``number | undefined``

## widget

- **`active`**: ``boolean | undefined``

  Boolean flags; defaults true, false, false
- **`alpha`**: ``number | undefined``

  Coverage 0–1; default 0.25
- **`backgroundMaterial`**: ``number | undefined``

  Integer −1–15; default −1
- **`border`**: ``Border | undefined``

  none, rounded, square, double, heavy; default none
- **`cellAspect`**: ``number | undefined``

  0.5–4; default 2; pie/donut only
- **`data`**: ``readonly number[] | undefined``

  Up to 128 finite values, each −1,000,000–1,000,000; initially empty
- **`enabled`**: ``boolean | undefined``

  Boolean flags; defaults true, false, false
- **`height`**: ``number | undefined``

  Positive integer dimensions; defaults 20 and 3
- **`id`**: ``number``

  Required identified resource; reserve it in the application
- **`innerRadius`**: ``number | undefined``

  0–0.98; default approximately 0.6164414; donut only
- **`kind`**: ``WidgetKind | undefined``

  One of the families above; a fresh widget defaults to text
- **`material`**: ``number | undefined``

  Integer 0–15; default 2
- **`max`**: ``number | undefined``

  Finite −1,000,000–1,000,000; defaults 0, 0, 1; max must exceed min
- **`min`**: ``number | undefined``

  Finite −1,000,000–1,000,000; defaults 0, 0, 1; max must exceed min
- **`mode`**: ``number | undefined``

  Integer 0–15; default 0; interpretation belongs to the kind
- **`padding`**: ``number | undefined``

  Integer 0–8; default 0
- **`pulseMs`**: ``number | undefined``

  Duration through 60000 ms; default 1000 ms
- **`replay`**: ``boolean | undefined``

  Boolean command option; true restarts reveal at current scene time
- **`revealMs`**: ``number | undefined``

  Duration through 60000 ms; default 0; geometric widgets only
- **`sampling`**: ``"cell" | "half" | "braille" | "hybrid" | "inherit" | undefined``

  inherit, cell, half, braille, hybrid; default inherit; geometric widgets only
- **`selected`**: ``boolean | undefined``

  Boolean flags; defaults true, false, false
- **`startAngle`**: ``number | undefined``

  −36000–36000 degrees; default 0; pie/donut only
- **`sweepAngle`**: ``number | undefined``

  0–360 degrees; default 360; pie/donut only
- **`text`**: ``string | undefined``

  Retained Unicode text within native text capacity; initially empty
- **`value`**: ``number | undefined``

  Finite −1,000,000–1,000,000; defaults 0, 0, 1; max must exceed min
- **`width`**: ``number | undefined``

  Positive integer dimensions; defaults 20 and 3
- **`x`**: ``number | undefined``

  Integer layout coordinates; default 0
- **`y`**: ``number | undefined``

  Integer layout coordinates; default 0

## window

- **`alpha`**: ``number | undefined``

  New-window default: 0.8.

  0..1
- **`anchorX`**: ``number | undefined``

  New-window default: 0.5,1.15.

  −2..3
- **`anchorY`**: ``number | undefined``

  New-window default: 0.5,1.15.

  −2..3
- **`bend`**: ``number | undefined``

  New-window default: 9.

  −40..40
- **`border`**: ``Border | undefined``

  New-window default: `rounded`.

  `none`, `rounded`, `square`, `double`, `heavy`
- **`chrome`**: ``WindowSourceChrome | undefined``
- **`chromeSize`**: ``number | undefined``

  New-window default: 3.

  Integer1..5
- **`controlHeight`**: ``number | undefined``
- **`controlWidth`**: ``number | undefined``
- **`customGlyphs`**: ``string | undefined``
- **`customOrder`**: ``string | undefined``
- **`customSide`**: ``"left" | "right" | undefined``
- **`depthFade`**: ``number | undefined``
- **`durationMs`**: ``number | undefined``

  New-window default: 600.

  0..60000 milliseconds
- **`effect`**: ``string | undefined``

  New-window default: `window-transition/glass-dissolve`.

  Current WindowTransition identity
- **`fadeEndRatio`**: ``number | undefined``

  New-window default: 1,0.22.

  Start0.001..8, end0..8; end strictly below start
- **`fadeStartRatio`**: ``number | undefined``

  New-window default: 1,0.22.

  Start0.001..8, end0..8; end strictly below start
- **`folds`**: ``number | undefined``

  New-window default: 6.

  Integer1..32
- **`group`**: ``number | undefined``

  New-window default: 0.

  Integer0..65535
- **`height`**: ``number | undefined``

  New-window default: 28,22.

  1..2147483647; world geometry dimensions
- **`id`**: ``number``
- **`material`**: ``number | undefined``

  New-window default: 2.

  Integer0..15
- **`maxColumns`**: ``number | undefined``

  New-window default: 30,78.

  Integers8..2147483647; ordered; minimum strictly greater than `2*(padding+1)`
- **`meshColumns`**: ``number | undefined``

  New-window default: 12.

  Integer2..32
- **`meshRows`**: ``number | undefined``

  New-window default: 8.

  Integer2..24
- **`minColumns`**: ``number | undefined``

  New-window default: 30,78.

  Integers8..2147483647; ordered; minimum strictly greater than `2*(padding+1)`
- **`overshoot`**: ``number | undefined``

  New-window default: 0.18.

  0..1
- **`padding`**: ``number | undefined``

  New-window default: 1.

  Integer0..8
- **`pitch`**: ``number | undefined``

  New-window default: 0.

  Each −36000..36000 degrees
- **`polygon`**: ``readonly (readonly [number, number])[] | undefined``
- **`position`**: ``Vector3 | undefined``

  New-window default: Slot-dependent arrangement.

  XYZ scene units, each −16000..16000
- **`roll`**: ``number | undefined``

  New-window default: 0.

  Each −36000..36000 degrees
- **`scatter`**: ``number | undefined``

  New-window default: 32.

  0..100
- **`seed`**: ``number | undefined``

  New-window default: Scene seed.

  uint32
- **`shape`**: ``string | undefined``

  New-window default: `rectangle`.

  Rectangle, rounded, ellipse, hexagon, diamond, capsule, ticket, squircle, petal, wave, cloud or polygon
- **`sourceGeometry`**: ``boolean | undefined``

  New-window default: `false`.

  Boolean; opts into preserved source geometry
- **`sourcePresentation`**: ``boolean | undefined``
- **`text`**: ``string | undefined``

  New-window default: Empty.

  Up to 2048 Unicode scalars
- **`title`**: ``string | undefined``

  New-window default: Empty.

  Up to 160 Unicode scalars
- **`width`**: ``number | undefined``

  New-window default: 28,22.

  1..2147483647; world geometry dimensions
- **`yaw`**: ``number | undefined``

  New-window default: 0.

  Each −36000..36000 degrees

## window-action

- **`action`**: ``WindowAction``
- **`durationMs`**: ``number | undefined``
- **`dx`**: ``number | undefined``
- **`dy`**: ``number | undefined``
- **`effect`**: ``string | undefined``
- **`forward`**: ``number | undefined``
- **`group`**: ``number | undefined``
- **`id`**: ``number``
- **`pitch`**: ``number | undefined``
- **`roll`**: ``number | undefined``
- **`rows`**: ``number | undefined``
- **`yaw`**: ``number | undefined``

## window-application

- **`atelierParticles`**: ``AtelierApplicationParticleOptions | undefined``
- **`atelierParticles.branches`**: ``number | undefined``
- **`atelierParticles.coreMs`**: ``number | undefined``
- **`atelierParticles.coreRadius`**: ``number | undefined``
- **`atelierParticles.count`**: ``number | undefined``
- **`atelierParticles.drag`**: ``number | undefined``
- **`atelierParticles.ejecta`**: ``number | undefined``
- **`atelierParticles.glitterHz`**: ``number | undefined``
- **`atelierParticles.gravity`**: ``number | undefined``
- **`atelierParticles.intensity`**: ``number | undefined``
- **`atelierParticles.jaggedness`**: ``number | undefined``
- **`atelierParticles.lifeMs`**: ``number | undefined``
- **`atelierParticles.reducedMotion`**: ``boolean | undefined``
- **`atelierParticles.rise`**: ``number | undefined``
- **`atelierParticles.seed`**: ``number | undefined``
- **`atelierParticles.shockwave`**: ``number | undefined``
- **`atelierParticles.speed`**: ``number | undefined``
- **`atelierParticles.trailMs`**: ``number | undefined``
- **`atelierParticles.turbulence`**: ``number | undefined``
- **`axisPitch`**: ``number | undefined``
- **`backgroundStyle`**: ``WindowApplicationBackgroundStyle | undefined``
- **`fps`**: ``number | undefined``
- **`gradientAngle`**: ``number | undefined``
- **`gradientPhase`**: ``number | undefined``
- **`gradientScreens`**: ``number | undefined``
- **`gradientSpeed`**: ``number | undefined``
- **`motion`**: ``boolean | undefined``
- **`novaRegularity`**: ``number | undefined``
- **`novaStrength`**: ``number | undefined``
- **`orbitMode`**: ``"pendulum" | "spin" | undefined``
- **`paletteWindowId`**: ``number | undefined``
- **`particles`**: ``WindowApplicationParticleOptions | undefined``
- **`particles.arcJitter`**: ``number | undefined``
- **`particles.arcReach`**: ``number | undefined``
- **`particles.arcSegments`**: ``number | undefined``
- **`particles.branches`**: ``number | undefined``
- **`particles.brightness`**: ``number | undefined``
- **`particles.coreMs`**: ``number | undefined``
- **`particles.count`**: ``number | undefined``
- **`particles.drag`**: ``number | undefined``
- **`particles.emberSpread`**: ``number | undefined``
- **`particles.explosionForce`**: ``number | undefined``
- **`particles.flickerHz`**: ``number | undefined``
- **`particles.glyphs`**: ``string | undefined``
- **`particles.gravity`**: ``number | undefined``
- **`particles.launchSpeed`**: ``number | undefined``
- **`particles.lifeMs`**: ``number | undefined``
- **`particles.seed`**: ``number | undefined``
- **`particles.shockwave`**: ``number | undefined``
- **`particles.trailMs`**: ``number | undefined``
- **`particles.wind`**: ``number | undefined``
- **`pivotX`**: ``number | undefined``
- **`pivotY`**: ``number | undefined``
- **`rotationSpeed`**: ``number | undefined``
- **`sampling`**: ``WindowApplicationSampling | undefined``
- **`scene`**: ``"windows" | "shapes" | "atelier-windows" | "observatory" | undefined``
- **`secondAxisSpeed`**: ``number | undefined``
- **`starCount`**: ``number | undefined``
- **`starDensity`**: ``number | undefined``
- **`starGlyphs`**: ``string | undefined``
- **`starSpeed`**: ``number | undefined``
- **`swingAngle`**: ``number | undefined``
- **`swingSeconds`**: ``number | undefined``
- **`trailMs`**: ``number | undefined``
- **`travelPitch`**: ``number | undefined``
- **`travelYaw`**: ``number | undefined``
- **`weatherIntensity`**: ``number | undefined``
- **`weatherLifeMs`**: ``number | undefined``
- **`weatherSpeed`**: ``number | undefined``
- **`weatherStyle`**: ``"embers" | "sparks" | "nova" | "rain" | "snow" | "ripples" | undefined``

## window-application-event

- **`atMs`**: ``number | undefined``
- **`id`**: ``number | undefined``
- **`kind`**: ``"embers" | "sparks" | "nova" | "rain" | "snow" | "ripples"``
- **`x`**: ``number | undefined``
- **`y`**: ``number | undefined``

## window-content

- **`background`**: ``number | undefined``
- **`brightness`**: ``number | undefined``
- **`chroma`**: ``number | undefined``
- **`chrome`**: ``"custom" | "mac" | "windows" | "gnome" | undefined``
- **`colors`**: ``readonly number[] | undefined``
- **`customGlyphs`**: ``string[] | undefined``
- **`customOrder`**: ``("minimize" | "maximize" | "fade" | "close")[] | undefined``
- **`customSide`**: ``"left" | "right" | undefined``
- **`fadeFloor`**: ``number | undefined``
- **`feather`**: ``number | undefined``
- **`hueOffset`**: ``number | undefined``
- **`id`**: ``number``
- **`ink`**: ``number | undefined``
- **`label`**: ``string | undefined``
- **`lightness`**: ``number | undefined``
- **`lockLightness`**: ``boolean | undefined``
- **`profile`**: ``"atelier" | undefined``
- **`sourceIndex`**: ``number | undefined``
- **`stopWidths`**: ``readonly number[] | undefined``
- **`text`**: ``string | undefined``
- **`textChroma`**: ``number | undefined``
- **`textLightness`**: ``number | undefined``
- **`toolColors`**: ``{ minimize?: number | undefined; maximize?: number | undefined; fade?: number | undefined; close?: number | undefined; } | undefined``
- **`toolColors.close`**: ``number | undefined``
- **`toolColors.fade`**: ``number | undefined``
- **`toolColors.maximize`**: ``number | undefined``
- **`toolColors.minimize`**: ``number | undefined``
- **`toolHeight`**: ``number | undefined``
- **`toolWidth`**: ``number | undefined``
- **`waveform`**: ``readonly number[] | undefined``

## window-texture

- **`cells`**: ``readonly (readonly [number, number, number])[] | undefined``
- **`height`**: ``number | undefined``
- **`id`**: ``number``
- **`offset`**: ``number | undefined``
- **`width`**: ``number | undefined``

## world-style

- **`count`**: ``number | undefined``
- **`gravity`**: ``number | undefined``
- **`id`**: ``number``
- **`lifeMs`**: ``number | undefined``
- **`paint`**: ``"source" | "material" | undefined``
- **`scale`**: ``number | undefined``
- **`seed`**: ``number | undefined``
