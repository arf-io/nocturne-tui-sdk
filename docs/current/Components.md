# Components and states

The registry covers all 18 widget kinds and the visible native component families below. Each named image uses its declared commands, Gallery recipe or composition project and time. The [capture index](images/CAPTURES.json) records image and cell hashes; native replay and WASM cells must match for every listed state. The [component registry](components.json) contains the requests that reproduce them. The [component catalogue](Catalogue.md) lists the native effects, except those hidden by the nullification contract, with the commands that accept them, their parameters, defaults, domains and examples.

## Component index

| Component | Contract | Coordinates |
|---|---|---|
| [Text](#widget-text) | `widget / text` | screen-cells |
| [Box](#widget-box) | `widget / box` | screen-cells |
| [Rule](#widget-rule) | `widget / rule` | screen-cells |
| [Button](#widget-button) | `widget / button` | screen-cells |
| [Item](#widget-item) | `widget / item` | screen-cells |
| [Cursor](#widget-cursor) | `widget / cursor` | screen-cells |
| [Progress](#widget-progress) | `widget / progress` | screen-cells |
| [Bars](#widget-bars) | `widget / bars` | screen-cells |
| [Pie](#widget-pie) | `widget / pie` | screen-cells |
| [Donut](#widget-donut) | `widget / donut` | screen-cells |
| [Scatter](#widget-scatter) | `widget / scatter` | screen-cells |
| [Line](#widget-line) | `widget / line` | screen-cells |
| [Digits](#widget-digits) | `widget / digits` | screen-cells |
| [Edge](#widget-edge) | `widget / edge` | screen-cells |
| [Checkbox](#widget-checkbox) | `widget / checkbox` | screen-cells |
| [Radio](#widget-radio) | `widget / radio` | screen-cells |
| [Select](#widget-select) | `widget / select` | screen-cells |
| [Scrollbar](#widget-scrollbar) | `widget / scrollbar` | screen-cells |
| [Window](#window) | `window` | native-surface |
| [Editable prompt](#prompt) | `prompt` | native-surface |
| [Animated text](#text) | `text` | native-surface |
| [Graph nodes and edges](#graph) | `node / edge / layout` | native-surface |
| [Weather emitter](#emitter) | `emitter` | native-surface |
| [Surface field](#field) | `field` | native-surface |
| [Floor and deposits](#floor) | `floor` | native-surface |
| [Surface and mesh](#surface) | `surface / mesh` | native-surface |
| [Flow and water](#flow) | `flow / flow-stage` | native-surface |
| [Floating body](#float) | `float-body` | native-surface |
| [Path travel](#path) | `path-travel` | native-surface |
| [Cell art](#cell-art) | `cell-art` | native-surface |
| [Status and notification](#status) | `status` | native-surface |
| [Wait indicator](#indicator) | `indicator` | native-surface |
| [Clipping area](#area) | `area` | native-surface |
| [Modal stack](#modal) | `source-modal` | native-surface |
| [Window reader](#reader) | `window-reader` | native-surface |
| [Material](#material) | `material` | native-surface |
| [Environment](#background) | `environment` | native-surface |
| [Camera rigs](#camera) | `camera / camera-controls` | native-surface |
| [Scripted flight](#flight) | `flight` | native-surface |
| [Pearl Cascade](#pearl-cascade) | `scene-art` | native-surface |
| [Copper Causeway](#copper-causeway) | `scene-art` | native-surface |
| [Tidal Glass](#tidal-glass) | `scene-art` | native-surface |
| [Silt](#silt) | `scene-art` | native-surface |
| [Model geometry](#model) | `model-view` | native-surface |
| [Application stage](#stage) | `source-stage / source-stage-component` | native-surface |
| [Connected arcs](#electrical) | `electrical-arc` | native-surface |

| [Signal Desk](#project-signal-desk) | `composition project` | world + interface |
| [Flight Deck](#project-flight-deck) | `composition project` | world + interface |
| [Tidal Console](#project-tidal-console) | `composition project` | world + interface |

## widget-text

**Text** uses `widget / text` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Text — Default](images/widget-text-default.png)

### Updated value / active

![Text — Updated value / active](images/widget-text-active.png)


## widget-box

**Box** uses `widget / box` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Box — Default](images/widget-box-default.png)

### Updated value / active

![Box — Updated value / active](images/widget-box-active.png)


## widget-rule

**Rule** uses `widget / rule` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Rule — Default](images/widget-rule-default.png)

### Updated value / active

![Rule — Updated value / active](images/widget-rule-active.png)


## widget-button

**Button** uses `widget / button` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Button — Default](images/widget-button-default.png)

### Updated value / active

![Button — Updated value / active](images/widget-button-active.png)


## widget-item

**Item** uses `widget / item` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Item — Default](images/widget-item-default.png)

### Updated value / active

![Item — Updated value / active](images/widget-item-active.png)


## widget-cursor

**Cursor** uses `widget / cursor` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Cursor — Default](images/widget-cursor-default.png)

### Updated value / active

![Cursor — Updated value / active](images/widget-cursor-active.png)


## widget-progress

**Progress** uses `widget / progress` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Progress — Default](images/widget-progress-default.png)

### Updated value / active

![Progress — Updated value / active](images/widget-progress-active.png)


## widget-bars

**Bars** uses `widget / bars` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Bars — Default](images/widget-bars-default.png)

### Updated value / active

![Bars — Updated value / active](images/widget-bars-active.png)


## widget-pie

**Pie** uses `widget / pie` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Pie — Default](images/widget-pie-default.png)

### Updated value / active

![Pie — Updated value / active](images/widget-pie-active.png)


## widget-donut

**Donut** uses `widget / donut` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Donut — Default](images/widget-donut-default.png)

### Updated value / active

![Donut — Updated value / active](images/widget-donut-active.png)


## widget-scatter

**Scatter** uses `widget / scatter` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Scatter — Default](images/widget-scatter-default.png)

### Updated value / active

![Scatter — Updated value / active](images/widget-scatter-active.png)


## widget-line

**Line** uses `widget / line` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Line — Default](images/widget-line-default.png)

### Updated value / active

![Line — Updated value / active](images/widget-line-active.png)


## widget-digits

**Digits** uses `widget / digits` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Digits — Default](images/widget-digits-default.png)

### Updated value / active

![Digits — Updated value / active](images/widget-digits-active.png)


## widget-edge

**Edge** uses `widget / edge` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Edge — Default](images/widget-edge-default.png)

### Updated value / active

![Edge — Updated value / active](images/widget-edge-active.png)


## widget-checkbox

**Checkbox** uses `widget / checkbox` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Checkbox — Default](images/widget-checkbox-default.png)

### Updated value / active

![Checkbox — Updated value / active](images/widget-checkbox-active.png)


## widget-radio

**Radio** uses `widget / radio` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Radio — Default](images/widget-radio-default.png)

### Updated value / active

![Radio — Updated value / active](images/widget-radio-active.png)


## widget-select

**Select** uses `widget / select` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Select — Default](images/widget-select-default.png)

### Updated value / active

![Select — Updated value / active](images/widget-select-active.png)


## widget-scrollbar

**Scrollbar** uses `widget / scrollbar` in screen-cells coordinates.

The first state shows its initial value/content. The second applies an explicit value or selection update. Geometry is authored in terminal cells. Enabled, active and selected are separate native properties; shape-specific plot settings apply only to geometric widgets.

### Default

![Scrollbar — Default](images/widget-scrollbar-default.png)

### Updated value / active

![Scrollbar — Updated value / active](images/widget-scrollbar-active.png)


## window

**Window** uses `window` in native-surface coordinates.

Projected panels retain their own position, size, rotation, content, texture and opening/closing effect. Use native hit ownership and the full reader for content clipped by perspective.

### Initial presentation

![Window — Initial presentation](images/window-default.png)

Gallery recipe: `windows`. Requested advance: 0 ms.

### At 1.2 seconds

![Window — At 1.2 seconds](images/window-advanced.png)

Gallery recipe: `windows`. Requested advance: 1200 ms.


## prompt

**Editable prompt** uses `prompt` in native-surface coordinates.

The editable document has scalar selection and independent cursor/typing-weather configuration. Input follows the active owner; the rendered viewport is only a presentation of the retained source.

### Initial presentation

![Editable prompt — Initial presentation](images/prompt-default.png)

Gallery recipe: `screen-prompt-marquee-isolated`. Requested advance: 0 ms.

### At 1.2 seconds

![Editable prompt — At 1.2 seconds](images/prompt-advanced.png)

Gallery recipe: `screen-prompt-marquee-isolated`. Requested advance: 1200 ms.

### Steady custom cursor

![Editable prompt — Steady custom cursor](images/prompt-cursor.png)

### Accepted input with embers

![Editable prompt — Accepted input with embers](images/prompt-typing-weather.png)


## text

**Animated text** uses `text` in native-surface coordinates.

Text runs preserve source, reveal/effect state and semantic identity. Their frame can be clipped or transformed without discarding the full source.

### Initial presentation

![Animated text — Initial presentation](images/text-default.png)

Gallery recipe: `text`. Requested advance: 0 ms.

### At 1.2 seconds

![Animated text — At 1.2 seconds](images/text-advanced.png)

Gallery recipe: `text`. Requested advance: 1200 ms.


## graph

**Graph nodes and edges** uses `node / edge / layout` in native-surface coordinates.

Nodes and edges have stable identities, metadata and layout controls. Change the native layout/camera to select spatial or planar presentation; keep full labels available to the reader.

### Initial presentation

![Graph nodes and edges — Initial presentation](images/graph-default.png)

Gallery recipe: `work-graph`. Requested advance: 0 ms.

### At 1.2 seconds

![Graph nodes and edges — At 1.2 seconds](images/graph-advanced.png)

Gallery recipe: `work-graph`. Requested advance: 1200 ms.


## emitter

**Weather emitter** uses `emitter` in native-surface coordinates.

An emitter controls birth, movement, lifetime and local appearance. Configure its material and sampling separately from its physical trajectory.

### Initial presentation

![Weather emitter — Initial presentation](images/emitter-default.png)

Gallery recipe: `autumn`. Requested advance: 0 ms.

### At 1.2 seconds

![Weather emitter — At 1.2 seconds](images/emitter-advanced.png)

Gallery recipe: `autumn`. Requested advance: 1200 ms.


## field

**Surface field** uses `field` in native-surface coordinates.

A field samples a declared scalar/color function over its space. Consumers can use the field while retaining their own geometry and local sampling.

### Initial presentation

![Surface field — Initial presentation](images/field-default.png)

Gallery recipe: `silk`. Requested advance: 0 ms.

### At 1.2 seconds

![Surface field — At 1.2 seconds](images/field-advanced.png)

Gallery recipe: `silk`. Requested advance: 1200 ms.


## floor

**Floor and deposits** uses `floor` in native-surface coordinates.

A floor is visible geometry and an optional collider. Its grid, matte and deposited details retain separate coverage.

### Initial presentation

![Floor and deposits — Initial presentation](images/floor-default.png)

Gallery recipe: `leaf-anatomy`. Requested advance: 0 ms.

### At 1.2 seconds

![Floor and deposits — At 1.2 seconds](images/floor-advanced.png)

Gallery recipe: `leaf-anatomy`. Requested advance: 1200 ms.


## surface

**Surface and mesh** uses `surface / mesh` in native-surface coordinates.

Surfaces associate physical properties and retained deposits with mesh triangles. Visibility, collision participation and rendered sampling are separate controls.

### Initial presentation

![Surface and mesh — Initial presentation](images/surface-default.png)

Gallery recipe: `surface-lab`. Requested advance: 0 ms.

### At 1.2 seconds

![Surface and mesh — At 1.2 seconds](images/surface-advanced.png)

Gallery recipe: `surface-lab`. Requested advance: 1200 ms.


## flow

**Flow and water** uses `flow / flow-stage` in native-surface coordinates.

Flows carry a time-dependent path and surface behavior. Inspect their native state rather than inferring physical quantities from a screenshot.

### Initial presentation

![Flow and water — Initial presentation](images/flow-default.png)

Gallery recipe: `scenic-spatial-water-isolated`. Requested advance: 0 ms.

### At 1.2 seconds

![Flow and water — At 1.2 seconds](images/flow-advanced.png)

Gallery recipe: `scenic-spatial-water-isolated`. Requested advance: 1200 ms.


## float

**Floating body** uses `float-body` in native-surface coordinates.

Float bodies use declared geometry and fluid interaction. They retain body pose and dynamics independently from the displayed water surface.

### Initial presentation

![Floating body — Initial presentation](images/float-default.png)

Gallery recipe: `scenic-shared-ocean-isolated`. Requested advance: 0 ms.

### At 1.2 seconds

![Floating body — At 1.2 seconds](images/float-advanced.png)

Gallery recipe: `scenic-shared-ocean-isolated`. Requested advance: 1200 ms.


## path

**Path travel** uses `path-travel` in native-surface coordinates.

Paths define motion through explicit points and sampling rules. Duration, position and motion events belong to the scene clock.

### Initial presentation

![Path travel — Initial presentation](images/float-default.png)

Gallery recipe: `scenic-shared-ocean-isolated`. Requested advance: 0 ms.

### At 1.2 seconds

![Path travel — At 1.2 seconds](images/float-advanced.png)

Gallery recipe: `scenic-shared-ocean-isolated`. Requested advance: 1200 ms.


## cell-art

**Cell art** uses `cell-art` in native-surface coordinates.

Cell art writes retained scalar/ink/background samples into a scene region. Use owned source data rather than an external image URL in a command.

### Initial presentation

![Cell art — Initial presentation](images/cell-art-default.png)

Gallery recipe: `screen-cell-art-background-isolated`. Requested advance: 0 ms.

### At 1.2 seconds

![Cell art — At 1.2 seconds](images/cell-art-advanced.png)

Gallery recipe: `screen-cell-art-background-isolated`. Requested advance: 1200 ms.


## status

**Status and notification** uses `status` in native-surface coordinates.

Status and notification records retain semantic identities and acknowledgement behavior. A visible notice does not execute a host action by itself.

### Initial presentation

![Status and notification — Initial presentation](images/status-default.png)

Gallery recipe: `notifications`. Requested advance: 0 ms.

### At 1.2 seconds

![Status and notification — At 1.2 seconds](images/status-advanced.png)

Gallery recipe: `notifications`. Requested advance: 1200 ms.


## indicator

**Wait indicator** uses `indicator` in native-surface coordinates.

Indicators display live state through declared material and geometry. Preserve labels and values in accessible metadata.

### Initial presentation

![Wait indicator — Initial presentation](images/indicator-default.png)

Gallery recipe: `status`. Requested advance: 0 ms.

### At 1.2 seconds

![Wait indicator — At 1.2 seconds](images/indicator-advanced.png)

Gallery recipe: `status`. Requested advance: 1200 ms.


## area

**Clipping area** uses `area` in native-surface coordinates.

Areas define screen layout and clipping for their content. Use area geometry queries when mapping host controls to native coordinates.

### Initial presentation

![Clipping area — Initial presentation](images/indicator-default.png)

Gallery recipe: `status`. Requested advance: 0 ms.

### At 1.2 seconds

![Clipping area — At 1.2 seconds](images/indicator-advanced.png)

Gallery recipe: `status`. Requested advance: 1200 ms.


## modal

**Modal stack** uses `source-modal` in native-surface coordinates.

Modal entries own input above the scene. Push/pop restores the preceding context and selection; a rejected operation leaves the stack unchanged.

### Initial presentation

![Modal stack — Initial presentation](images/modal-default.png)

Gallery recipe: `source-modal-center`. Requested advance: 0 ms.

### At 1.2 seconds

![Modal stack — At 1.2 seconds](images/modal-default.png)

Gallery recipe: `source-modal-center`. Requested advance: 1200 ms.


## reader

**Window reader** uses `window-reader` in native-surface coordinates.

Readers expose complete source text from projected or clipped content. Navigation and selection belong to the reader while it owns input.

### Initial presentation

![Window reader — Initial presentation](images/reader-default.png)

Gallery recipe: `input-workflow-reader-owner-isolated`. Requested advance: 0 ms.

### At 1.2 seconds

![Window reader — At 1.2 seconds](images/reader-advanced.png)

Gallery recipe: `input-workflow-reader-owner-isolated`. Requested advance: 1200 ms.


## material

**Material** uses `material` in native-surface coordinates.

Materials specify color and pattern behavior over time. The same material can be consumed by multiple geometries with their own alpha and sampling.

### Initial presentation

![Material — Initial presentation](images/material-default.png)

Gallery recipe: `mixed-materials`. Requested advance: 0 ms.

### At 1.2 seconds

![Material — At 1.2 seconds](images/material-advanced.png)

Gallery recipe: `mixed-materials`. Requested advance: 1200 ms.


## background

**Environment** uses `environment` in native-surface coordinates.

Environment fields establish the background and sky. Foreground pseudo-alpha resolves against the actual background at the sample.

### Initial presentation

![Environment — Initial presentation](images/field-default.png)

Gallery recipe: `silk`. Requested advance: 0 ms.

### At 1.2 seconds

![Environment — At 1.2 seconds](images/field-advanced.png)

Gallery recipe: `silk`. Requested advance: 1200 ms.


## camera

**Camera rigs** uses `camera / camera-controls` in native-surface coordinates.

Camera controls support orbit, head, dolly, crane, follow and spacecraft rigs. Configure axes independently and preserve the selected world anchor during orbit.

### Initial presentation

![Camera rigs — Initial presentation](images/camera-default.png)

Gallery recipe: `flight`. Requested advance: 0 ms.

### At 1.2 seconds

![Camera rigs — At 1.2 seconds](images/camera-advanced.png)

Gallery recipe: `flight`. Requested advance: 1200 ms.


## flight

**Scripted flight** uses `flight` in native-surface coordinates.

Flight advances the camera carrier on the native clock. Head-relative look and manual camera input remain independent from an explicit brake.

### Initial presentation

![Scripted flight — Initial presentation](images/flight-default.png)

Gallery recipe: `flight-banked`. Requested advance: 0 ms.

### At 1.2 seconds

![Scripted flight — At 1.2 seconds](images/flight-advanced.png)

Gallery recipe: `flight-banked`. Requested advance: 1200 ms.


## pearl-cascade

**Pearl Cascade** uses `scene-art` in native-surface coordinates.

Pearl Cascade renders waterfall, cliffs and vegetation. Water flow edits preserve the independent phase timeline and camera framing.

### Initial presentation

![Pearl Cascade — Initial presentation](images/pearl-cascade-default.png)

Gallery recipe: `original-pearl-cascade`. Requested advance: 0 ms.

### At 1.2 seconds

![Pearl Cascade — At 1.2 seconds](images/pearl-cascade-advanced.png)

Gallery recipe: `original-pearl-cascade`. Requested advance: 1200 ms.


## copper-causeway

**Copper Causeway** uses `scene-art` in native-surface coordinates.

Copper Causeway renders the road, supports and surrounding terrain. Travel speed changes preserve the distance timeline.

### Initial presentation

![Copper Causeway — Initial presentation](images/copper-causeway-default.png)

Gallery recipe: `original-copper-causeway`. Requested advance: 0 ms.

### At 1.2 seconds

![Copper Causeway — At 1.2 seconds](images/copper-causeway-advanced.png)

Gallery recipe: `original-copper-causeway`. Requested advance: 1200 ms.


## tidal-glass

**Tidal Glass** uses `scene-art` in native-surface coordinates.

Tidal Glass renders water, boat and structures in world space. Wave and projection controls change the native surface.

### Initial presentation

![Tidal Glass — Initial presentation](images/tidal-glass-default.png)

Gallery recipe: `original-tidal-glass`. Requested advance: 0 ms.

### At 1.2 seconds

![Tidal Glass — At 1.2 seconds](images/tidal-glass-advanced.png)

Gallery recipe: `original-tidal-glass`. Requested advance: 1200 ms.


## silt

**Silt** uses `scene-art` in native-surface coordinates.

Silt renders terrain with spatial projection. Use camera rigs to inspect its depth and surface detail.

### Initial presentation

![Silt — Initial presentation](images/silt-default.png)

Gallery recipe: `original-silt`. Requested advance: 0 ms.

### At 1.2 seconds

![Silt — At 1.2 seconds](images/silt-advanced.png)

Gallery recipe: `original-silt`. Requested advance: 1200 ms.


## model

**Model geometry** uses `model-view` in native-surface coordinates.

Model view imports complete supported mesh records and renders their actual triangles. Keep the owned model resource with a saved project.

### Initial presentation

![Model geometry — Initial presentation](images/model-default.png)

Gallery recipe: `original-orbital-loom`. Requested advance: 0 ms.

### At 1.2 seconds

![Model geometry — At 1.2 seconds](images/model-default.png)

Gallery recipe: `original-orbital-loom`. Requested advance: 1200 ms.


## stage

**Application stage** uses `source-stage / source-stage-component` in native-surface coordinates.

Stage components compose application text, panels, plots and controls over a configured background and scene clock.

### Initial presentation

![Application stage — Initial presentation](images/stage-default.png)

Gallery recipe: `pearl-fleet-original`. Requested advance: 0 ms.

### At 1.2 seconds

![Application stage — At 1.2 seconds](images/stage-advanced.png)

Gallery recipe: `pearl-fleet-original`. Requested advance: 1200 ms.


## electrical

**Connected arcs** uses `electrical-arc` in native-surface coordinates.

Electrical arcs connect declared anchors and retain their shape and temporal controls in the native scene.

### Initial presentation

![Connected arcs — Initial presentation](images/electrical-default.png)

Gallery recipe: `electrical-graphs-connected-leaders-isolated`. Requested advance: 0 ms.

### At 1.2 seconds

![Connected arcs — At 1.2 seconds](images/electrical-advanced.png)

Gallery recipe: `electrical-graphs-connected-leaders-isolated`. Requested advance: 1200 ms.


## project-signal-desk

**Signal Desk** combines editable world and interface elements from the shared composition project. Select `project:signal-desk` in Gallery.

### Initial presentation

![Signal Desk — Initial presentation](images/project-signal-desk-default.png)

### At 1.2 seconds

![Signal Desk — At 1.2 seconds](images/project-signal-desk-advanced.png)


## project-flight-deck

**Flight Deck** combines editable world and interface elements from the shared composition project. Select `project:flight-deck` in Gallery.

### Initial presentation

![Flight Deck — Initial presentation](images/project-flight-deck-default.png)

### At 1.2 seconds

![Flight Deck — At 1.2 seconds](images/project-flight-deck-advanced.png)


## project-tidal-console

**Tidal Console** combines editable world and interface elements from the shared composition project. Select `project:tidal-console` in Gallery.

### Initial presentation

![Tidal Console — Initial presentation](images/project-tidal-console-default.png)

### At 1.2 seconds

![Tidal Console — At 1.2 seconds](images/project-tidal-console-advanced.png)
