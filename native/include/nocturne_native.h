#ifndef NOCTURNE_NATIVE_H
#define NOCTURNE_NATIVE_H
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Current native contract, ABI 1. No clock, devices, file I/O or subprocesses.
 * All calls on a context must be serialized. Returned views are borrowed until
 * the next call; language bindings copy them. Initialize caller-owned, 8-byte
 * aligned memory of nrContextSize() bytes. Unknown commands fail transactionally.
 * World: +X right, +Y up, +Z toward default viewer. View looks along -Z.
 * Canonical cells: four little-endian u32 words (scalar, fgRGB, bgRGB, semanticID).
 */
#define NR_ABI_VERSION 1u
#define NR_MAX_COMMAND 1048576u
#define NR_INFO_PAGE_MAX 65536u
#define NR_MAX_PARTICLES 2048u
#define NR_MAX_EMITTERS 16u
#define NR_MAX_SURFACES 16u
#define NR_MAX_FLOAT_BODIES 64u
#define NR_MAX_MESH_TRIANGLES 256u
#define NR_MAX_COLLISION_CONTACTS 4u
#define NR_MAX_WINDOWS 32u
#define NR_MAX_NODES 64u
#define NR_MAX_TEXT 2048u
#define NR_MAX_PROMPT 65536u

/** nr-shortcut-negotiation-v1. Pure host-owned tables: <=64 distinct nonzero
 * action IDs; <=256 candidate rows [action,key,modifiers]; <=256 unique host
 * rows [key,modifiers,reserved]. Keys: Unicode nonzero scalars or host-normalized
 * special codes 0x110000..0x11ffff. Modifiers: Shift1 Control2 Alt4 Meta8.
 * Reserved is 0/1; omitted or reserved chords cannot be assigned. Candidate
 * order is preference order. Deterministic maximum-cardinality matching may
 * relocate assignments; no global lexicographic preference guarantee.
 * Output rows [action,key,modifiers,assigned], in action order; unassigned 0s.
 * Capacity counts rows; NULL/0 probes. All arrays aligned to 4 bytes. Invalid
 * or short output untouched; input/output aliasing is allowed. No dispatch,
 * key delivery inference, context mutation, or hidden host defaults. */
int nrNegotiateShortcuts(const uint32_t*,uint32_t,const uint32_t*,uint32_t,
                        const uint32_t*,uint32_t,uint32_t*,uint32_t);

/** nr-wave-height-field-v1. Up to 32 binary64 wave rows
 * [amplitude, kX, kZ, angularFrequency, phaseRadians]. World units and seconds.
 * Returns [height, normalX, normalY, normalZ, verticalVelocity, LaplacianHeight].
 * All scalars finite and within +/-1e6; arrays 8-byte aligned. Zero waves is flat.
 * Output needs six doubles. Pure; returns 1 or -1 leaving output untouched.
 * This analytic field is not a nonlinear fluid or horizontal displacement model. */
int nrWaveSample(const double*,uint32_t,double,double,double,double*,uint32_t);
/** Pure closed convex hull immersion below horizontal water height.
 * XYZ vertices (4..128), outward u32 triangle rows (4..256), finite world
 * coordinates/height within +/-1e6. Five doubles: full volume, submerged volume,
 * submerged centroid XYZ (zeros if dry). Capacity doubles >=5; arrays aligned
 * 8/4/8. Returns 1 valid, -1 invalid, output untouched on rejection.
 * Input/output aliasing allowed. No retained body or nonlinear-wave coupling. */
int nrHullImmersion(const double*,uint32_t,const uint32_t*,uint32_t,double,double*,uint32_t);
/** Same result for the half-space dot(normal, vertex - point) <= 0.
 * Point and normal each contain three aligned doubles within +/-1e6. Normal
 * length must be >=1e-12; normalization is native and does not alter input.
 * Output capacity, aliasing, validation and rejection follow nrHullImmersion. */
int nrHullImmersionPlane(const double*,uint32_t,const uint32_t*,uint32_t,
                         const double *point,const double *normal,double*,uint32_t);
/** Pure convex hull hydrostatic wrench about centerOfMass in world coordinates.
 * Inputs follow nrHullImmersion. density 0..100000, gravity 0..256, mass
 * .001..1000000, center XYZ finite +/-1e6. Eleven doubles: full volume,
 * submerged volume, submerged centroid XYZ, net force XYZ (including gravity),
 * torque XYZ. Lift is vertical. Gravity has zero moment about centerOfMass.
 * Capacity is in doubles; alignment 8. Returns 1 or -1 with untouched output.
 * Input/output aliasing is supported; this call does not integrate motion. */
