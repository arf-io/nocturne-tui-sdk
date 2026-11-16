#!/usr/bin/env python3
"""Assemble the cross-version artwork inventory from the extract, verify and
reconcile layers into INVENTORY.json and INVENTORY.md.

Deterministic: no network, no LLM, no rendering. Entities come only from the
per-group extract files (each carries an exact quote from a named file);
verification results and catalogue mappings are joined by (file, identifier,
name). Byte-identical definitions across editions are collapsed into one
definition record that lists every edition, so provenance is kept while the
count is not inflated.
"""
import glob, hashlib, json, os, re, subprocess, sys
from collections import Counter, defaultdict

ROOT = sys.argv[1]
OUT = os.path.join(ROOT, 'native/evidence/artwork-inventory-20261031')
os.chdir(ROOT)


EDITION_RULES = [
    (r'^0\.1\b', '0.1'), (r'^0\.2\b', '0.2'), (r'^0\.3\b', '0.3'), (r'^0\.4\b', '0.4'),
    (r'0\.5-atelier|atelier-v0\.5|Spatial Atelier', '0.5-atelier'), (r'0\.5-kinetic|0\.5\.0-kinetic', '0.5-kinetic'),
    (r'^0\.7\b', '0.7'), (r'0\.8', '0.8'), (r'Continuity-v0\.9-preview', '0.9-rc.1-preview'),
    (r'Nocturne-Continuity|0\.9\.0-rc\.1', '0.9-rc.1'), (r'rc\.2|workbench|field-guide', '0.9-rc.2'),
    (r'RC3|rc\.3', '0.9-rc.3'), (r'current-root|^root|gallery-root|studio-root', 'current-root'),
    (r'template', 'web-template'), (r'schema', 'schema'), (r'catalogue-json', 'root-catalogue-json'),
    (r'source|src/', 'c-source'),
]


def normalize_edition(label):
    for pat, key in EDITION_RULES:
        if re.search(pat, label or '', re.I):
            return key
    return 'unclassified:' + str(label)


def load(p):
    with open(p) as f:
        return json.load(f)


modules = load(os.path.join(OUT, 'modules.json'))
extracts = [load(p) for p in sorted(glob.glob(os.path.join(OUT, 'extract', '*.json')))]
verifies = {}
for p in sorted(glob.glob(os.path.join(OUT, 'verify', '*.json'))):
    v = load(p); verifies[v.get('group')] = v
reconciles = [load(p) for p in sorted(glob.glob(os.path.join(OUT, 'reconcile', '*.json')))]

# ---- entities -------------------------------------------------------------
entities = []
quote_checked = Counter()
for ex in extracts:
    for e in ex.get('entities', []):
        e = dict(e)
        e['group'] = ex.get('group')
        e['editionKey'] = normalize_edition(e.get('edition'))
        f = e.get('file') or ''
        q = e.get('quote') or ''
        # recheck every quote against the file bytes: the single most important guard
        ok = False
        path = os.path.join(ROOT, f)
        if q and os.path.isfile(path):
            with open(path, 'rb') as fh:
                ok = q.encode('utf-8', 'surrogatepass') in fh.read()
        e['quoteVerified'] = bool(ok)
        quote_checked['verified' if ok else 'unverified'] += 1
        entities.append(e)

# join reconcile mappings
mapping = {}
for r in reconciles:
    for m in r.get('mappings', []):
        key = (m.get('entityFile') or '', m.get('identifier') or '', m.get('name') or '')
        mapping[key] = m
for e in entities:
    m = mapping.get((e.get('file') or '', e.get('identifier') or '', e.get('name') or ''))
    if m is None:
        # fall back on identifier+name only
        for k, v in mapping.items():
            if k[1] == (e.get('identifier') or '') and k[2] == (e.get('name') or '') and k[1]:
                m = v; break
    e['mapping'] = {k: m.get(k) for k in ('status', 'currentId', 'evidence', 'difference')} if m else {'status': 'not-reconciled'}

# collapse byte-identical definitions across editions
defs = defaultdict(list)
for e in entities:
    h = hashlib.sha256(((e.get('kind') or '') + '\0' + (e.get('name') or '') + '\0' + (e.get('quote') or '')).encode('utf-8', 'surrogatepass')).hexdigest()
    defs[h].append(e)
definitions = []
for h, es in defs.items():
    first = es[0]
    definitions.append({
        'definitionId': h[:16], 'kind': first.get('kind'), 'name': first.get('name'), 'identifier': first.get('identifier'),
        'editions': sorted({e.get('editionKey') for e in es}), 'editionLabels': sorted({e.get('edition') or '?' for e in es}), 'files': sorted({e.get('file') for e in es}),
        'implementation': first.get('implementation'), 'variants': first.get('variants'), 'parameters': first.get('parameters'),
        'quoteVerified': all(e['quoteVerified'] for e in es), 'mapping': first.get('mapping'), 'instances': len(es),
    })
