#!/usr/bin/env python3
"""The operator's nullification contract: validation, resolution against the repository, and its effects.

native/contract/NULLIFICATION.json (schema native/contract/NULLIFICATION.schema.json) lists decisions that
strike artwork from the final contract: a historical definition or instance of the cross-version artwork
inventory, a current catalogue identity, or a rendering output (a recipe of native/recipes.json or a
component capture of docs/current/images/CAPTURES.json). This module is the only reader of that contract.
apply_nullification.py records what every decision strikes; build_reference_docs.py and build_gallery.py
call it at their single choke points, and build_gallery_site.py takes the HTTP bundle's library from
build_gallery.py's, so a nullified identity is omitted from the generated catalogue pages, the Gallery
library and its attract rotation in both the standalone page and the bundle, and listed in the
Nullification.md ledger.

Nothing is deleted. The C implementation, tests, fixtures and evidence of a nullified identity stay, the
native core still accepts and renders it, and docs/current/components.json keeps its engine observations.
Removing it from the core is a later, separately qualified step (native/docs/NULLIFICATION.md).

Deterministic: no network, clock or rendering. Keys are exact strings and are never stripped or split: an
instance key is matched whole against every instance's file#locator#identifier, because locators and
identifiers contain '#'.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from functools import cached_property
from pathlib import Path
import hashlib
import json
import re
import sys

SCHEMA = 'nocturne.nullification.v1'
RESOLVED_SCHEMA = 'nocturne.nullified.v1'
SCOPES = ('historical-definition', 'historical-instance', 'current-identity', 'rendering-output')
HISTORICAL_SCOPES = ('historical-definition', 'historical-instance')
CONTRACT_SCOPES = ('current-identity', 'rendering-output')  # the scopes the documentation and Gallery generators apply
FIELDS = ('scope', 'key', 'name', 'reason', 'decidedBy', 'decidedAt')
KEY_PATTERNS = {
    'historical-definition': r'^[0-9a-f]{16}$',
    'historical-instance': r'^[^#]+#.+#.+$',
    'current-identity': r'^[a-z][a-z0-9-]*/[a-z0-9][a-z0-9.-]*$',
    'rendering-output': r'^(recipe:\S+|capture:[^/\s]+/[^/\s]+)$',
}
DECIDED_AT_PATTERN = r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d{1,9})?(Z|[+-]\d{2}:\d{2})$'

CONTRACT = 'native/contract/NULLIFICATION.json'
INVENTORY = 'native/evidence/artwork-inventory-20261031/INVENTORY.json'
INVENTORY_MARKDOWN = 'native/evidence/artwork-inventory-20261031/INVENTORY.md'
NULLIFIED = 'native/evidence/artwork-inventory-20261031/NULLIFIED.json'
CATALOGUE = 'native/catalogue.json'
PORT_LEDGER = 'native/port-ledger.json'
RECIPES = 'native/recipes.json'
CAPTURES = 'docs/current/images/CAPTURES.json'
COMPONENTS = 'docs/current/components.json'
DOCS = 'docs/current'
TEMPLATE = 'native/web/template.html'
STATEMENT = ('Operator decisions that strike artwork, or artwork and its rendering outputs, from the final contract. '
             'A struck catalogue identity is omitted from the generated catalogue pages and, with every recipe and study '
             'that names it, from the Gallery library and attract rotation; a struck recipe is omitted from the Gallery. '
             'Nothing is deleted: the C implementation, tests, fixtures and evidence stay, and the native core still accepts '
             'and renders a struck identity. Removing it from the core is a later, separately qualified step '
             '(native/docs/NULLIFICATION.md).')

_ID_CHARACTERS = 'A-Za-z0-9_./-'
_SURROGATE = re.compile('[\ud800-\udfff]')
_LINE_BREAKS = re.compile('[\r\n\x0b\x0c\x1c-\x1e\x85\u2028\u2029]')  # every character str.splitlines() ends a line at
_CONTROLS = re.compile('[\x00-\x08\x0e-\x1b\x1f\x7f-\x84\x86-\x9f\ufffe\uffff\ud800-\udfff]')  # other controls, and what XML 1.0 forbids


class NullificationError(ValueError):
    """Every problem found, in decision order; str() joins the messages with newlines."""

    def __init__(self, messages):
        self.messages = list(messages)
        super().__init__('\n'.join(self.messages))


def quote(text):
    return json.dumps(text, ensure_ascii=False)


def _unique_pairs(label):
    def hook(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise NullificationError([label + ': duplicate JSON key ' + quote(key)])
            seen[key] = value
        return seen
    return hook


def parse_document(text, label):
    """Parse decisions JSON; a repeated object key is refused rather than silently keeping the last value."""
    try:
        return json.loads(text, object_pairs_hook=_unique_pairs(label))
    except NullificationError:
        raise
    except ValueError as error:
        raise NullificationError([label + ': not valid JSON: ' + str(error)]) from None


def decode(data, label):
    """data as UTF-8 text. Bytes that are not UTF-8 are refused with an exact message naming the first of them, before
    anything is written, rather than ending in a traceback."""
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError as error:
        raise NullificationError([label + ': not valid UTF-8 (byte 0x' + format(data[error.start], '02x') + ' at offset '
                                  + str(error.start) + ')']) from None


def read_document(path):
    """The decisions file at path. A missing file is an error, never an empty contract."""
    path = Path(path)
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        raise NullificationError([str(path) + ': missing nullification contract']) from None
    except OSError as error:
        raise NullificationError([str(path) + ': cannot read nullification contract: ' + (error.strerror or str(error))]) from None
    return parse_document(decode(data, str(path)), str(path))


def canonical_document(document):
    """The validated document in canonical form: fields in schema order, two-space JSON, final newline."""
    decisions = validate(document)
    value = {'schema': SCHEMA, 'decisions': [{field: item[field] for field in FIELDS} for item in decisions]}
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def _timestamp(value):
    match = re.fullmatch(DECIDED_AT_PATTERN, value, re.ASCII) if isinstance(value, str) else None
    if not match:
        return False
    year, month, day, hour, minute, second = (int(x) for x in match.groups()[:6])
    try:
        datetime(year, month, day, hour, minute, second)
    except ValueError:
        return False
    offset = match.group(8)
    return offset == 'Z' or (int(offset[1:3]) <= 23 and int(offset[4:6]) <= 59)


def validate(document):
    """The decisions of a contract document, or NullificationError naming every structural problem.

    Checks the schema identifier, fields, non-empty text, scope, key shape, timestamp and (scope, key)
    uniqueness. Keys are resolved against the repository by resolve()."""
    if not isinstance(document, dict):
        raise NullificationError(['nullification contract must be a JSON object'])
    messages = ['unknown top-level field ' + quote(field) for field in sorted(set(document) - {'schema', 'decisions'})]
    if document.get('schema') != SCHEMA:
        messages.append('schema must be ' + quote(SCHEMA))
    if 'decisions' not in document:
        messages.append('missing decisions')
    elif not isinstance(document['decisions'], list):
        messages.append('decisions must be an array')
    if messages:
        raise NullificationError(messages)
    seen = {}
    for index, item in enumerate(document['decisions']):
        prefix = 'decision ' + str(index) + ': '
        if not isinstance(item, dict):
            messages.append(prefix + 'must be an object')
            continue
        messages += [prefix + 'unknown field ' + quote(field) for field in sorted(set(item) - set(FIELDS))]
        for field in FIELDS:
            surrogate = _SURROGATE.search(item[field]) if isinstance(item.get(field), str) else None
            if field not in item:
                messages.append(prefix + 'missing ' + field)
            elif surrogate:
                messages.append(prefix + field + ' contains a lone surrogate (U+' + format(ord(surrogate.group()), '04X') + ') and cannot be '
                                'written as UTF-8')
            elif field == 'decidedAt':
                if not _timestamp(item[field]):
                    messages.append(prefix + 'decidedAt must be an ISO-8601 date-time with seconds and a UTC offset, '
                                    'such as 2026-11-01T17:45:00Z')
            elif not isinstance(item[field], str) or not item[field].strip():
                messages.append(prefix + field + ' must be a non-empty string')
        scope, key = item.get('scope'), item.get('key')
        if isinstance(scope, str) and scope.strip() and scope not in SCOPES:
            messages.append(prefix + 'unknown scope ' + quote(scope) + ' (expected ' + ', '.join(SCOPES[:-1]) + ' or ' + SCOPES[-1] + ')')
        if scope in SCOPES and isinstance(key, str) and key.strip() and not _SURROGATE.search(key):
            if not re.fullmatch(KEY_PATTERNS[scope], key, re.ASCII):
                messages.append(prefix + scope + ' key ' + quote(key) + ' must match ' + KEY_PATTERNS[scope])
            if (scope, key) in seen:
                messages.append(prefix + 'duplicates decision ' + str(seen[(scope, key)]) + ' (' + scope + ' ' + quote(key) + ')')
            else:
                seen[(scope, key)] = index
    if messages:
        raise NullificationError(messages)
    return [dict(item) for item in document['decisions']]


def definition_id(instance):
    """The inventory's definitionId: assemble_artwork_inventory.py collapses instances by kind, name and quote."""
    text = (instance.get('kind') or '') + '\0' + (instance.get('name') or '') + '\0' + (instance.get('quote') or '')
    return hashlib.sha256(text.encode('utf-8', 'surrogatepass')).hexdigest()[:16]