int nrHullBuoyancy(const double *vertices, uint32_t vertexCount,
                   const uint32_t *faces, uint32_t triangleCount,
                   double height, double density, double gravity, double mass,
                   const double *centerOfMass, double *out, uint32_t capacity);
/** Oriented-plane displacement with the same eleven-word wrench profile.
 * Plane point/normal follow nrHullImmersionPlane. Lift remains vertical;
 * this is a displaced-volume model, not a sloped hydrostatic equilibrium or
 * dynamic pressure solver. Torque uses the exact clipped-volume centroid.
 * Other domains, capacity, ownership and rejection follow nrHullBuoyancy. */
int nrHullBuoyancyPlane(const double*,uint32_t,const uint32_t*,uint32_t,
                        const double *point,const double *normal,
                        double density,double gravity,double mass,
                        const double *centerOfMass,double*,uint32_t);
/** Pure convex hull immersion in a piecewise planar water mesh.
 * Water contains 1..256 nine-double XYZ triangle rows, finite +/-1e6.
 * Projected XZ triangles must have nonzero area and disjoint interiors.
 * Vertical columns are clipped below each triangle's plane; outside coverage
 * is dry. Five result words and hull validity follow nrHullImmersion. Reversed
 * water winding is accepted; overlapping water footprints reject atomically.
 * This integrates the provided mesh, not an untriangulated analytic wave. */
int nrHullMeshImmersion(const double*,uint32_t,const uint32_t*,uint32_t,
                        const double *water,uint32_t waterCount,double*,uint32_t);
/** Exact diagonal angular drag exchange in a caller-specified shared frame.
 * Inertia XYZ arrays use .001..1e12; conductance XYZ uses 0..1e12.
 * Angular velocities use +/-1e6; seconds 0..86400. Ten-double output:
 * body omega XYZ, water omega XYZ, angular impulse to water XYZ, dissipated
 * rotational energy. Eight-byte alignment; input/output aliasing supported.
 * Returns 1 or -1 leaving output untouched. Does not rotate inertia tensors,
 * retain a reservoir, advance time or integrate body orientation. */
int nrAngularDragExchange(const double *bodyInertia,const double *waterInertia,
                         const double *conductance,double seconds,
                         const double *bodyOmega,const double *waterOmega,
                         double *out,uint32_t capacity);
typedef struct NrContext NrContext;
/** Pure retained angular fluid row: inertia, omega XYZ, initial angular
 * momentum XYZ, body angular impulse XYZ, dissipated/initial rotational energy.
 * Capacity >=12 doubles, alignment 8, context overlap forbidden. Returns
 * 1 present, 0 absent, -1 invalid; absent/invalid output stays untouched. */
int nrSurfaceFluidAngular(const NrContext*,uint32_t,double*,uint32_t);
/** Pure exact linear drag exchange between finite body and water masses.
 * Masses .001..1e12; conductance kg/s 0..1e12; seconds 0..86400.
 * Input velocities XYZ finite +/-1e6. Ten doubles: body velocity XYZ,
 * water velocity XYZ, impulse delivered to water XYZ, dissipated energy.
 * Momentum is exchanged reciprocally; dissipation is nonnegative. Capacity
 * >=10 doubles, alignment 8. Returns 1 or -1 untouched on rejection.
 * Input/output aliasing allowed. Does not retain or integrate scene state. */
int nrFluidDragExchange(double bodyMass,double waterMass,double conductance,
                        double seconds,const double *bodyVelocity,
                        const double *waterVelocity,double*,uint32_t);
/** Pure arc-length path sample: position XYZ, travel tangent XYZ, total length,
 * resolved distance. Points are count XYZ rows; closed is 0/1, mode is
 * 0 clamp, 1 loop, 2 reverse. Capacity is doubles (>=8). Invalid stays untouched. */
int nrPathSample(const double*,uint32_t,int,int,double,double*,uint32_t);
/* Context scenic inspection outputs (foam/transport, flow thickness/triangles,
 * float bodies and named-surface wave samples) must not overlap NrContext memory.
 * Wrapping address ranges reject before writes. Bounds use actual output bytes,
 * not unused capacity. This preserves query purity even at the raw C ABI. */
/** Pure foam rows: triangle index, density, generated, decayed, saturated.
 * Capacity counts five-double rows, not scalars. NULL/zero probes row count.
 * Returns row count or -1 invalid; short output stays untouched. Alignment 8. */
int nrSurfaceFoam(const NrContext*,uint32_t,double*,uint32_t);
/** Pure seven-double rows: triangle, density, generated, decayed, saturated,
 * incoming, outgoing. Capacity counts rows. NULL/zero probes count; invalid or
 * short output stays untouched. Alignment 8. See SURFACE-FOAM.md for balance. */