definitions.sort(key=lambda d: (d['kind'] or '', d['name'] or ''))

# ---- totals ---------------------------------------------------------------
by_kind = Counter(e.get('kind') for e in entities)
by_edition = Counter(e.get('editionKey') for e in entities)
by_edition_label = Counter(e.get('edition') for e in entities)
by_impl = Counter(e.get('implementation') for e in entities)
def_by_kind = Counter(d['kind'] for d in definitions)
map_status = Counter(e['mapping'].get('status') for e in entities)
variant_sum = 0
for d in definitions:
    v = d.get('variants') or {}
    try:
        variant_sum += int(v.get('count') or 0)
    except Exception:
        pass

# ---- per-release presence table ------------------------------------------
tags = subprocess.run(['git', 'tag', '--list'], capture_output=True, text=True).stdout.split()
remote = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True).stdout.split()
def present(*paths):
    return all(os.path.exists(os.path.join(ROOT, p)) for p in paths)
releases = [
    ('0.1', 'present', 'legacy/editions/0.1-Nocturne-Gallery.html (= legacy/Nocturne-Gallery-v0.1.html)') if present('legacy/editions/0.1-Nocturne-Gallery.html') else ('0.1', 'absent', ''),
    ('0.1.9', 'absent', 'no archive or ref on host; recorded unresolved in native/evidence/historical-runtime-recovery-20261013/RUN-03-RECEIPT.json'),
    ('0.2', 'present', 'legacy/editions/0.2-Nocturne-{Gallery,Studio}.html'),
    ('0.3', 'present', 'legacy/editions/0.3-Nocturne-{Gallery,Pearl-Fleet,Studio}.html'),
    ('0.4', 'present', 'legacy/editions/0.4-Nocturne-{Gallery,Observatory,Pearl-Fleet,Studio}.html'),
    ('0.5 (Spatial Atelier)', 'present', 'legacy/editions/0.5-atelier-*.html and legacy/atelier-v0.5 SDK snapshot'),
    ('0.5 (Kinetic)', 'present', 'legacy/editions/0.5-kinetic-*.html'),
    ('0.6', 'absent', 'no file, archive or ref carries a 0.6 label; CHANGELOG states v0.7 was rebuilt from recovered Kinetic v0.5, not from missing v0.6 files'),
    ('0.7 (Black Hole)', 'present', 'legacy/editions/0.7-Nocturne-*.html'),
    ('0.8 (Restoration)', 'present', 'legacy/editions/0.8-Nocturne-Restoration.html, Nocturne-Restoration.html'),
    ('0.9.0-rc.1 (Continuity)', 'present', 'legacy/editions/Continuity-v0.9-preview.html, Nocturne-Continuity.html'),
    ('0.9.0-rc.2 (Workbench, +input.1)', 'present, archive off-host', 'Nocturne-Workbench.html, Nocturne-Workbench-Docs.html; the exact rc.2 Gallery archive (SHA256 375c4468...) is off-host and its tracked copy differs in bytes'),
    ('0.9.0-rc.3 (Unified RC3)', 'present', 'Nocturne-RC3.html'),
    ('0.9.0-rc.4 (RC4 SDK, Contracts 1-7)', 'present as source', 'native/ tree, native/SOURCE-PROVENANCE.json, docs/rc4-contracts*/'),
    ('1.0.0 tag (2026-10-16)', 'present as git tag' if '1.0.0' in tags else 'absent', 'git tag 1.0.0 -> 1eb6f94; release packages off-host'),
    ('1.0.0-rc.2', 'present as git tag' if '1.0.0-rc.2' in tags else 'absent', 'git tag 1.0.0-rc.2 -> 9760404; compact SDK zip and Gallery off-host'),
]

inventory = {
    'schema': 'nocturne.artwork-inventory.v1',
    'generatedFrom': {'extractGroups': [ex.get('group') for ex in extracts], 'verifyGroups': sorted(verifies), 'reconcileClusters': [r.get('cluster') for r in reconciles], 'modules': 'modules.json'},
    'totals': {
        'entityInstances': len(entities), 'distinctDefinitions': len(definitions), 'enumeratedVariantsSum': variant_sum,
        'quoteVerifiedInstances': quote_checked['verified'], 'quoteUnverifiedInstances': quote_checked['unverified'],
        'byKind': dict(by_kind), 'definitionsByKind': dict(def_by_kind), 'byEdition': dict(by_edition), 'byEditionLabel': dict(by_edition_label), 'byImplementation': dict(by_impl),
        'mappingStatus': dict(map_status),
        'distinctFiles': modules.get('distinctFileCount'), 'distinctWasmModules': modules.get('distinctModuleCount'),
    },
    'countReconciliation': {
        'operatorCitedApproximate': 4000,
        'currentCatalogueIdentities': 111, 'historicalLedgerIdentities': 109, 'currentApiStudiesCited': 5728,
        'statement': 'Instances, distinct definitions and enumerated variants above are what the host-resident files define. No figure here is inflated toward the cited approximation; archives that are off-host are not counted.',
    },
    'releases': [{'release': r, 'status': s, 'evidence': e} for r, s, e in releases],
    'gitRefsOnHost': {'tags': tags, 'remoteBranches': remote},
    'catalogueIdsNeverReferenced': sorted({i for r in reconciles for i in r.get('catalogueIdsNeverReferenced', [])}),
    'verification': {g: {k: v.get(k) for k in ('checked', 'confirmed', 'failed', 'fabricationSuspected', 'notes')} for g, v in verifies.items()},
    'omissions': {ex.get('group'): ex.get('omissions') for ex in extracts},
    'definitions': definitions,
    'instances': entities,
}
with open(os.path.join(OUT, 'INVENTORY.json'), 'w') as f:
    json.dump(inventory, f, indent=1, sort_keys=False)

