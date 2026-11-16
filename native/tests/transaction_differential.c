/* Transaction differential (native/docs/TRANSACTIONS.md, "Verification").
 *
 * Loads two builds of the native library side by side with dlopen (for example the base commit's library and the
 * candidate) and feeds both the same recorded command streams. After every command it compares, between the two
 * engines: the return code, the nrError text, the complete nrSave snapshot bytes and, unless --frames 0, the
 * rendered cells. Only the public C ABI is used, so the two libraries may come from different commits.
 *
 * Usage: transaction-differential <reference.dylib> <candidate.dylib> [--frames N] [--quiet] stream.jsonl...
 *   --frames N     render and compare the frame after every Nth command (default 1: every command; 0: never)
 *   --snapshots N  compare nrSave bytes after every Nth command (default 1; 0: never). nrSave of the 30.5 MB State
 *                  costs about 20 ms, so a full run is parallelised by stream shard (native/tests/run_transaction_differential.py).
 *
 * Stream lines: {"entry":"name"} opens a fresh pair of contexts (seed 2030); {"frame":label} compares the snapshot and
 * a fresh frame at that point whatever the cadence options; every other line is one command, sent
 * verbatim. A command that returns 1 (time budget exhausted) is sent again, at most 64 times, on both engines alike.
 * Storage requests ("Prompt storage required", "Modal storage required", "Viewport render memory required") are
 * granted and the command retried, as the language bindings do.
 *
 * Exit status: 0 when no divergence was found, 1 when any was, 2 on a usage or setup error. */
#include <dlfcn.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct NrContext NrContext;
typedef struct { uint32_t glyph, foreground, background, id; } Cell;
typedef struct {
    void *handle;
    uint32_t (*contextSize)(void);
    int (*init)(void *, uint32_t, uint32_t);
    int (*command)(NrContext *, const char *, uint32_t);
    const char *(*error)(const NrContext *);
    uint32_t (*snapshotSizeFor)(const NrContext *);
    int (*save)(const NrContext *, void *, uint32_t);
    uint32_t (*render)(NrContext *);
    const Cell *(*cells)(const NrContext *);
    uint64_t (*promptMemorySize)(const NrContext *);
    int (*setPromptMemory)(NrContext *, void *, uint64_t);
    uint64_t (*modalMemorySize)(const NrContext *);
    int (*setModalMemory)(NrContext *, void *, uint64_t);
    uint64_t (*renderMemorySize)(const NrContext *);
    int (*setRenderMemory)(NrContext *, void *, uint64_t);
} Library;
typedef struct { Library *lib; NrContext *c; void *blocks[64]; int blockCount; unsigned char *snapshot; uint32_t snapshotCap; } Engine;

static void *symbol(void *handle, const char *path, const char *name) {
    void *p = dlsym(handle, name);
    if (!p) { fprintf(stderr, "%s: missing symbol %s\n", path, name); exit(2); }
    return p;
}
static void openLibrary(Library *l, const char *path) {
    /* RTLD_LOCAL keeps each image's symbols private; each library binds its own internal calls. */
    l->handle = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!l->handle) { fprintf(stderr, "dlopen %s: %s\n", path, dlerror()); exit(2); }
#define BIND(field, name) *(void **)&l->field = symbol(l->handle, path, name)
    BIND(contextSize, "nrContextSize"); BIND(init, "nrInit"); BIND(command, "nrCommand"); BIND(error, "nrError");
    BIND(snapshotSizeFor, "nrSnapshotSizeFor"); BIND(save, "nrSave"); BIND(render, "nrRender"); BIND(cells, "nrCells");
    BIND(promptMemorySize, "nrPromptMemorySize"); BIND(setPromptMemory, "nrSetPromptMemory");
    BIND(modalMemorySize, "nrModalMemorySize"); BIND(setModalMemory, "nrSetModalMemory");
    BIND(renderMemorySize, "nrRenderMemorySize"); BIND(setRenderMemory, "nrSetRenderMemory");