int nrSurfaceFoamTransport(const NrContext*,uint32_t,double*,uint32_t);
/** Pure thermal cell sample by current triangle index. Ten doubles: temperature,
 * energy, initialEnergy, appliedEnergy, environmentEnergy, importedEnergy,
 * transferredEnergy, capacity, power, ambientTemperature. Returns 1 configured,
 * 0 unconfigured, -1 invalid. Capacity counts doubles; alignment 8; outputs may
 * not overlap context. Absent/invalid/short outputs stay untouched. */
int nrThermalSample(const NrContext*,uint32_t,double*,uint32_t);
/* Pure global screen-cell query. Four doubles: intensity, RGB, centerX, centerY.
 * 1 present,0 absent,-1 invalid; absent/invalid leave output unchanged. */
int nrFieldSample(const NrContext*,uint32_t,double,double,double*,uint32_t);
/* Pure declared geometry, including offscreen/empty areas; twelve doubles:
 * origin/size, viewport+ancestor+owner clip, content origin/size. */
/* Owned prompt cluster rows: start,end,column,row,width,screenX,screenY,visible.
 * Capacity counts8-double rows; NULL/0 probes. Pure; scalar presentation returns0. */
int nrPromptLayout(const NrContext*,double*,uint32_t);
/** Pure owned visual prompt rows: start,end,column,row,width,screenX,screenY,
 * visible,level,mappedFirstScalar. Capacity counts ten-double rows. */
int nrPromptVisualLayout(const NrContext*,double*,uint32_t);
int nrAreaGeometry(const NrContext*,uint32_t,double*,uint32_t);
/** Pure water cell sample by triangle index. Eight doubles: surfaceId,
 * receivedVolume (excluding imports), retainedVolume, wetness, importedVolume,
 * transferredVolume, evaporatedVolume, capacity. Returns 1 configured, 0 absent,
 * -1 invalid. Capacity is doubles (>=8); alignment 8; no context overlap.
 * Absent/invalid/short outputs stay untouched. */
int nrWaterSample(const NrContext*,uint32_t,double*,uint32_t);
/** Pure six doubles: flux, depth, cross-section area, width, speed, maxDepth.
 * Return 1 present, 0 absent, -1 invalid. Short/invalid buffers stay untouched. */
int nrFlowThickness(const NrContext*,uint32_t,double*,uint32_t);
/** Pure sampled surface geometry: 12 doubles per row, triangle index, three XYZ
 * vertices, RGB24, alpha. NULL/zero counts rows. Short output stays untouched. */
int nrSurfaceTriangles(const NrContext*,uint32_t,double*,uint32_t);
/** Pure four-u32 rows: persistent identity, scalar start/end, run generation.
 * Kinds 0 prompt/id0, 1 animated text, 2 window body, 3 title.
 * Capacity counts rows; NULL/zero probes count. Short/invalid output unchanged. */
int nrTextRunClusters(const NrContext*,uint32_t,uint32_t,uint32_t*,uint32_t);
/** Pure owned inspection: position XYZ, velocity XYZ, sampled normal XYZ,
 * immersion fraction, last buoyant force, mass. Twelve binary64 outputs.
 * Returns 1 for present, 0 absent (output untouched), -1 invalid (untouched).
 * Caller output requires 8-byte alignment and capacity >=12. */
int nrFloatBody(const NrContext*,uint32_t,double*,uint32_t);
/** Pure retained hull pose: quaternion XYZW, local angular velocity XYZ,
 * local principal inertia XYZ, local center of mass XYZ, full volume.
 * Capacity >=14 doubles, alignment 8; context overlap/wrapping reject.
 * Returns 1 attached, 0 absent, -1 invalid; absent/invalid output untouched.
 * Bindings return owned copies; this query never integrates motion. */
int nrFloatHull(const NrContext*,uint32_t,double*,uint32_t);
/** Pure finite-water record: mass, velocity XYZ, offset XYZ, initial momentum
 * XYZ, received body impulse XYZ, dissipated energy, initial kinetic energy.
 * Capacity >=15 doubles/alignment 8. Returns 1 configured, 0 absent, -1 invalid;
 * absent/invalid output untouched. Context overlap and wrapping reject.
 * Stopped records remain present; metadata surfaceFluids[].active identifies
 * lifecycle. A stopped record's velocity is its preserved final velocity. */
int nrSurfaceFluid(const NrContext*,uint32_t,double*,uint32_t);
/** Owned/pure six-double surface sample at world XZ: height, normal XYZ,
 * vertical velocity, Laplacian. A pose-backed finite reservoir samples its
 * topmost rendered facet: upward world normal, material Y velocity and zero
 * within-facet Laplacian. Vertical/uncovered facets return -1 unchanged.
 * Without a retained pose, the existing translated analytic wave field applies.
 * Capacity >=6, alignment 8; context overlap rejects. Metadata queryContracts
 * declares both modes and surfaceFluidAngular[].pose selects the posed mode. */
