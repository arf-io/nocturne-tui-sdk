# C reference

The public header is `native/include/nocturne_native.h`. Link the native library from `native/dist`. The C11 core is freestanding with caller-owned storage; it performs no heap allocation or device I/O. ABI 1 contexts are opaque.

## Minimal program

This complete program creates and renders a progress component. `calloc` provides suitable alignment for the context. Copy `nrCells` output before another context call.

```c
#include "nocturne_native.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
    uint32_t bytes=nrContextSize();
    NrContext *scene=calloc(1,bytes);
    if(!scene || nrInit(scene,bytes,2030)!=0) return 1;
    const char *command="{\"op\":\"batch\",\"commands\":[{\"op\":\"resize\",\"width\":80,\"height\":24},{\"op\":\"widget\",\"id\":1,\"kind\":\"progress\",\"x\":5,\"y\":6,\"width\":60,\"height\":3,\"value\":0.65,\"border\":\"rounded\"}]}";
    if(nrCommand(scene,command,(uint32_t)strlen(command))<0) {
        fprintf(stderr,"%s\n",nrError(scene)); free(scene); return 2;
    }
    uint32_t count=nrRender(scene);
    if(count!=80*24 || !nrCells(scene)) {free(scene);return 3;}
    printf("%u x %u: %u cells\n",nrWidth(scene),nrHeight(scene),count);
    free(scene);return 0;
}
```

The source is [examples/panel.c](examples/panel.c). From the SDK root on macOS:

```sh
cc -std=c11 -I native/include docs/current/examples/panel.c -L native/dist -lnocturne_native -Wl,-rpath,"$PWD/native/dist" -o /tmp/nocturne-panel
/tmp/nocturne-panel
```

On Linux use the same include/library arguments with a runtime search path appropriate to the installed SDK. The shipping core has no profiling runtime requirement.

## Ownership and errors

Allocate `nrContextSize()` bytes aligned to 8 and initialize with `nrInit`. Keep all caller buffers alive while bound. `nrCommand` returns 0 accepted, 1 catch-up pending, or -1 rejected. Inspect `nrError` immediately on failure. Input edits commit independently of decorative impulse capacity.

For a growable payload, query the required size, allocate disjoint aligned storage, install it and retry only the corresponding storage-required operation. Do not free the previous allocation until replacement succeeds. Prompt, model, modal and presentation scratch use separate APIs. Imported model records use signed Q8 XYZ coordinates and packed RGB.

Snapshot size is `nrSnapshotSizeFor(ctx)`; never hard-code a private State size. Save/load use pointer-free wire data with length/schema/CRC validation. A CRC checks corruption, not authenticity. `nrInfoPage` copies complete UTF-8 metadata; serialize all context calls during paging and decode only after reassembly.

## Frames and queries

`nrRender` returns the number of cells; `nrCells` is a borrowed view. Each `NrCell` has four 32-bit words: Unicode scalar, foreground RGB, background RGB and semantic ID. Query outputs specify capacities in rows, scalars, doubles or bytes; use each signature's contract, not a generic byte assumption. Most pure queries return a count or present/absent status, with -1 for invalid input; short outputs remain untouched where documented.

The declarations below are taken from the public header. They include pure geometry/text functions as well as retained scene queries.

## Public declarations

```c
int nrNegotiateShortcuts(const uint32_t*,uint32_t,const uint32_t*,uint32_t, const uint32_t*,uint32_t,uint32_t*,uint32_t);
```

```c
int nrWaveSample(const double*,uint32_t,double,double,double,double*,uint32_t);
```

```c
int nrHullImmersion(const double*,uint32_t,const uint32_t*,uint32_t,double,double*,uint32_t);
```

```c
int nrHullImmersionPlane(const double*,uint32_t,const uint32_t*,uint32_t, const double *point,const double *normal,double*,uint32_t);
```

```c
int nrHullBuoyancy(const double *vertices, uint32_t vertexCount, const uint32_t *faces, uint32_t triangleCount, double height, double density, double gravity, double mass, const double *centerOfMass, double *out, uint32_t capacity);
```

```c
int nrHullBuoyancyPlane(const double*,uint32_t,const uint32_t*,uint32_t, const double *point,const double *normal, double density,double gravity,double mass, const double *centerOfMass,double*,uint32_t);
```

```c
int nrHullMeshImmersion(const double*,uint32_t,const uint32_t*,uint32_t, const double *water,uint32_t waterCount,double*,uint32_t);
```

```c
int nrAngularDragExchange(const double *bodyInertia,const double *waterInertia, const double *conductance,double seconds, const double *bodyOmega,const double *waterOmega, double *out,uint32_t capacity);
```