def _base_key(instance):
    return instance['file'] + '#' + instance['locator'] + '#' + instance['identifier']


def strings(value, path=''):
    """Every string value in a JSON value with its path, lists written as []."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from strings(item, path + '.' + key if path else key)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item, path + '[]')


def names(value, identity):
    """True when some string in value is exactly identity."""
    return any(text == identity for _, text in strings(value))


def reason_for(path):
    """Why a recipe naming an identity at path is struck: it is the study subject, it renders it, or it compares with it."""
    if path in ('demonstrates.effect', 'catalogueEffect'):
        return 'subject'
    if path.startswith(('commands', 'actions')):
        return 'commands'
    return 'comparison'


class Sources:
    """The repository files decisions resolve against, each read once.

    inventory=False (a Gallery build, a packaged SDK without native/evidence) leaves historical keys to
    apply_nullification.py, which always resolves every scope."""

    def __init__(self, root, inventory=True):
        self.root = Path(root)
        self.with_inventory = inventory

    def read(self, name):
        return json.loads((self.root / name).read_text(encoding='utf-8'))

    def digest(self, name):
        path = self.root / name
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

    @cached_property
    def inventory(self):
        if not self.with_inventory:
            raise NullificationError(['historical keys need ' + INVENTORY + '; resolve them with native/scripts/apply_nullification.py'])
        return self.read(INVENTORY)

    @cached_property
    def instance_keys(self):
        """file#locator#identifier and file#locator#identifier#kind -> instance positions."""
        three, four = {}, {}
        for position, instance in enumerate(self.inventory['instances']):
            base = _base_key(instance)
            three.setdefault(base, []).append(position)
            four.setdefault(base + '#' + instance['kind'], []).append(position)
        return three, four

    @cached_property
    def definitions(self):
        return {d['definitionId']: d for d in self.inventory['definitions']}

    @cached_property
    def members(self):
        out = {}
        for position, instance in enumerate(self.inventory['instances']):
            out.setdefault(definition_id(instance), []).append(position)
        return out

    def canonical_key(self, position):
        """The shortest key that names exactly this instance: #kind is appended only where the triple collides."""
        instance = self.inventory['instances'][position]
        base = _base_key(instance)
        return base if len(self.instance_keys[0][base]) == 1 else base + '#' + instance['kind']

    def instance(self, position):
        instance = self.inventory['instances'][position]
        mapping = instance.get('mapping') or {}
        return {'key': self.canonical_key(position), 'index': position, 'file': instance['file'], 'locator': instance['locator'],
                'identifier': instance['identifier'], 'kind': instance['kind'], 'name': instance['name'],
                'editionKey': instance['editionKey'], 'definitionId': definition_id(instance), 'quoteVerified': instance['quoteVerified'],
                'mapping': {'status': mapping.get('status'), 'currentId': mapping.get('currentId')}}

    def definition(self, identifier):
        d = self.definitions[identifier]
        mapping = d.get('mapping') or {}
        return {'definitionId': d['definitionId'], 'kind': d['kind'], 'name': d['name'], 'identifier': d['identifier'],
                'editions': d['editions'], 'files': d['files'], 'instances': d['instances'], 'variants': d['variants'],
                'mapping': {'status': mapping.get('status'), 'currentId': mapping.get('currentId')}}

    @cached_property
    def catalogue(self):
        return {row['id']: row for row in self.read(CATALOGUE)}

    @cached_property
    def ledger(self):
        return {row['newId']: row for row in self.read(PORT_LEDGER)['entries']}

    @cached_property
    def recipes(self):
        return self.read(RECIPES)

    @cached_property
    def captures(self):
        return {row['component'] + '/' + row['state']: row for row in self.read(CAPTURES)['captures']}

    @cached_property
    def components(self):
        return self.read(COMPONENTS)

    @cached_property
    def recipe_captures(self):
        """Gallery recipe id -> the component captures (component/state) whose state loads it."""
        out = {}
        for component in self.components['components']:
            for state in component['states']:
                if state.get('recipeId'):
                    out.setdefault(state['recipeId'], []).append(component['id'] + '/' + state['id'])
        return out

    @cached_property
    def engine_defaults(self):
        """Catalogue identity -> commands whose omitted effect the engine replaces with it (components.json catalogue tables)."""
        out = {}
        for op, table in self.components['catalogue']['commands'].items():
            for record in table:
                default = (record.get('default') or '').strip()
                if record['field'] == 'effect' and len(default) > 2 and default[0] == default[-1] and default[0] in '`"':
                    out.setdefault(default[1:-1], []).append(op)
        return {identity: sorted(ops) for identity, ops in out.items()}

    @cached_property
    def pages(self):
        """docs/current pages as they read with no decision applied: the generated catalogue pages rendered from the
        complete components.json section, every other page from disk, and the ledger left out. What a decision strikes
        therefore never depends on whether an earlier, possibly interrupted, apply already omitted something."""
        docs = reference_docs()
        rendered = docs.catalogue_pages(self.components['catalogue'], [])
        out = []
        for path in sorted((self.root / DOCS).glob('*.md')):
            if path.name != docs.NULLIFICATION_PAGE:
                out.append((path.name, rendered.get(path.name, path.read_text(encoding='utf-8')).split('\n')))
        return out