int nrSurfaceWaveSample(const NrContext*,uint32_t,double,double,double*,uint32_t);
typedef struct NrCell { uint32_t glyph, foreground, background, id; } NrCell;
/** Candidate Unicode-17 UAX14-55 scalar break opportunities. Returns offset
 * count, including end-of-text; null output/capacity zero probes required count.
 * Maximum 2048 valid Unicode scalars. Capacity is u32 offsets, alignment 4.
 * Invalid input or short output returns -1 without writing; aliasing is allowed.
 * This raw scalar profile is separate from host grapheme-safe line selection. */
int nrLineBreaks(const uint32_t*,uint32_t,uint32_t*,uint32_t);
/** Same candidate scalar profile, with two-u32 rows [offset, mandatory].
 * Mandatory is 1 for hard breaks/end-of-text, 0 for optional opportunities.
 * Capacity/probe result counts rows, alignment 4; owned/atomic/alias-safe. */
int nrLineBreakDetails(const uint32_t*,uint32_t,uint32_t*,uint32_t);
/** Unicode 17.0.0 UAX29-47 extended grapheme boundaries in scalar offsets.
 * Pure streaming traversal; accepts all valid Unicode scalars.
 * Input/output must not overlap; storage and the int return representation bound size.
 * Returns boundary count including 0/end, or -1 without touching output.
 * NULL output with zero capacity probes required count. Empty input yields [0]. */
int nrGraphemeBreaks(const uint32_t *text, uint32_t count, uint32_t *out, uint32_t capacity);
/** Pure nr-script-grapheme-v1 itemization using Unicode 17 Script/Extensions.
 * UTF32 input up to NR_MAX_TEXT; rows are start/end scalar offsets and ISO15924
 * tag encoded in big-endian ASCII u32. Whole graphemes never split; mixed-script
 * graphemes use first strong script. Common/Inherited use compatible preceding
 * context, then following context, then deterministic ISO tag order; unresolved
 * neutral text is Zyyy. Capacity counts rows. NULL/zero probes count. Returns
 * row count or -1 untouched for invalid/short input. Alignment 4; aliases allowed.
 * No font, language, bidi or shaping inference occurs in this query. */
int nrScriptRuns(const uint32_t*,uint32_t,uint32_t*,uint32_t);

/** Pure nr-grapheme-cell-width-v1 / Unicode 17 width rows: start scalar offset,
 * end scalar offset, columns (0..2). Ambiguous width must be 1 or 2; capacity
 * counts rows, each requiring THREE uint32 words. NULL/0 probes row count.
 * Up to 2048 scalars; returns row count or -1 leaving output untouched.
 * Explicit metric policy, not a font/shaping or host display guarantee. */
int nrGraphemeWidths(const uint32_t *text,uint32_t count,uint32_t ambiguous,
                     uint32_t *out,uint32_t capacity);
/** Pure nr-grapheme-layout-v1 rows: start/end scalar, column, row, width.
 * Positive columns; soft wraps never split clusters. A two-column cluster in
 * one column retains width two for explicit host clipping. Tabs use stops of
 * four (bounded by columns); CR/LF/CRLF/NEL/LS/PS break lines. Capacity counts
 * FIVE-word rows; NULL/0 probes. Invalid input returns -1, output untouched. */
int nrGraphemeLayout(const uint32_t *text,uint32_t count,uint32_t ambiguous,
                     uint32_t columns,uint32_t *out,uint32_t capacity);
/** Pure nr-grapheme-hit-v1: nearest source cluster boundary in logical layout.
 * Uses nrGraphemeLayout width/wrap policy; row proximity precedes column.
 * Equal distances choose the later scalar boundary. Newline ends map to the
 * following row. Empty valid input returns zero; invalid input returns -1.
 * Does not mutate a context, split a cluster, shape glyphs or reorder bidi text. */
int nrGraphemeHit(const uint32_t *text,uint32_t count,uint32_t ambiguous,
                  uint32_t columns,uint32_t column,uint32_t row);
/** nr-text-run-layout-v1: context source kinds 0 prompt (id 0), 1 authored
 * text, 2 window body, 3 window title. IDs remain authored IDs through reflow
 * and retargeting; (kind,id) is the stable run key, not a cluster identity.
 * Pure seven-word rows: id,start,end,column,row,width,kind. Logical Unicode 17
 * grapheme layout; no bidi/shaping. Capacity counts rows; NULL/0 probes.
 * Missing source, invalid policy or short/overlapping output rejects untouched.
 * Source access remains available when hidden or another owner has input focus. */
