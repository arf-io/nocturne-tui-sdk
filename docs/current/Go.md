# Go reference

The package in `native/bindings/go` uses cgo. Use the actual module name in its go.mod and a local replace directive for an adjacent SDK. The shared project exporter writes go.mod and main.go with the selected SDK path.

## Scene lifecycle

```go
scene, err := nocturne.New(2030)
if err != nil { return err }
defer scene.Close()
_, err = scene.Command(map[string]any{"op":"draft", "text":"Ready", "caret":5})
if err != nil { return err }
if err = scene.AdvanceTo(500000); err != nil { return err }
frame, err := scene.Render()
if err != nil { return err }
// Present frame.Bytes using frame.Width and frame.Height.
```

`Command` returns a status and error; inspect both. `Batch` creates one transaction. `InfoComplete` returns copied JSON bytes. `Snapshot` and `Restore` retain runtime state. Queries return copied numeric rows and errors with domains matching the C API.

Bubble Tea owns event delivery, terminal setup and resize. Keep scene calls in a deterministic event order. The application defines the order of concurrent updates. Build with a C compiler and a runtime library search path appropriate to the installed SDK.

## Runtime contract

Commands are native transactions. Rejection preserves authoritative state; catch-up pending means more work remains. Serialize operations on one scene. The binding returns copied frames, snapshots and complete metadata. Supply integer microseconds; rendering does not advance time.

The binding grows prompt, model, modal and render storage. Resource IDs and bounded emitter/window/node pools retain their declared native domains; those are separate from document length. Keep the core and binding from a compatible SDK. Use complete metadata when source exceeds ordinary readback capacity.

![Progress component](images/widget-progress-default.png)

## Public method index

The shipped binding declares the following methods. Geometry, text and resource query names correspond to the [C declarations](C.md).