def reference_docs():
    """native/scripts/build_reference_docs.py beside this module, which renders the pages decisions act on."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import build_reference_docs
    return build_reference_docs


FIXED_RECIPE = re.compile(r"recipes\.find\(\s*(\w+)\s*=>\s*\1\.id===\s*'([^']+)'\s*\)|\bexample\(\s*'([^']+)'\s*\)")


def fixed_controls(template, recipes):
    """The controls of the Gallery page (native/web/template.html) that load a recipe by a fixed identity, as
    {control: candidate recipe ids}: a button that finds one recipe by its id (directly in the library, or through the
    page's example(id), which looks in the library and then in the Workshop examples, both of which omit a struck recipe),
    and a scenic button that loads the first recipe of recipes with its originalScenic value. Omitting every candidate
    from the library leaves the control on the page with nothing to load."""
    out = {}
    for line in template.split('\n'):
        for match in FIXED_RECIPE.finditer(line):
            controls = re.findall(r"\$\('([A-Za-z0-9_-]+)'\)\.on\w+=", line[:match.start()])
            out.setdefault('#' + controls[-1] if controls else 'a script of the page', []).append(match.group(2) or match.group(3))
    for value in dict.fromkeys(re.findall(r'data-scenic-open="([^"]+)"', template)):
        out['[data-scenic-open="' + value + '"]'] = [recipe['id'] for recipe in recipes if recipe.get('originalScenic') == value]
    return {control: list(dict.fromkeys(ids)) for control, ids in out.items()}


def control_warnings(controls, struck, recipes):
    """For a decision that strikes recipes: each fixed control left with nothing to load once everything in struck
    (the Gallery recipes all decisions strike) is omitted, and one of whose candidates is among recipes."""
    return ['the Gallery control ' + control + ' in ' + TEMPLATE + ' loads recipe ' + ', '.join(ids) + ' by a fixed identity; with '
            + ('it' if len(ids) == 1 else 'them') + ' struck the control stays on the page and reports an error when used, until '
            'the template handles a struck recipe' for control, ids in controls.items() if ids and set(ids) <= struck and set(ids) & set(recipes)]


def capture_warnings(captures_by_recipe, recipes):
    out = []
    for recipe in recipes:
        for capture in captures_by_recipe.get(recipe, []):
            out.append('component capture ' + capture + ' loads Gallery recipe ' + recipe + ', which this decision strikes; the next '
                       'capture_reference_components.py run fails with "Missing reference recipe ' + recipe + '" until that state is '
                       're-pointed or removed')
    return out


def _docs_effects(sources, identity):
    """Pages whose catalogue section or index row is omitted, and the other lines that keep naming the identity."""
    pattern = re.compile('(?<![' + _ID_CHARACTERS + '])' + re.escape(identity) + '(?![' + _ID_CHARACTERS + '])')
    pages, mentions = [], []
    for name, lines in sources.pages:
        inside = False
        for number, line in enumerate(lines, 1):
            if line.startswith(('# ', '## ', '### ')):
                inside = line == '### ' + identity
                if inside:
                    pages.append({'page': name, 'omits': 'section ' + identity})
                    continue
            if inside:
                continue
            if line.startswith('| [`' + identity + '`]('):
                pages.append({'page': name, 'omits': 'index row'})
            elif pattern.search(line):
                mentions.append({'page': name, 'line': number, 'text': line.strip()})
    return pages, mentions


def _resolve_one(index, item, sources):
    """(resolved decision, error message or None)."""
    scope, key = item['scope'], item['key']
    prefix = 'decision ' + str(index) + ': ' + scope + ' key ' + quote(key)
    out = {'decision': index, **{field: item[field] for field in FIELDS}, 'resolved': None, 'strikes': {}, 'retained': {}, 'warnings': []}
    if scope == 'historical-definition':
        if key not in sources.definitions:
            return None, prefix + ' does not resolve against ' + INVENTORY + ' definitions'
        out['resolved'] = sources.definition(key)
        out['strikes'] = {'instances': [sources.instance(p) for p in sources.members[key]]}
    elif scope == 'historical-instance':
        three, four = sources.instance_keys
        matches = three.get(key, []) + four.get(key, [])
        if not matches:
            return None, prefix + ' does not resolve against ' + INVENTORY + ' instances'
        if len(matches) > 1:
            kinds = ', '.join(sorted({sources.inventory['instances'][p]['kind'] for p in matches}))
            hint = 'append "#<kind>" to choose one' if key in three else 'nullify its definition instead'
            return None, prefix + ' matches ' + str(len(matches)) + ' instances (kinds ' + kinds + '); ' + hint
        found = sources.instance(matches[0])
        definition = sources.definitions[found['definitionId']]
        out['resolved'] = {**found, 'definition': {x: definition[x] for x in ('definitionId', 'kind', 'name', 'instances', 'variants')}}
        out['strikes'] = {'instances': [found]}
    elif scope == 'current-identity':
        entry = sources.catalogue.get(key)
        if entry is None:
            return None, prefix + ' does not resolve against ' + CATALOGUE
        ledger = sources.ledger.get(key)
        recipes = [recipe['id'] for recipe in sources.recipes if names(recipe, key)]
        captures = [name for name, row in sources.captures.items() if names(row, key)]
        pages, mentions = _docs_effects(sources, key)
        out['resolved'] = dict(entry)
        out['strikes'] = {'catalogue': {x: entry[x] for x in ('id', 'name', 'contract', 'family')},
                          'portLedger': None if ledger is None else {x: ledger[x] for x in ('newId', 'oldId', 'state')},
                          'recipes': recipes, 'captures': sorted(captures),
                          'docsPages': sorted(pages, key=lambda x: (x['page'], x['omits']))}
        defaults = sources.engine_defaults.get(key, [])
        loading = sorted(c for recipe in recipes for c in sources.recipe_captures.get(recipe, []))
        out['retained'] = {'docsMentions': mentions, 'engineDefaultFor': defaults, 'capturesLoadingStruckRecipes': loading}
        out['warnings'] = [key + ' is the engine default effect for ' + op + ' commands that omit effect; omitting it from the docs and '
                           'the Gallery does not stop the core from rendering it. Removing it needs a core change that chooses a new '
                           'default, and a new qualification.' for op in defaults] + capture_warnings(sources.recipe_captures, recipes)
    elif key.startswith('recipe:'):
        recipe = next((r for r in sources.recipes if r['id'] == key[len('recipe:'):]), None)
        if recipe is None:
            return None, prefix + ' does not resolve against ' + RECIPES
        out['resolved'] = {'kind': 'recipe', 'id': recipe['id'], 'name': recipe['name']}
        out['strikes'] = {'recipes': [recipe['id']]}
        out['retained'] = {'capturesLoadingStruckRecipes': sorted(sources.recipe_captures.get(recipe['id'], []))}
        out['warnings'] = capture_warnings(sources.recipe_captures, [recipe['id']])
    else:
        name = key[len('capture:'):]
        row = sources.captures.get(name)
        if row is None:
            return None, prefix + ' does not resolve against ' + CAPTURES
        embedded = '](images/' + row['image'] + ')'
        out['resolved'] = {'kind': 'capture', 'component': row['component'], 'state': row['state'], 'label': row['label'],
                           'image': row['image'], 'pngSha256': row['pngSha256']}
        out['strikes'] = {'captures': [name]}
        out['retained'] = {'image': row['image'],
                           'imageSharedWith': sorted(other for other, x in sources.captures.items() if other != name and x['image'] == row['image']),
                           'pages': sorted(page for page, lines in sources.pages if any(embedded in line for line in lines))}
        out['warnings'] = ['Components.md and the components.json registry are maintained by hand: the atlas keeps this capture and its '
                           'image until the state is removed from both and the atlas is recaptured with capture_reference_components.py']
    return out, None


def resolve(document, sources, scopes=SCOPES):
    """Validate the whole document, then resolve every decision in scopes against sources.

    Returns the resolved decisions in contract order: what each names, what it strikes, what is retained and
    why, and warnings. Raises NullificationError with every unresolvable key."""
    decisions = validate(document)
    resolved, messages = [], []
    for index, item in enumerate(decisions):
        if item['scope'] not in scopes:
            continue
        row, error = _resolve_one(index, item, sources)
        if error:
            messages.append(error)
        else:
            resolved.append(row)
    if messages:
        raise NullificationError(messages)
    _note_overlaps(resolved)
    return resolved


def _note_overlaps(resolved):
    historical = [(row, {x['index'] for x in row['strikes']['instances']}) for row in resolved if row['scope'] in HISTORICAL_SCOPES]
    for row, positions in historical:
        for other, covering in historical:
            if other is not row and positions <= covering and (other['scope'] == 'historical-definition' or other['decision'] < row['decision']):
                row['warnings'].append('every instance it strikes is already struck by decision ' + str(other['decision']))
                break


def load_contract(root, path=None, scopes=CONTRACT_SCOPES):
    """The contract's decisions in scopes, the whole document validated, resolved against the repository at root."""
    root = Path(root)
    document = read_document(root / CONTRACT if path is None else path)
    return resolve(document, Sources(root, inventory=any(scope in HISTORICAL_SCOPES for scope in scopes)), scopes)


def _variants(value):
    try:
        return int((value or {}).get('count') or 0)
    except (TypeError, ValueError):
        return 0


def historical_counts(resolved):
    """Struck historical instances (by position) and the definitions none of whose instances remain."""
    struck, definitions = {}, {}
    for row in resolved:
        if row['scope'] == 'historical-definition':
            d = row['resolved']
        elif row['scope'] == 'historical-instance':
            d = row['resolved']['definition']
        else:
            continue
        definitions[d['definitionId']] = d
        for instance in row['strikes']['instances']:
            struck[instance['index']] = instance
    per_definition = Counter(x['definitionId'] for x in struck.values())
    full = [d for identifier, d in definitions.items() if per_definition.get(identifier) == d['instances']]
    return struck, full


def totals(resolved):
    struck, full = historical_counts(resolved)
    recipes = {x for row in resolved for x in row['strikes'].get('recipes', [])}
    captures = {x for row in resolved for x in row['strikes'].get('captures', [])}
    return {'decisions': len(resolved), 'byScope': {scope: sum(row['scope'] == scope for row in resolved) for scope in SCOPES},
            'historicalInstances': len(struck), 'historicalDefinitions': len(full),
            'historicalVariants': sum(_variants(d['variants']) for d in full),
            'currentIdentities': sum(row['scope'] == 'current-identity' for row in resolved),
            'recipes': len(recipes), 'captures': len(captures)}


def references_by_identity(recipes, identities):
    """identity -> {recipe id: reasons} for every recipe in which some string is exactly a nullified identity."""
    identities = set(identities)
    out = {identity: {} for identity in identities}
    if not identities:
        return out
    for recipe in recipes:
        for path, text in strings(recipe):
            if text in identities:
                out[text].setdefault(recipe['id'], set()).add(reason_for(path))
    return out


def gallery_strikes(recipes, resolved):
    """Recipe id -> sorted reasons, for every Gallery recipe the decisions strike."""
    identities = [row['key'] for row in resolved if row['scope'] == 'current-identity']
    named = {row['resolved']['id'] for row in resolved if row['scope'] == 'rendering-output' and row['resolved']['kind'] == 'recipe'}
    out = {}
    for found in references_by_identity(recipes, identities).values():
        for recipe, reasons in found.items():
            out.setdefault(recipe, set()).update(reasons)
    for recipe in recipes:
        if recipe['id'] in named:
            out.setdefault(recipe['id'], set()).add('decision')
    return {recipe: sorted(reasons) for recipe, reasons in out.items()}


def gallery_recipes(recipes, resolved):
    """The Gallery library without what the decisions strike: the single choke point for the library and its attract
    rotation. With no decision the same list object is returned."""
    if not resolved:
        return recipes
    struck = gallery_strikes(recipes, resolved)
    return [recipe for recipe in recipes if recipe['id'] not in struck]


def gallery_effects(recipes, resolved, sources):
    """Per contract-scope decision (by position): Gallery recipes struck, counts by reason, ids and the captures that load them."""
    identities = [row['key'] for row in resolved if row['scope'] == 'current-identity']
    found = references_by_identity(recipes, identities)
    out = {}
    for row in resolved:
        if row['scope'] == 'current-identity':
            struck = found[row['key']]
        elif row['scope'] == 'rendering-output' and row['resolved']['kind'] == 'recipe':
            struck = {row['resolved']['id']: {'decision'}}
        else:
            continue
        ids = sorted(struck)
        reasons = Counter(reason for found_reasons in struck.values() for reason in found_reasons)
        loading = sorted(c for recipe in ids for c in sources.recipe_captures.get(recipe, []))
        out[row['decision']] = {'recipes': len(ids), 'byReason': dict(sorted(reasons.items())), 'ids': ids,
                                'capturesLoadingStruckRecipes': loading}
    return out


# ---- INVENTORY.md --------------------------------------------------------------------------------------------

TOTAL_ROWS = ('entityInstances', 'distinctDefinitions', 'enumeratedVariantsSum', 'quoteVerifiedInstances', 'quoteUnverifiedInstances',
              'distinctFiles', 'distinctWasmModules')
TABLE_HEADINGS = ('## Totals', '### Distinct definitions by kind',
                  '### Instances by edition (normalized key; raw labels kept in INVENTORY.json byEditionLabel)',
                  '### Mapping to the current contract')
SECTION = '## Nullified by the operator'


def plain(text):
    """Text as one line that XML 1.0, and so the PDF build, accepts: every character at which str.splitlines() ends a
    line becomes a space, and every other control character, noncharacter U+FFFE/U+FFFF or lone surrogate U+FFFD."""
    return _CONTROLS.sub('\ufffd', _LINE_BREAKS.sub(' ', str(text)))


def markdown_text(text):
    """Free text (a name, reason or author from the review page) as literal Markdown table-cell content: one line (see
    plain), HTML escaped, and the inline syntax that could open a link, emphasis, code span or cell escaped, so that it
    can neither inject markup into the rendered HTML nor break the XHTML the PDF build parses. Parentheses are escaped as
    well because build_reference_docs.validate finds links by scanning the raw text, which ignores backslashes."""
    text = plain(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'([\\`*_\[\]()|])', r'\\\1', text)


def cell(text):
    return plain(text).replace('|', '\\|')


def code(text):
    text = str(text)
    fence = '`' * (max((len(run) for run in re.findall('`+', text)), default=0) + 1)
    pad = ' ' if text.startswith('`') or text.endswith('`') else ''
    return fence + pad + cell(text) + pad + fence


def strike_summary(row):
    if row['scope'] in HISTORICAL_SCOPES:
        n = len(row['strikes']['instances'])
        return str(n) + (' instance' if n == 1 else ' instances')
    if row['scope'] == 'current-identity':
        s = row['strikes']
        recipes, captures, pages = len(s['recipes']), len(s['captures']), len(s['docsPages'])
        return ', '.join(['catalogue entry', 'port-ledger entry' if s['portLedger'] else 'no port-ledger entry',
                          str(recipes) + (' recipe' if recipes == 1 else ' recipes'),
                          str(captures) + (' capture' if captures == 1 else ' captures'),
                          str(pages) + (' page' if pages == 1 else ' pages')])
    return row['resolved']['kind']


def _replace_table(text, heading, rows):
    marker = '\n' + heading + '\n\n'
    if text.count(marker) != 1:
        raise NullificationError([INVENTORY_MARKDOWN + ' lacks the ' + quote(heading) + ' table; regenerate it with '
                                  'native/scripts/assemble_artwork_inventory.py, then apply again'])
    head, rest = text.split(marker, 1)
    lines = rest.split('\n')
    count = 0
    while count < len(lines) and lines[count].startswith('|'):
        count += 1
    if count < 2:
        raise NullificationError([INVENTORY_MARKDOWN + ' has no table under ' + quote(heading)])
    return head + marker + '\n'.join(rows + lines[count:])


def _table(header, rows):
    return ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)] + ['| ' + ' | '.join(str(x) for x in row) + ' |' for row in rows]