int nrTextRunLayout(NrContext *ctx,uint32_t kind,uint32_t id,uint32_t ambiguous,
                    uint32_t columns,uint32_t *out,uint32_t capacity);
/** Pure owned-source export for the same run key; capacity counts scalars.
 * NULL/0 probes length; empty existing run returns 0, missing run returns -1. */
int nrTextRunSource(NrContext *ctx,uint32_t kind,uint32_t id,uint32_t *out,uint32_t capacity);
/** Pure hit mapping into the same context-owned logical run layout. Returns
 * the nearest whole-cluster scalar boundary; -1 for missing/invalid source.
 * Coordinates are local logical layout coordinates, not projected screen XY. */
int nrTextRunHit(NrContext *ctx,uint32_t kind,uint32_t id,uint32_t ambiguous,
                 uint32_t columns,uint32_t column,uint32_t row);
/** Pure logical viewport intersection, preserving complete source clusters.
 * Nine-word rows: id,start,end,column,row,width,kind,clipLeft,clipWidth.
 * Last two fields describe visible columns relative to the original cluster.
 * Zero-width clusters have no painted footprint. Rectangle sums use 64 bits;
 * empty/offscreen rectangles return zero. NULL/0 probes; capacity counts rows.
 * Invalid/short/overlapping output rejects untouched. No source truncation. */
int nrTextRunClip(NrContext *ctx,uint32_t kind,uint32_t id,uint32_t ambiguous,
                  uint32_t columns,uint32_t x,uint32_t y,uint32_t width,uint32_t height,
                  uint32_t *out,uint32_t capacity);
/** Unicode 17 bidi properties, independent of context and host Unicode data.
 * Classes: L=0 R=1 AL=2 EN=3 AN=4 ES=5 ET=6 CS=7 NSM=8 BN=9 B=10 S=11
 * WS=12 ON=13 LRE=14 LRO=15 RLE=16 RLO=17 PDF=18 LRI=19 RLI=20 FSI=21 PDI=22.
 * Invalid Unicode scalars return -1. These properties do not resolve/reorder text. */
int nrBidiClass(uint32_t scalar);
/** Writes [paired scalar,type(open=1,close=2)], returns 1 for a paired bracket,
 * 0 for none (output untouched), -1 for invalid scalar/output (untouched). */
int nrBidiBracket(uint32_t scalar,uint32_t *out,uint32_t capacity);
/** Mirrored glyph scalar, or the original when absent; -1 for invalid scalar. */
int nrBidiMirror(uint32_t scalar);
/** UAX9 P2/P3 first paragraph base direction. First strong L/R/AL outside
 * isolate contents determines 0/1; fallback must be 0 or 1. Validates all
 * scalars, bounded to NR_MAX_TEXT; invalid input returns -1. Pure. */
int nrBidiParagraphLevel(const uint32_t *text,uint32_t count,uint32_t fallback);
/** UAX9 X1-X9 explicit stage, before weak/neutral/implicit resolution.
 * Four-word scalar rows: original class, overridden class, explicit level,
 * X9 removed flag. direction: 0 LTR, 1 RTL, 2 auto per paragraph (fallback LTR).
 * Removed formatting rows retain their pre-operation level for source mapping.
 * NULL/0 probes; capacity counts rows. Invalid input/output rejects untouched.
 * Max 2048 scalars; pure, bounded stack with UAX9 max explicit depth 125. */
int nrBidiExplicit(const uint32_t *text,uint32_t count,uint32_t direction,
                    uint32_t *out,uint32_t capacity);
/** UAX9 through X10/W1-W7, before neutral/bracket/implicit resolution.
 * Seven-word scalar rows: original class, weak-resolved class, explicit level,
 * removed flag, sequence key(first source index), sos, eos. Removed rows have
 * UINT32_MAX sequence key. direction and capacity follow nrBidiExplicit.
 * Invalid input/output rejects untouched; pure and bounded to 2048 scalars. */
int nrBidiWeak(const uint32_t *text,uint32_t count,uint32_t direction,
                uint32_t *out,uint32_t capacity);
/** UAX9 through N0-N2/I1-I2: seven-word rows follow nrBidiWeak, but class
 * and level are now resolved. Does not apply line reset or visual reordering.
 * Bracket pairing is bounded to 63 opens and honors canonical equivalents.
 * NULL/0 probes; invalid input/output rejects untouched. Pure. */
int nrBidiLevels(const uint32_t *text,uint32_t count,uint32_t direction,
                  uint32_t *out,uint32_t capacity);