L = ['# Cross-version artwork inventory (host-resident editions), 2026-10-31\n',
     'Generated by `native/scripts/assemble_artwork_inventory.py` from the quoted per-group extracts, quote re-verification, and catalogue reconciliation under this directory. Every instance carries a file, locator and exact quote; `quoteVerified` is recomputed here against the file bytes. This inventory covers only files present in this checkout; off-host archives remain UNVERIFIABLE and are listed as such below.\n',
     '## Totals\n', '| Measure | Value |', '|---|---|']
t = inventory['totals']
for k in ('entityInstances', 'distinctDefinitions', 'enumeratedVariantsSum', 'quoteVerifiedInstances', 'quoteUnverifiedInstances', 'distinctFiles', 'distinctWasmModules'):
    L.append(f'| {k} | {t[k]} |')
L.append('\n### Distinct definitions by kind\n\n| Kind | Definitions | Instances |\n|---|---|---|')
for k in sorted(def_by_kind, key=lambda x: str(x)):
    L.append(f'| {k} | {def_by_kind[k]} | {by_kind.get(k, 0)} |')
L.append('\n### Instances by edition (normalized key; raw labels kept in INVENTORY.json byEditionLabel)\n\n| Edition | Instances |\n|---|---|')
for k in sorted(by_edition, key=lambda x: str(x)):
    L.append(f'| {k} | {by_edition[k]} |')
L.append('\n### Mapping to the current contract\n\n| Status | Instances |\n|---|---|')
for k, v in sorted(map_status.items(), key=lambda kv: str(kv[0])):
    L.append(f'| {k} | {v} |')
L.append(f"\nCatalogue identities never referenced by any historical entity: {len(inventory['catalogueIdsNeverReferenced'])}.")
L.append('\n## Count reconciliation\n')
L.append(f"Operator-cited approximation: about 4,000 instances/variants. Host-resident files define {t['entityInstances']} entity instances, {t['distinctDefinitions']} distinct definitions and {t['enumeratedVariantsSum']} enumerated variants. The 111 current catalogue identities, 109 historical ledger identities and 5,728 current API studies are different inventories and are not added to these figures. No number here is adjusted toward the approximation.\n")
L.append('## Per-release presence\n\n| Release | Status | Evidence |\n|---|---|---|')
for r in inventory['releases']:
    L.append(f"| {r['release']} | {r['status']} | {r['evidence']} |")
L.append('\n## Verification by group\n\n| Group | Checked | Confirmed | Failed | Fabrication suspected |\n|---|---|---|---|---|')
for g, v in sorted(inventory['verification'].items()):
    L.append(f"| {g} | {v.get('checked')} | {v.get('confirmed')} | {len(v.get('failed') or [])} | {v.get('fabricationSuspected')} |")
L.append('\n## Omissions declared by extractors\n')
for g, om in inventory['omissions'].items():
    for o in (om or []):
        L.append(f'- {g}: {o}')
L.append('\n## Known classification limits\n\nVerifiers confirmed every sampled quote but flagged two recurring weaknesses that this assembler cannot repair: (1) some `name` fields are descriptive labels written by the extractor rather than strings from the file (the identifier and quote are still exact); (2) a small number of `kind` values are implausible, mostly colour-math helpers or bare export declarations classed as palette, composite or graph. Treat `kind` and `name` as extractor judgement and `file`/`locator`/`quote` as the evidence.\n')
L.append('\n## Scope limits\n\n- Off-host: the rc.2 Gallery archive and every operator-held archive (see EDITIONS.json); the all-reference bundle with 313 named refs. Only the two tags listed in gitRefsOnHost are on this host.\n- Semantic extraction was performed by reading agents and is bounded by the quotes they recorded; `quoteUnverifiedInstances` counts entries whose quote does not occur in the named file and must be treated as unproven.\n')
with open(os.path.join(OUT, 'INVENTORY.md'), 'w') as f:
    f.write('\n'.join(L) + '\n')
print(json.dumps(inventory['totals'], indent=1))