#undef BIND
}
static void release(Engine *e) { for (int i = 0; i < e->blockCount; i++) free(e->blocks[i]); e->blockCount = 0; }
static void *keep(Engine *e, uint64_t bytes) {
    if (e->blockCount >= 64) { fprintf(stderr, "too many storage grants\n"); exit(2); }
    void *p = calloc(1, (size_t)bytes + 16); if (!p) { fprintf(stderr, "out of memory\n"); exit(2); }
    e->blocks[e->blockCount++] = p; return (void *)(((uintptr_t)p + 7u) & ~(uintptr_t)7u);
}
static void openEngine(Engine *e) {
    release(e);
    if (!e->c) { e->c = malloc(e->lib->contextSize()); if (!e->c) { fprintf(stderr, "out of memory\n"); exit(2); } }
    if (e->lib->init(e->c, e->lib->contextSize(), 2030) != 0) { fprintf(stderr, "nrInit failed\n"); exit(2); }
}
static int send(Engine *e, const char *text, size_t n) {
    int code = 1;
    for (int again = 0; again < 64 && code == 1; again++) {
        code = e->lib->command(e->c, text, (uint32_t)n);
        for (int guard = 0; code < 0 && guard < 16; guard++) {
            const char *m = e->lib->error(e->c); uint64_t need;
            if (!strcmp(m, "Prompt storage required")) { need = e->lib->promptMemorySize(e->c); if (e->lib->setPromptMemory(e->c, keep(e, need), need)) break; }
            else if (!strcmp(m, "Modal storage required")) { need = e->lib->modalMemorySize(e->c); if (e->lib->setModalMemory(e->c, keep(e, need), need)) break; }
            else if (!strcmp(m, "Viewport render memory required")) { need = e->lib->renderMemorySize(e->c); if (e->lib->setRenderMemory(e->c, keep(e, need), need)) break; }
            else break;
            code = e->lib->command(e->c, text, (uint32_t)n);
        }
    }
    return code;
}
static uint32_t snapshot(Engine *e) {
    uint32_t n = e->lib->snapshotSizeFor(e->c);
    if (n > e->snapshotCap) { free(e->snapshot); e->snapshot = malloc(n); e->snapshotCap = n; if (!e->snapshot) { fprintf(stderr, "out of memory\n"); exit(2); } }
    /* nrSave returns 0 on success, not a length: the snapshot is the n bytes nrSnapshotSizeFor named. */
    if (e->lib->save(e->c, e->snapshot, n) != 0) { fprintf(stderr, "nrSave failed\n"); exit(2); }
    return n;
}
static int frame(Engine *e, const Cell **cells) {
    uint32_t n = e->lib->render(e->c);
    if (!n) {
        uint64_t need = e->lib->renderMemorySize(e->c);
        if (need && !e->lib->setRenderMemory(e->c, keep(e, need), need)) n = e->lib->render(e->c);
    }
    *cells = n ? e->lib->cells(e->c) : 0;
    return (int)n;
}

static unsigned long commands, divergences, rejected, frames, snapshots, entries, checkpoints;
static int quiet;
static char entry[160];
static void report(const char *what, const char *text, size_t n, const char *detail) {
    divergences++;
    if (divergences <= 40) fprintf(stderr, "DIVERGENCE [%s] %s after %.*s\n  %s\n", entry, what, (int)(n > 300 ? 300 : n), text, detail);
}
static void compare(Engine *a, Engine *b, const char *text, size_t n, int renderNow, int snapshotNow) {
    int ra = send(a, text, n), rb = send(b, text, n);
    commands++;
    if (ra < 0) rejected++;
    char detail[900];
    if (ra != rb || strcmp(a->lib->error(a->c), b->lib->error(b->c))) {
        snprintf(detail, sizeof(detail), "reference %d \"%s\", candidate %d \"%s\"", ra, a->lib->error(a->c), rb, b->lib->error(b->c));
        report("result", text, n, detail); return;
    }
    uint32_t sa = snapshotNow ? snapshot(a) : 0, sb = snapshotNow ? snapshot(b) : 0;
    if (snapshotNow) snapshots++;
    if (sa != sb || memcmp(a->snapshot, b->snapshot, sa)) {
        uint32_t i = 0; while (i < sa && i < sb && a->snapshot[i] == b->snapshot[i]) i++;
        snprintf(detail, sizeof(detail), "snapshot differs: sizes %u and %u, first difference at byte %u", sa, sb, i);
        report("snapshot", text, n, detail); return;
    }
    if (renderNow) {
        const Cell *ca, *cb; int na = frame(a, &ca), nb = frame(b, &cb);
        frames++;
        if (na != nb || (na && memcmp(ca, cb, (size_t)na * sizeof(Cell)))) {
            int i = 0; while (i < na && i < nb && !memcmp(&ca[i], &cb[i], sizeof(Cell))) i++;
            snprintf(detail, sizeof(detail), "frame differs: %d and %d cells, first difference at cell %d", na, nb, i);
            report("frame", text, n, detail);
        }
    }
}