/** UAX9 scalar visual order with L1/L2 and mapped mirroring. Treats each
 * paragraph as one unwrapped line. Four-word visual rows: source scalar index,
 * resolved class, reset level, mapped display scalar. X9 removed rows omitted.
 * Returns retained row count; NULL/0 probes. Invalid input/output rejects
 * untouched. Does not shape glyphs or preserve clusters as visual glyph units. */
int nrBidiVisual(const uint32_t *text,uint32_t count,uint32_t direction,
                  uint32_t *out,uint32_t capacity);
/** nr-bidi-grapheme-layout-v1: logical Unicode 17 cluster wrapping, then
 * L1/L2 reordering of whole clusters on each line. Seven-word visual rows:
 * start,end,column,row,width,level,mapped first retained scalar. Internal source
 * order is preserved; all-X9-removed clusters are omitted. Tabs retain logical
 * advances; columns use the existing cell metric, not shaped font metrics.
 * NULL/0 probes; capacity counts rows, invalid input/output rejects untouched. */
/* Whole-document equivalent with growing caller-owned workspace. No authored
 * text ceiling; count is addressable through INT32_MAX. Source, output and
 * scratch must be disjoint. Scratch needs 40*(count+1) uint32 words. Invalid
 * input leaves output unchanged. Output rows retain the seven-word bidi ABI. */
int nrDocumentBidiClusterLayout(const uint32_t *text,uint32_t count,uint32_t ambiguous,
    uint32_t columns,uint32_t direction,uint32_t *out,uint32_t capacity,
    uint32_t *scratch,uint64_t scratchWords);
int nrBidiClusterLayout(const uint32_t *text,uint32_t count,uint32_t ambiguous,
                        uint32_t columns,uint32_t direction,uint32_t *out,uint32_t capacity);
/** Caller-selected font line boundaries with full-paragraph bidi resolution.
 * ends contains strictly increasing scalar line ends covering all input, at
 * whole grapheme boundaries. A line cannot cross a structural hard break.
 * Seven-word visual rows follow nrBidiClusterLayout; columns/widths remain cell
 * annotations, not font advances. L1/L2 are applied separately to chosen lines.
 * Empty input uses zero lines. NULL/0 output probes; atomic invalid/short output.
 * Input, line-end and output arrays may alias. */
int nrBidiClusterLines(const uint32_t *text,uint32_t count,const uint32_t *ends,
                      uint32_t lines,uint32_t direction,uint32_t *out,uint32_t capacity);
/** Visual nearest whole-cluster source boundary in nr-bidi-grapheme-layout-v1.
 * Row proximity precedes column; ties choose the later logical source offset.
 * Odd-level cluster edges reverse source start/end. Invalid input returns -1. */
int nrBidiClusterHit(const uint32_t *text,uint32_t count,uint32_t ambiguous,
                     uint32_t columns,uint32_t direction,uint32_t column,uint32_t row);
/** Pure caret [column,row,level] for a grapheme source boundary. Affinity 0
 * prefers preceding cluster end; 1 prefers following cluster start. Uses the
 * available edge at document ends. Invalid/interior offset, missing visible
 * edge or short output rejects untouched. Returns 0 success, -1 rejection. */
int nrBidiCaret(const uint32_t *text,uint32_t count,uint32_t ambiguous,uint32_t columns,
                 uint32_t direction,uint32_t offset,uint32_t affinity,uint32_t *out,uint32_t capacity);
/** Required allocation size in bytes, including isolated simulation and scratch. */
uint32_t nrContextSize(void);
/** Pure selected scalar source export; zero for no range or non-prompt owner.
 * NULL/0 probes length; short/overlapping output rejects untouched (-1). */
int nrPromptSelection(NrContext *context,uint32_t *out,uint32_t capacity);
/** Presentation scratch follows the actual viewport, with no fixed dimension
 * ceiling. Required/current capacities in bytes; zero means invalid context.
 * Init supplies inline scratch for ordinary small frames. For larger frames,
 * bind caller-owned, 8-byte-aligned memory disjoint from the context and keep it
 * alive until replacement/context destruction. Set rejects short/overlapping
 * memory atomically. Buffers are presentation-only and excluded from snapshots.
 * Bindings grow automatically; the freestanding C core never allocates. */
uint64_t nrRenderMemorySize(const NrContext *ctx);
uint64_t nrRenderMemoryCapacity(const NrContext *ctx);
int nrSetRenderMemory(NrContext *ctx,void *memory,uint64_t capacity);
/* Original visual model records: signed Q8 coordinates and opaque sRGB.
 * Upload is one atomic operation, separate from JSON command transactions.
 * Caller storage is owned by the caller and must outlive the context binding. */
