/* RC4-028 acceptance: hostile restored selector registries, appearance maps and
 * guard trees. Companion to tests/test_language_contracts_acceptance.py.
 *
 * Contract sentences enforced here:
 *  SELECTORS.md  "Sanitizers test hostile restored registries, property maps and
 *                 condition indices."
 *  CONDITIONS.md "The native sanitizer program also rejects hostile tree indices
 *                 and counts despite an attacker recomputing the snapshot checksum."
 *  DATA-EXPRESSIONS.md "it cannot directly reference an event because appearance
 *                 has no event subscription."  CONDITIONS.md "A selector without an
 *                 event gate is ambiguous and rejects."
 *  API.md        "Rejection leaves scene state byte-identical."
 * Every hostile case recomputes the CRC, so only semantic validation can refuse it.
 * Positive controls prove the harness accepts valid in-range edits. Standalone:
 * no allocation in the core, no libm, no mocks. */
#include "internal.h"
#include <stdio.h>
#include <stdlib.h>

static unsigned char *base, *work, *after;
static uint32_t size;
static int failures, cases;

static void run(NrContext *c, const char *text) {
    if (nrCommand(c, text, (uint32_t)strlen(text)) < 0) {
        printf("SETUP REJECTED: %s -> %s\n", text, nrError(c));
        exit(2);
    }
}
static State *mutable(NrContext *c) {
    size = nrSnapshotSizeFor(c);
    base = realloc(base, size); work = realloc(work, size); after = realloc(after, size);
    if (!base || !work || !after || nrSave(c, base, size)) { puts("SNAPSHOT FAILED"); exit(3); }
    memcpy(work, base, size);
    return (State *)(void *)(work + 24);
}
static int restore(NrContext *c) {
    uint32_t crc = nrCrc(work + 24, size - 24);
    for (int i = 0; i < 4; i++) work[20 + i] = (unsigned char)(crc >> (8 * i));
    int result = nrLoad(c, work, size);
    if (nrSave(c, after, size)) { puts("SAVE AFTER LOAD FAILED"); exit(4); }
    return result;
}
static void reject(NrContext *c, const char *name) {
    int result = restore(c), same = !memcmp(after, base, size);
    cases++;
    if (result < 0 && same) { printf("PASS reject  %s\n", name); return; }
    failures++;
    printf("FAIL reject  %s (%s)\n", name, result < 0 ? "state changed" : "accepted");
    if (result >= 0 && nrLoad(c, base, size)) { puts("BASE RESTORE FAILED"); exit(5); }
}
static void accept(NrContext *c, const char *name) {
    int result = restore(c);
    cases++;
    if (result == 0 && nrRender(c) > 0) printf("PASS accept  %s\n", name);
    else { failures++; printf("FAIL accept  %s\n", name); }
    if (nrLoad(c, base, size)) { puts("BASE RESTORE FAILED"); exit(5); }
}
static int valueSlot(const NrContext *c, const char *path) {
    for (int i = 0; i < NR_VALUES; i++)
        if (c->state.values[i].used && !strcmp(c->state.values[i].path, path)) return i;
    printf("MISSING VALUE %s\n", path); exit(6);
}
static int ruleSlot(const NrContext *c, int id) {
    for (int i = 0; i < NR_STYLE_RULES; i++)
        if (c->state.styleRules[i].used && c->state.styleRules[i].id == id) return i;
    printf("MISSING RULE %d\n", id); exit(7);
}
static int registrySlot(const NrContext *c, int id) {
    for (int i = 0; i < NR_REGISTERED_STATES; i++)
        if (c->state.registeredStates[i].used && c->state.registeredStates[i].id == id) return i;
    printf("MISSING REGISTRATION %d\n", id); exit(8);
}