```c
int nrSurfaceFluidAngular(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrFluidDragExchange(double bodyMass,double waterMass,double conductance, double seconds,const double *bodyVelocity, const double *waterVelocity,double*,uint32_t);
```

```c
int nrPathSample(const double*,uint32_t,int,int,double,double*,uint32_t);
```

```c
int nrSurfaceFoam(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrSurfaceFoamTransport(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrThermalSample(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrFieldSample(const NrContext*,uint32_t,double,double,double*,uint32_t);
```

```c
int nrPromptLayout(const NrContext*,double*,uint32_t);
```

```c
int nrPromptVisualLayout(const NrContext*,double*,uint32_t);
```

```c
int nrAreaGeometry(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrWaterSample(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrFlowThickness(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrSurfaceTriangles(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrTextRunClusters(const NrContext*,uint32_t,uint32_t,uint32_t*,uint32_t);
```

```c
int nrFloatBody(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrFloatHull(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrSurfaceFluid(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrSurfaceWaveSample(const NrContext*,uint32_t,double,double,double*,uint32_t);
```

```c
int nrLineBreaks(const uint32_t*,uint32_t,uint32_t*,uint32_t);
```

```c
int nrLineBreakDetails(const uint32_t*,uint32_t,uint32_t*,uint32_t);
```

```c
int nrGraphemeBreaks(const uint32_t *text, uint32_t count, uint32_t *out, uint32_t capacity);
```

```c
int nrScriptRuns(const uint32_t*,uint32_t,uint32_t*,uint32_t);
```

```c
int nrGraphemeWidths(const uint32_t *text,uint32_t count,uint32_t ambiguous, uint32_t *out,uint32_t capacity);
```

```c
int nrGraphemeLayout(const uint32_t *text,uint32_t count,uint32_t ambiguous, uint32_t columns,uint32_t *out,uint32_t capacity);
```

```c
int nrGraphemeHit(const uint32_t *text,uint32_t count,uint32_t ambiguous, uint32_t columns,uint32_t column,uint32_t row);
```

```c
int nrTextRunLayout(NrContext *ctx,uint32_t kind,uint32_t id,uint32_t ambiguous, uint32_t columns,uint32_t *out,uint32_t capacity);
```

```c
int nrTextRunSource(NrContext *ctx,uint32_t kind,uint32_t id,uint32_t *out,uint32_t capacity);
```

```c
int nrTextRunHit(NrContext *ctx,uint32_t kind,uint32_t id,uint32_t ambiguous, uint32_t columns,uint32_t column,uint32_t row);
```

```c
int nrTextRunClip(NrContext *ctx,uint32_t kind,uint32_t id,uint32_t ambiguous, uint32_t columns,uint32_t x,uint32_t y,uint32_t width,uint32_t height, uint32_t *out,uint32_t capacity);
```

```c
int nrBidiClass(uint32_t scalar);
```

```c
int nrBidiBracket(uint32_t scalar,uint32_t *out,uint32_t capacity);
```

```c
int nrBidiMirror(uint32_t scalar);
```

```c
int nrBidiParagraphLevel(const uint32_t *text,uint32_t count,uint32_t fallback);
```

```c
int nrBidiExplicit(const uint32_t *text,uint32_t count,uint32_t direction, uint32_t *out,uint32_t capacity);
```

```c
int nrBidiWeak(const uint32_t *text,uint32_t count,uint32_t direction, uint32_t *out,uint32_t capacity);
```

```c
int nrBidiLevels(const uint32_t *text,uint32_t count,uint32_t direction, uint32_t *out,uint32_t capacity);
```

```c
int nrBidiVisual(const uint32_t *text,uint32_t count,uint32_t direction, uint32_t *out,uint32_t capacity);
```

```c
int nrDocumentBidiClusterLayout(const uint32_t *text,uint32_t count,uint32_t ambiguous, uint32_t columns,uint32_t direction,uint32_t *out,uint32_t capacity, uint32_t *scratch,uint64_t scratchWords);
```

```c
int nrBidiClusterLayout(const uint32_t *text,uint32_t count,uint32_t ambiguous, uint32_t columns,uint32_t direction,uint32_t *out,uint32_t capacity);
```

```c
int nrBidiClusterLines(const uint32_t *text,uint32_t count,const uint32_t *ends, uint32_t lines,uint32_t direction,uint32_t *out,uint32_t capacity);
```

```c
int nrBidiClusterHit(const uint32_t *text,uint32_t count,uint32_t ambiguous, uint32_t columns,uint32_t direction,uint32_t column,uint32_t row);
```