typedef struct {int32_t vertices[9];uint32_t color;} NrModelTriangle;
uint64_t nrModelMemorySize(const NrContext *ctx);
uint64_t nrModelMemoryCapacity(const NrContext *ctx);
int nrSetModelMemory(NrContext *ctx,void *memory,uint64_t capacity);
int nrModelSet(NrContext *ctx,const NrModelTriangle *triangles,uint32_t count);
uint32_t nrModelTriangleCount(const NrContext *ctx);
int nrModelCopy(const NrContext *ctx,NrModelTriangle *out,uint32_t capacity);
/** Initialize only after size/alignment checks. Returns 0 or -1; seed is explicit. */
int nrInit(void *memory, uint32_t capacity, uint32_t seed);
/** Apply one bounded UTF-8 JSON transaction. Returns 0, 1 (catch-up pending), or
 * -1. Rejected commands leave authoritative state unchanged. Input edits commit
 * independently of decorative impulse capacity. Examples are in COMMANDS.md. */
int nrCommand(NrContext *ctx, const char *json, uint32_t length);
/* Caller-owned, disjoint committed/trial/probe modal Unicode storage. */
uint64_t nrModalMemorySize(const NrContext *ctx);
uint64_t nrModalMemoryCapacity(const NrContext *ctx);
int nrSetModalMemory(NrContext *ctx, void *memory, uint64_t bytes);
/** Pure presentation: returns cell count, or 0 on invalid context. Rendering
 * changes scratch/diagnostics only, never simulation, queues, inputs or RNG keys. */
uint32_t nrRender(NrContext *ctx);
const NrCell *nrCells(const NrContext *ctx);
typedef struct {
    NrCell cell;
    uint32_t index;
    char role[129],state[129],path[128];
} NrCharacterCellInfo;
/** Pure inspection of the latest successful render. 0=success, -1=invalid
 * context/coordinate/output, -2=render required. Successful commands, restores
 * and render-memory replacement invalidate inspection. No implicit rendering.
 * Output (at least sizeof(NrCharacterCellInfo) bytes) is unchanged on failure. */
int nrInspectCharacterCell(const NrContext*,int32_t x,int32_t y,NrCharacterCellInfo*,uint32_t capacity);
uint32_t nrWidth(const NrContext *ctx);
uint32_t nrHeight(const NrContext *ctx);
/** JSON metadata (borrowed), including complete text, selection, counts, overflow
 * and clock state. No caller-supplied strings are executed or fetched. */
const char *nrInfo(NrContext *ctx);
/** Opt-in complete metadata, using the same JSON formatter as nrInfo.
 * Raw UTF-8 bytes, no NUL: pages may split a scalar. capacity <= NR_INFO_PAGE_MAX.
 * words[0..3] = total bytes, written bytes, next offset, full-stream IEEE CRC32.
 * Return 1 for more, 0 for done, -1 for invalid arguments; rejection preserves
 * caller outputs and authoritative state. Zero capacity permits NULL destination
 * for a size/checksum probe. offset==total is a valid empty final page.
 * Outputs must be caller-owned, disjoint from each other and the whole context;
 * words must be uint32-aligned with wordCapacity >= 4. No other words are changed.
 * Serialize ALL context calls across the entire read (including rendering).
 * Each page visits the whole stream: use 64 KiB pages for explicit recovery,
 * not animation-frame polling. CRC32 is a consistency check, not authentication.
 * Additive ABI-1 entry point; older cores need explicit feature detection. */
int nrInfoPage(NrContext *ctx, uint32_t offset, void *destination,
               uint32_t capacity, uint32_t *words, uint32_t wordCapacity);
const char *nrError(const NrContext *ctx);
/** Snapshot includes owned simulation, deposits, documents, motion, and triggers.
 * Wire header includes ABI/schema, length and CRC32. The current private writer
 * is reported by nrInfo's contract.snapshotSchema. Known older schema/length pairs have explicit validated
 * migrations; all unknown pairs reject. See API.md for exact source layouts. */
uint32_t nrSnapshotSize(void);
/** Exact pointer-free variable snapshot size of this context. */
uint32_t nrSnapshotSizeFor(const NrContext *ctx);
/** Caller-owned prompt storage. A rejected transaction requesting more storage
 * returns "Prompt storage required". Allocate Size bytes, install, and retry.
 * Install copies current authority; keep old memory alive until it succeeds. */
uint64_t nrPromptMemorySize(const NrContext *ctx);
uint64_t nrPromptMemoryCapacity(const NrContext *ctx);
int nrSetPromptMemory(NrContext *ctx,void *memory,uint64_t capacity);
int nrSave(const NrContext *ctx, void *destination, uint32_t capacity);
int nrLoad(NrContext *ctx, const void *source, uint32_t length);
/** Standalone pure OKLCh -> packed sRGB, with chroma reduction at fixed L/h.
 * Inputs: L,C in millionths, hue millidegrees. Reject invalid range with 0xffffffff. */