int main(void) {
    NrContext *c = malloc(nrContextSize());
    if (!c || nrInit(c, nrContextSize(), 2030)) return 1;
    run(c, "{\"op\":\"widget\",\"id\":1,\"kind\":\"button\",\"x\":4,\"y\":4,\"width\":20,\"height\":3,\"text\":\"x\",\"material\":1}");
    run(c, "{\"op\":\"emitter\",\"id\":2,\"effect\":\"weather/silver-squall\",\"count\":1}");
    run(c, "{\"op\":\"define\",\"path\":\"/heat\",\"value\":60}");
    run(c, "{\"op\":\"define\",\"path\":\"/flag\",\"value\":true}");
    run(c, "{\"op\":\"state-register\",\"id\":7,\"path\":\"/app/one\",\"role\":\"control\",\"target\":{\"family\":\"widget\",\"id\":1}}");
    run(c, "{\"op\":\"state-register\",\"id\":8,\"path\":\"/weather/rain\",\"role\":\"rain\",\"target\":{\"family\":\"emitter\",\"id\":2}}");
    /* Guard nodes: [0] all, [1] heat above 50 h5, [2] not, [3] heat below 0. */
    run(c, "{\"op\":\"style-rule\",\"id\":3,\"selector\":{\"family\":\"widget\",\"pathPrefix\":\"/app\"},\"style\":{\"material\":2,"
           "\"alpha\":{\"path\":\"/heat\",\"inputMin\":0,\"inputMax\":100,\"outputMin\":0,\"outputMax\":1}},"
           "\"when\":{\"all\":[{\"path\":\"/heat\",\"comparison\":\"above\",\"value\":50,\"hysteresis\":5},"
           "{\"not\":{\"path\":\"/heat\",\"comparison\":\"below\",\"value\":0}}]}}");
    run(c, "{\"op\":\"style-rule\",\"id\":4,\"selector\":{\"family\":\"widget\"},\"style\":{\"alpha\":0.5},\"when\":"
           "{\"not\":{\"not\":{\"not\":{\"not\":{\"not\":{\"not\":{\"not\":{\"path\":\"/heat\",\"comparison\":\"above\",\"value\":1}}}}}}}}}");
    run(c, "{\"op\":\"style-rule\",\"id\":5,\"selector\":{\"family\":\"emitter\",\"role\":\"leaf\"},\"style\":{\"veinContrast\":1}}");
    const int heat = valueSlot(c, "/heat"), typed = valueSlot(c, "/flag");
    int unused = -1;
    for (int i = 0; i < NR_VALUES && unused < 0; i++) if (!c->state.values[i].used) unused = i;
    const int r = ruleSlot(c, 3), deep = ruleSlot(c, 4), leafOnly = ruleSlot(c, 5);
    const int g = registrySlot(c, 7), rain = registrySlot(c, 8);
    if (c->state.styleRules[r].guard.conditionCount != 4 || c->state.styleRules[deep].guard.conditionCount != 8) {
        puts("UNEXPECTED GUARD LAYOUT"); return 9;
    }
    State *s;
    /* Positive controls. */
    s = mutable(c); accept(c, "unmodified snapshot");
    s = mutable(c); s->styleRules[r].guard.conditions[1].low = s->styleRules[r].guard.conditions[1].high = 40; accept(c, "in-range guard constant");
    s = mutable(c); s->styleRules[r].properties[2].outputMax = .5; accept(c, "in-range map output");
    s = mutable(c); s->styleRules[r].priority = -32768; accept(c, "minimum priority");

    /* Registries. */
    s = mutable(c); s->registeredStates[g].targetId = 0; reject(c, "registry widget target zero");
    s = mutable(c); s->registeredStates[g].targetId = 70000; reject(c, "registry target above 65535");
    s = mutable(c); s->registeredStates[g].active = 2; reject(c, "registry active 2");
    s = mutable(c); s->registeredStates[g].used = 2; reject(c, "registry used 2");
    s = mutable(c); s->registeredStates[g].id = 0; reject(c, "registry id 0");
    s = mutable(c); s->registeredStates[g].role[0] = '!'; reject(c, "registry role invalid byte");
    s = mutable(c); s->registeredStates[g].role[0] = 0; reject(c, "registry role empty");
    s = mutable(c); memset(s->registeredStates[g].role, 'a', sizeof(s->registeredStates[g].role)); reject(c, "registry role unterminated");
    s = mutable(c); strcpy(s->registeredStates[g].path, "/app//one"); reject(c, "registry path empty segment");
    s = mutable(c); strcpy(s->registeredStates[g].path, "/app/.."); reject(c, "registry path dot-dot segment");
    s = mutable(c); memset(s->registeredStates[g].path, 'x', sizeof(s->registeredStates[g].path)); reject(c, "registry path unterminated");
    s = mutable(c); s->registeredStates[rain].family = 1; s->registeredStates[rain].targetId = 1; reject(c, "registry duplicate target");
    s = mutable(c); strcpy(s->registeredStates[rain].path, "/app/one"); reject(c, "registry duplicate path");
    s = mutable(c); s->registeredStates[rain].id = 7; reject(c, "registry duplicate id");
    s = mutable(c); s->registeredStates[g].family = 0; reject(c, "registry family 0");
    s = mutable(c); s->registeredStates[g].family = NR_STYLE_FAMILIES + 1; reject(c, "registry family beyond table");
    s = mutable(c); s->registeredStates[g].family = 8; s->registeredStates[g].targetId = 1; reject(c, "registry singleton target nonzero");

    /* Rules and selectors. */
    s = mutable(c); s->styleRules[r].used = 2; reject(c, "rule used 2");
    s = mutable(c); s->styleRules[r].id = 0; reject(c, "rule id 0");
    s = mutable(c); s->styleRules[r].id = 4; reject(c, "rule duplicate id");
    s = mutable(c); s->styleRules[r].enabled = 2; reject(c, "rule enabled 2");
    s = mutable(c); s->styleRules[r].priority = 40000; reject(c, "rule priority above 32767");
    s = mutable(c); s->styleRules[r].selector.family = 0; reject(c, "selector family 0");
    s = mutable(c); s->styleRules[r].selector.family = NR_STYLE_FAMILIES + 1; reject(c, "selector family beyond table");
    s = mutable(c); s->styleRules[r].selector.targetId = -2; reject(c, "selector target -2");
    s = mutable(c); s->styleRules[r].selector.targetId = 0; reject(c, "selector widget target zero");
    s = mutable(c); s->styleRules[r].selector.prefix = 2; reject(c, "selector prefix flag 2");
    s = mutable(c); strcpy(s->styleRules[r].selector.path, "/app/"); reject(c, "selector path trailing slash");
    s = mutable(c); memset(s->styleRules[r].selector.path, 'a', sizeof(s->styleRules[r].selector.path)); reject(c, "selector path unterminated");
    s = mutable(c); s->styleRules[r].selector.stateMask = 32; reject(c, "selector state mask beyond five flags");
    s = mutable(c); s->styleRules[r].selector.stateValue = 1; reject(c, "selector state value outside mask");
    s = mutable(c); strcpy(s->styleRules[r].selector.role, "bad role"); reject(c, "selector role invalid");
    s = mutable(c); strcpy(s->styleRules[leafOnly].selector.role, "rain"); reject(c, "leaf-only property on matching non-leaf emitter");

    /* Property maps and discrete constants. */
    s = mutable(c); s->styleRules[r].propertyMask = 0; reject(c, "property mask empty");
    s = mutable(c); s->styleRules[r].propertyMask |= 64u; reject(c, "property mask color on widget");
    s = mutable(c); s->styleRules[r].properties[2].source = -1; reject(c, "map source -1");
    s = mutable(c); s->styleRules[r].properties[2].source = NR_VALUES; reject(c, "map source beyond value table");
    s = mutable(c); s->styleRules[r].properties[2].source = unused; reject(c, "map source unused slot");
    s = mutable(c); s->styleRules[r].properties[2].source = typed; reject(c, "map source typed value");
    s = mutable(c); s->styleRules[r].properties[2].outputMax = 2; reject(c, "map output above one");
    s = mutable(c); s->styleRules[r].properties[2].outputMin = -.1; reject(c, "map output below zero");
    s = mutable(c); s->styleRules[r].properties[2].inputMin = __builtin_nan(""); reject(c, "map input NaN");
    s = mutable(c); s->styleRules[r].properties[2].inputMin = -2000000; reject(c, "map input below -1e6");
    s = mutable(c); s->styleRules[r].properties[2].inputMin = 100; reject(c, "map input interval empty");
    s = mutable(c); s->styleRules[r].properties[2].mapped = 2; reject(c, "map flag 2");
    s = mutable(c); s->styleRules[r].properties[0].outputMin = s->styleRules[r].properties[0].outputMax = 1.5; reject(c, "material constant 1.5");
    s = mutable(c); s->styleRules[r].properties[0].outputMin = s->styleRules[r].properties[0].outputMax = 9; reject(c, "material constant missing material");
    s = mutable(c); {StyleValue *v = &s->styleRules[r].properties[0]; v->mapped = 1; v->source = heat; v->inputMin = 0; v->inputMax = 1; v->outputMin = 0; v->outputMax = 3;}
    reject(c, "material as rounded value map");
    s = mutable(c); s->styleRules[r].properties[0].outputMax = 3; reject(c, "constant with distinct endpoints");
    s = mutable(c); s->styleRules[r].properties[0].source = heat; reject(c, "constant with a value source");

    /* Guard trees: bounded, prefix ordered, nonrecursive. */
    Trigger *t;
    s = mutable(c); s->styleRules[r].guard.lastTruth = 2; reject(c, "guard truth 2");
    s = mutable(c); s->styleRules[r].guard.conditionCount = NR_CONDITIONS + 1; reject(c, "guard node count 32");
    s = mutable(c); s->styleRules[r].guard.conditionCount = -1; reject(c, "guard node count -1");
    s = mutable(c); s->styleRules[r].guard.conditions[0].end = 1; reject(c, "guard root end truncated");
    s = mutable(c); s->styleRules[r].guard.conditions[0].end = 9; reject(c, "guard root end beyond count");
    s = mutable(c); s->styleRules[r].guard.conditions[0].children = 3; reject(c, "guard all child count too large");
    s = mutable(c); s->styleRules[r].guard.conditions[0].children = 0; reject(c, "guard all without children");
    s = mutable(c); s->styleRules[r].guard.conditions[2].children = 2; reject(c, "guard not with two children");
    s = mutable(c); s->styleRules[r].guard.conditions[2].end = 2; reject(c, "guard node ending at itself");
    s = mutable(c); s->styleRules[r].guard.conditions[1].source = NR_VALUES; reject(c, "guard leaf source beyond value table");
    s = mutable(c); s->styleRules[r].guard.conditions[1].source = typed; reject(c, "guard leaf source typed value");
    s = mutable(c); s->styleRules[r].guard.conditions[1].source = unused; reject(c, "guard leaf source unused slot");
    s = mutable(c); s->styleRules[r].guard.conditions[1].kind = 7; reject(c, "guard node kind 7");
    s = mutable(c); s->styleRules[r].guard.conditions[0].kind = 5; reject(c, "guard typed node without compiled formula");
    s = mutable(c); s->styleRules[r].guard.conditions[1].lastTruth = 2; reject(c, "guard leaf truth 2");
    s = mutable(c); s->styleRules[r].guard.conditions[1].hysteresis = __builtin_nan(""); reject(c, "guard hysteresis NaN");
    s = mutable(c); s->styleRules[r].guard.conditions[1].hysteresis = -1; reject(c, "guard hysteresis negative");
    s = mutable(c); s->styleRules[r].guard.conditions[1].comparison = 7; reject(c, "guard comparison 7");
    s = mutable(c); s->styleRules[r].guard.conditions[1].low = s->styleRules[r].guard.conditions[1].high = 2e6; reject(c, "guard constant above 1e6");
    s = mutable(c); s->styleRules[r].guard.conditions[1].low = 60; s->styleRules[r].guard.conditions[1].high = 50; reject(c, "guard reversed range");
    s = mutable(c); s->styleRules[r].guard.conditions[3].comparison = 2; s->styleRules[r].guard.conditions[3].hysteresis = 1; reject(c, "guard equal with hysteresis");
    s = mutable(c); t = &s->styleRules[deep].guard; t->conditions[8] = t->conditions[7]; t->conditions[8].end = 9;
    for (int k = 0; k < 8; k++) { t->conditions[k] = (Condition){.kind = 3, .source = -1, .children = 1, .end = 9}; }
    t->conditionCount = 9; reject(c, "guard depth 9");

    /* Appearance has no event subscription, so no restored guard may read one. */
    s = mutable(c); t = &s->styleRules[r].guard; t->conditions[3].kind = 4; t->conditions[3].source = -1;
    reject(c, "guard event-payload leaf without event gate");
    s = mutable(c); t = &s->styleRules[r].guard; t->conditions[3].kind = 4; t->conditions[3].source = -1; strcpy(t->eventPath, "/review/inspect");
    reject(c, "guard event-payload leaf with smuggled event gate");
    s = mutable(c); strcpy(s->styleRules[r].guard.eventPath, "/review/inspect"); reject(c, "guard smuggled event gate");

    printf("%s: %d of %d hostile/positive restore cases\n", failures ? "FAIL" : "PASS", cases - failures, cases);
    free(base); free(work); free(after); free(c);
    return failures ? 1 : 0;
}