/* A {"frame":label} line: compare the snapshot and a freshly rendered frame now, whatever the cadence options say. */
static void checkpoint(Engine *a, Engine *b, const char *line) {
    char detail[300];
    uint32_t sa = snapshot(a), sb = snapshot(b); snapshots++;
    if (sa != sb || memcmp(a->snapshot, b->snapshot, sa)) {
        uint32_t i = 0; while (i < sa && i < sb && a->snapshot[i] == b->snapshot[i]) i++;
        snprintf(detail, sizeof(detail), "snapshot differs at checkpoint, first difference at byte %u", i);
        report("checkpoint snapshot", line, strlen(line), detail); return;
    }
    const Cell *ca, *cb; int na = frame(a, &ca), nb = frame(b, &cb); frames++; checkpoints++;
    if (na != nb || (na && memcmp(ca, cb, (size_t)na * sizeof(Cell)))) {
        snprintf(detail, sizeof(detail), "frame differs at checkpoint: %d and %d cells", na, nb);
        report("checkpoint frame", line, strlen(line), detail);
    }
}
int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: %s reference.dylib candidate.dylib [--frames N] [--quiet] stream.jsonl...\n", argv[0]); return 2; }
    static Library la, lb; openLibrary(&la, argv[1]); openLibrary(&lb, argv[2]);
    if (la.handle == lb.handle) { fprintf(stderr, "both paths name the same loaded image; copy one library to another path\n"); return 2; }
    Engine a = {.lib = &la}, b = {.lib = &lb};
    long every = 1, snapEvery = 1; int opened = 0;
    size_t cap = 1 << 20; char *line = malloc(cap);
    for (int arg = 3; arg < argc; arg++) {
        if (!strcmp(argv[arg], "--frames") && arg + 1 < argc) { every = strtol(argv[++arg], 0, 10); continue; }
        if (!strcmp(argv[arg], "--snapshots") && arg + 1 < argc) { snapEvery = strtol(argv[++arg], 0, 10); continue; }
        if (!strcmp(argv[arg], "--quiet")) { quiet = 1; continue; }
        FILE *f = fopen(argv[arg], "rb"); if (!f) { fprintf(stderr, "cannot open %s\n", argv[arg]); return 2; }
        unsigned long since = 0;
        for (;;) {
            size_t used = 0; int ch;
            while ((ch = fgetc(f)) != EOF && ch != '\n') { if (used + 1 >= cap) { cap *= 2; line = realloc(line, cap); } line[used++] = (char)ch; }
            if (ch == EOF && !used) break;
            line[used] = 0; if (!used) continue;
            if (!strncmp(line, "{\"entry\":\"", 10)) {
                if (opened && !quiet) printf("  %-60s %6lu commands\n", entry, commands - since);
                snprintf(entry, sizeof(entry), "%.*s", (int)(strcspn(line + 10, "\"")), line + 10);
                openEngine(&a); openEngine(&b); opened = 1; entries++; since = commands; continue;
            }
            if (!opened) { snprintf(entry, sizeof(entry), "%s", argv[arg]); openEngine(&a); openEngine(&b); opened = 1; entries++; }
            if (!strncmp(line, "{\"frame\":", 9)) { checkpoint(&a, &b, line); continue; }
            compare(&a, &b, line, used, every > 0 && (commands + 1) % (unsigned long)every == 0, snapEvery > 0 && (commands + 1) % (unsigned long)snapEvery == 0);
        }
        if (opened && !quiet) printf("  %-60s %6lu commands\n", entry, commands - since);
        fclose(f);
    }
    printf("transaction-differential: %lu entries, %lu commands (%lu rejected), %lu snapshots and %lu frames compared (%lu checkpoints), %lu divergences\n", entries, commands, rejected, snapshots, frames, checkpoints, divergences);
    return divergences ? 1 : 0;
}