uint32_t nrOklch(int32_t lightness, int32_t chroma, int32_t hue);
/** Current native implementation catalogue. Historical IDs never dispatch here. */
const char *nrCatalogue(void);
/** Encoded RGB blend and independent Porter-Duff composition. out[0]=RGB,
 * out[1]=alpha (0..65535). 28 blend indices, 13 operators listed in API.md.
 * Invalid inputs return -1 without modifying output. No hidden matte applied. */
int nrComposite(uint32_t base, uint32_t source, uint32_t baseAlpha,
                uint32_t sourceAlpha, uint32_t blend, uint32_t operation,
                uint32_t seed, uint32_t *out);
/** Pure blend/composition with alpha interpolation in the chosen space:
 * 0=sRGB, 1=linear sRGB, 2=OKLab, 3=OKLCh (shorter hue route).
 * Blend algebra is encoded RGB; additive composition keeps its energy algebra.
 * Other arguments/output and atomic rejection match nrComposite. */
int nrCompositeInSpace(uint32_t base, uint32_t source, uint32_t baseAlpha,
                       uint32_t sourceAlpha, uint32_t blend, uint32_t operation,
                       uint32_t seed, uint32_t space, uint32_t *out);
/** Native scalar tests and bindings can inspect a particle without rendering.
 * Writes 12 int32 words: id, emitterID, state, XYZ Q16, velocity XYZ Q16,
 * bornStep, ageSteps, lifetimeSteps. Returns 1 for active, 0 for empty, -1 invalid. */
int nrParticle(const NrContext *ctx, uint32_t index, int32_t *words, uint32_t capacity);
/** Authored particle XYZ degrees and XYZ degrees/second; six binary64 outputs.
 * Returns 1 for authored active motion, 0 for legacy/empty, -1 invalid. Pure. */
int nrParticleMotion(const NrContext*,uint32_t,double*,uint32_t);
/** Inspect a current WindowTransition without rendering or changing time.
 * u, v and visibility are normalized millionths (0..1000000). Five output words:
 * local XYZ Q16, opacity millionths, mask coverage (0/1). */
int nrWindowSample(const NrContext *ctx, uint32_t id, uint32_t u, uint32_t v,
                   uint32_t visibility, int32_t *words, uint32_t capacity);
/** Pure current TextTransition inspection. Eight words: display scalar, source
 * scalar, stable scalar identity, x/y Q16, opacity millionths, hue millidegrees,
 * settled flag. This is the documented single-cell scalar layout profile. */
/* Read-only trail sample: identity,glyph,ordinal,xQ16,yQ16,opacity1e6,hue1e3,settled.
 * Indices are zero-based. Invalid requests leave the output buffer unchanged. */
int nrTextTrailSample(const NrContext *ctx,uint32_t id,uint32_t glyphIndex,
                     uint32_t trailIndex,int32_t *words,uint32_t capacity);
int nrTextSample(const NrContext *ctx, uint32_t id, uint32_t index,
                 int32_t *words, uint32_t capacity);
/** Pure Unicode-17 grapheme sample for an animated text run. Eight words:
 * persistent identity (u32 bits), source start/end scalar offsets, anchor XY Q16,
 * opacity millionths, hue millidegrees, settled. Index counts whole clusters.
 * Pose uses the cluster's first scalar; source is read through nrTextRunSource.
 * This does not perform font shaping or change legacy scalar rendering. */
int nrTextClusterSample(const NrContext *ctx, uint32_t id, uint32_t index,
                        int32_t *words, uint32_t capacity);
/* Pure original Stage formulas. Unknown C easing retains original linear fallback;
 * owned bindings restrict authored easing to0..3. Times have no hidden clock. */
/* Original integer color kernel: L/1000, C/10000, hue/1000 degrees. */
uint32_t nrSourceStageOklch(int32_t lightness,int32_t chroma,int32_t hue);
int32_t nrSourceStageTween(int32_t from,int32_t to,uint64_t elapsedMs,uint32_t durationMs,int32_t easing);
int32_t nrSourceStageInkOpacity(uint32_t ageMs,uint32_t fadeMs,int32_t rowQ8,int32_t bandQ8,int32_t topMinimum);
/* Current retained source nodes, reverse insertion order. Returns1 and writes
 * [original semantic ID,zero-based subitem],0 nohit,-1invalid. Outputcapacity
 * >=2 int32,alignment4,external to all context-owned storage. No-hit/invalid
 * preserve output. Does not render, advance time, or change context state. */
int32_t nrSourceStageHit(const NrContext*,int32_t x,int32_t y,int32_t*out,uint32_t capacity);
#ifdef __cplusplus
}
#endif
#endif