```c
int nrBidiCaret(const uint32_t *text,uint32_t count,uint32_t ambiguous,uint32_t columns, uint32_t direction,uint32_t offset,uint32_t affinity,uint32_t *out,uint32_t capacity);
```

```c
uint32_t nrContextSize(void);
```

```c
int nrPromptSelection(NrContext *context,uint32_t *out,uint32_t capacity);
```

```c
uint64_t nrRenderMemorySize(const NrContext *ctx);
```

```c
uint64_t nrRenderMemoryCapacity(const NrContext *ctx);
```

```c
int nrSetRenderMemory(NrContext *ctx,void *memory,uint64_t capacity);
```

```c
uint64_t nrModelMemorySize(const NrContext *ctx);
```

```c
uint64_t nrModelMemoryCapacity(const NrContext *ctx);
```

```c
int nrSetModelMemory(NrContext *ctx,void *memory,uint64_t capacity);
```

```c
int nrModelSet(NrContext *ctx,const NrModelTriangle *triangles,uint32_t count);
```

```c
uint32_t nrModelTriangleCount(const NrContext *ctx);
```

```c
int nrModelCopy(const NrContext *ctx,NrModelTriangle *out,uint32_t capacity);
```

```c
int nrInit(void *memory, uint32_t capacity, uint32_t seed);
```

```c
int nrCommand(NrContext *ctx, const char *json, uint32_t length);
```

```c
uint64_t nrModalMemorySize(const NrContext *ctx);
```

```c
uint64_t nrModalMemoryCapacity(const NrContext *ctx);
```

```c
int nrSetModalMemory(NrContext *ctx, void *memory, uint64_t bytes);
```

```c
uint32_t nrRender(NrContext *ctx);
```

```c
const NrCell *nrCells(const NrContext *ctx);
```

```c
int nrInspectCharacterCell(const NrContext*,int32_t x,int32_t y,NrCharacterCellInfo*,uint32_t capacity);
```

```c
uint32_t nrWidth(const NrContext *ctx);
```

```c
uint32_t nrHeight(const NrContext *ctx);
```

```c
const char *nrInfo(NrContext *ctx);
```

```c
int nrInfoPage(NrContext *ctx, uint32_t offset, void *destination, uint32_t capacity, uint32_t *words, uint32_t wordCapacity);
```

```c
const char *nrError(const NrContext *ctx);
```

```c
uint32_t nrSnapshotSize(void);
```

```c
uint32_t nrSnapshotSizeFor(const NrContext *ctx);
```

```c
uint64_t nrPromptMemorySize(const NrContext *ctx);
```

```c
uint64_t nrPromptMemoryCapacity(const NrContext *ctx);
```

```c
int nrSetPromptMemory(NrContext *ctx,void *memory,uint64_t capacity);
```

```c
int nrSave(const NrContext *ctx, void *destination, uint32_t capacity);
```

```c
int nrLoad(NrContext *ctx, const void *source, uint32_t length);
```

```c
uint32_t nrOklch(int32_t lightness, int32_t chroma, int32_t hue);
```

```c
const char *nrCatalogue(void);
```

```c
int nrComposite(uint32_t base, uint32_t source, uint32_t baseAlpha, uint32_t sourceAlpha, uint32_t blend, uint32_t operation, uint32_t seed, uint32_t *out);
```

```c
int nrCompositeInSpace(uint32_t base, uint32_t source, uint32_t baseAlpha, uint32_t sourceAlpha, uint32_t blend, uint32_t operation, uint32_t seed, uint32_t space, uint32_t *out);
```

```c
int nrParticle(const NrContext *ctx, uint32_t index, int32_t *words, uint32_t capacity);
```

```c
int nrParticleMotion(const NrContext*,uint32_t,double*,uint32_t);
```

```c
int nrWindowSample(const NrContext *ctx, uint32_t id, uint32_t u, uint32_t v, uint32_t visibility, int32_t *words, uint32_t capacity);
```

```c
int nrTextTrailSample(const NrContext *ctx,uint32_t id,uint32_t glyphIndex, uint32_t trailIndex,int32_t *words,uint32_t capacity);
```

```c
int nrTextSample(const NrContext *ctx, uint32_t id, uint32_t index, int32_t *words, uint32_t capacity);
```

```c
int nrTextClusterSample(const NrContext *ctx, uint32_t id, uint32_t index, int32_t *words, uint32_t capacity);
```

```c
uint32_t nrSourceStageOklch(int32_t lightness,int32_t chroma,int32_t hue);
```


[Common command field reference](Commands.md).