- `InspectCharacterCell(x, y int32) (CharacterCellInfo, error)`
- `New(seed uint32) (*Scene, error)`
- `Close()`
- `CommandRaw(raw []byte) (int, error)`
- `Command(value any) (int, error)`
- `AdvanceTo(us uint64) error`
- `Render() (Frame, error)`
- `Info() ([]byte, error)`
- `InfoComplete() ([]byte, error)`
- `Snapshot() ([]byte, error)`
- `Restore(b []byte) error`
- `Catalogue() ([]byte, error)`
- `Particles() ([][12]int32, error)`
- `Oklch(l, c, h float64) (uint32, error)`
- `Composite(base, source, baseAlpha, sourceAlpha, blend, operation, seed uint32) ([2]uint32, error)`
- `CompositeInSpace(base, source, baseAlpha, sourceAlpha, blend, operation, seed, space uint32) ([2]uint32, error)`
- `TextSample(id, index uint32) ([8]int32, error)`
- `TextClusterSample(id, index uint32) ([8]int32, error)`
- `TextTrailSample(id, index, trail uint32) ([8]int32, error)`
- `WindowSample(id, u, v, visibility uint32) ([5]int32, error)`
- `Batch(commands []any) error`
- `Schedule(id uint32, atUs uint64, command any) error`
- `ParticleMotions() ([][7]float64, error)`
- `GraphemeWidths(text string, ambiguous uint32) ([][3]uint32, error)`
- `GraphemeLayout(text string, columns, ambiguous uint32) ([][5]uint32, error)`
- `LineBreaks(text string) ([]uint32, error)`
- `LineBreakDetails(text string) ([][2]uint32, error)`
- `GraphemeBoundaries(text string) ([]uint32, error)`
- `GraphemeHit(text string, columns, column, row, ambiguous uint32) (uint32, error)`
- `SelectedText() (string, error)`
- `TextRunClusters(kind, id uint32) ([][4]uint32, error)`
- `TextRunSource(kind, id uint32) (string, error)`
- `TextRunLayout(kind, id, columns, ambiguous uint32) ([][7]uint32, error)`
- `TextRunHit(kind, id, columns, column, row, ambiguous uint32) (uint32, error)`
- `TextRunClip(kind, id, columns, x, y, width, height, ambiguous uint32) ([][9]uint32, error)`
- `BidiVisual(text string, direction uint32) ([][4]uint32, error)`
- `BidiLayout(text string, columns, direction, ambiguous uint32) ([][7]uint32, error)`
- `BidiHit(text string, columns, column, row, direction, ambiguous uint32) (uint32, error)`
- `BidiCaret(text string, columns, offset, affinity, direction, ambiguous uint32) ([3]uint32, error)`
- `WaveSample(waves [][5]float64, x, z, seconds float64) ([6]float64, error)`
- `SurfaceWaveSample(id uint32, x, z float64) ([6]float64, error)`
- `FloatBody(id uint32) ([]float64, error)`
- `SurfaceFoam(id uint32) ([][5]float64, error)`
- `FlowThickness(id uint32) ([]float64, error)`
- `SurfaceTriangles(id uint32) ([][12]float64, error)`
- `PromptLayout() ([][8]float64, error)`
- `AreaGeometry(id uint32) (*[12]float64, error)`
- `FieldSample(id uint32, x, y float64) (*[4]float64, error)`
- `WaterSample(index uint32) (*[8]float64, error)`
- `ThermalSample(index uint32) (*[10]float64, error)`
- `SurfaceFoamTransport(id uint32) ([][7]float64, error)`
- `PathSample(points [][3]float64, distance float64, closed bool, mode uint32) ([8]float64, error)`
- `NegotiateShortcuts(actions []uint32, candidates, host [][3]uint32) ([][4]uint32, error)`
- `AngularDragExchange(bodyInertia, waterInertia, conductance [3]float64, seconds float64, bodyOmega, waterOmega [3]float64) ([10]float64, error)`
- `FluidDragExchange(bodyMass, waterMass, conductance, seconds float64, bodyVelocity, waterVelocity [3]float64) ([10]float64, error)`
- `HullImmersionPlane(vertices [][3]float64, faces [][3]uint32, point, normal [3]float64) ([5]float64, error)`
- `HullBuoyancyPlane(vertices [][3]float64, faces [][3]uint32, point, normal [3]float64, density, gravity, mass float64, centerOfMass [3]float64) ([11]float64, error)`
- `HullImmersion(vertices [][3]float64, faces [][3]uint32, height float64) ([5]float64, error)`
- `FloatHull(id uint32) (*[14]float64, error)`
- `HullMeshImmersion(vertices [][3]float64, faces [][3]uint32, water [][9]float64) ([5]float64, error)`
- `SurfaceFluidAngular(id uint32) (*[12]float64, error)`
- `SurfaceFluid(id uint32) (*[15]float64, error)`
- `BidiLines(text string, ends []uint32, direction uint32) ([][7]uint32, error)`
- `ScriptRuns(text string) ([]ScriptRun, error)`
- `PromptVisualLayout() ([][10]float64, error)`
- `SourceStageTween(from, to int32, elapsed uint64, duration uint32, easing int32) (int32, error)`
- `SourceStageInkOpacity(age, fade uint32, row, band, minimum int32) (int32, error)`
- `SourceStageHit(x, y int32) (*SourceStageHit, error)`
- `SourceStageOklch(lightness,chroma,hue int32)(uint32,error)`
- `DocumentLayout(text string, columns, direction, ambiguous uint32) ([][7]uint32, error)`
- `DocumentBoundaries(text string) ([]uint32, error)`
- `DocumentHit(text string, columns, column, row, direction, ambiguous uint32) (uint32, error)`
- `DocumentCaret(text string, columns, offset, affinity, direction, ambiguous uint32) ([3]uint32, error)`
- `SetModelRecords(data []byte) error`
- `ModelRecords() ([]byte, error)`

## Runnable example

[go/main.go](examples/go/main.go), [go/go.mod](examples/go/go.mod) use [the panel transaction](examples/panel.json). Run from the example directory beside the SDK source. The Go example uses the shared library; Rust builds its native archive.

[Common command field reference](Commands.md).