def inventory_markdown(text, inventory, resolved, contract_sha256):
    """INVENTORY.md with a Nullified column beside every totals table and one "Nullified by the operator" section.

    The values the assembler wrote are recomputed from INVENTORY.json, so applying twice, or a different decision set
    after an earlier one, never stacks columns or sections. Everything else is left byte for byte."""
    t = inventory['totals']
    struck, full = historical_counts(resolved)
    instances = list(struck.values())
    verified = sum(1 for x in instances if x['quoteVerified'])
    nullified = {'entityInstances': len(instances), 'distinctDefinitions': len(full), 'enumeratedVariantsSum': sum(_variants(d['variants']) for d in full),
                 'quoteVerifiedInstances': verified, 'quoteUnverifiedInstances': len(instances) - verified}
    by_kind, full_by_kind = Counter(x['kind'] for x in instances), Counter(d['kind'] for d in full)
    by_edition, by_status = Counter(x['editionKey'] for x in instances), Counter(x['mapping']['status'] for x in instances)
    text = _replace_table(text, TABLE_HEADINGS[0], _table(('Measure', 'Value', 'Nullified'),
                          [(k, t[k], nullified.get(k, 'n/a')) for k in TOTAL_ROWS]))
    text = _replace_table(text, TABLE_HEADINGS[1], _table(('Kind', 'Definitions', 'Instances', 'Nullified definitions', 'Nullified instances'),
                          [(k, t['definitionsByKind'][k], t['byKind'].get(k, 0), full_by_kind.get(k, 0), by_kind.get(k, 0))
                           for k in sorted(t['definitionsByKind'], key=str)]))
    text = _replace_table(text, TABLE_HEADINGS[2], _table(('Edition', 'Instances', 'Nullified'),
                          [(k, t['byEdition'][k], by_edition.get(k, 0)) for k in sorted(t['byEdition'], key=str)]))
    text = _replace_table(text, TABLE_HEADINGS[3], _table(('Status', 'Instances', 'Nullified'),
                          [(k, v, by_status.get(k, 0)) for k, v in sorted(t['mappingStatus'].items(), key=lambda kv: str(kv[0]))]))
    paragraph = ('Decisions from `' + CONTRACT + '` (SHA-256 `' + contract_sha256 + '`), applied by `native/scripts/apply_nullification.py`; '
                 '`NULLIFIED.json` beside this file lists everything each decision strikes. The totals above still count what the '
                 'host-resident files define; the Nullified columns count the historical instances and definitions the operator struck '
                 'from the final contract, and a definition counts once none of its instances remain. Nothing is deleted: the extracts, '
                 'the native core, its fixtures and evidence are unchanged, and deleting a current identity from the core is a later, '
                 'separately qualified step.')
    if resolved:
        body = '\n'.join(_table(('#', 'Scope', 'Key', 'Name', 'Strikes', 'Reason', 'Decided by', 'Decided at'),
                                [(row['decision'], row['scope'], code(row['key']), markdown_text(row['name']), strike_summary(row),
                                  markdown_text(row['reason']), markdown_text(row['decidedBy']), markdown_text(row['decidedAt']))
                                 for row in resolved]))
    else:
        body = 'No decisions.'
    block = SECTION + '\n\n' + paragraph + '\n\n' + body + '\n'
    marker = '\n' + SECTION + '\n'
    if marker in text:
        head, rest = text.split(marker, 1)
        at = rest.find('\n## ')
        if at == -1:
            raise NullificationError([INVENTORY_MARKDOWN + ': nothing follows ' + quote(SECTION)])
        tail = rest[at + 1:]
    else:
        anchor = '\n## Count reconciliation\n'
        if anchor not in text:
            raise NullificationError([INVENTORY_MARKDOWN + ' lacks "## Count reconciliation"; regenerate it with '
                                      'native/scripts/assemble_artwork_inventory.py, then apply again'])
        head, tail = text.split(anchor, 1)
        tail = anchor[1:] + tail
    return head.rstrip('\n') + '\n\n' + block + '\n' + tail
