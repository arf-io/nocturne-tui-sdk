"""Compile explicit manual field tables; do not infer undocumented defaults."""

import argparse
import hashlib
import json
from pathlib import Path
import re

REGISTRY = [
    ('define', 'VALUES-EVENTS-AND-TRANSACTIONS.md', ['Define, bind and edit a value'], ''),
    ('bind', 'VALUES-EVENTS-AND-TRANSACTIONS.md', ['Define, bind and edit a value'], ''),
    ('remove-value', 'VALUES-EVENTS-AND-TRANSACTIONS.md', ['Teardown and rollback'], ''),
    ('schedule', 'VALUES-EVENTS-AND-TRANSACTIONS.md', ['Scheduling and retained triggers'], ''),
    ('cancel-schedule', 'VALUES-EVENTS-AND-TRANSACTIONS.md', ['Scheduling and retained triggers'], ''),
    ('floor', 'FLOOR-AND-DEPOSITS.md', ['Complete floor reference'], ''),
    ('environment', 'ENVIRONMENT-AND-BACKGROUNDS.md', ['Complete environment reference'], ''),
    ('surface', 'SURFACES-WATER-AND-HEAT.md', ['Surface settings'], ''),
    ('camera', 'CAMERA-AND-FLIGHT.md', ['Direct pose and projection'], ''),
    ('flight', 'CAMERA-AND-FLIGHT.md', ['Authored flight steps'], 'steps[].'),
    ('widget', 'WIDGETS-AND-NOTIFICATIONS.md', ['Widget families'], ''),
    ('status', 'WIDGETS-AND-NOTIFICATIONS.md', ['Notification authoring'], ''),
    ('text', 'TEXT-TREATMENTS.md', ['Authoring fields'], ''),
    ('material', 'MATERIALS-AND-COLOR.md', ['Every material option'], ''),
    ('material', 'MATERIALS-AND-COLOR.md', ['Tracks and partial edits'], 'alpha.'),
    ('material', 'MATERIALS-AND-COLOR.md', ['Tracks and partial edits'], 'index.'),
    ('window', 'WINDOWS-AND-AREAS.md', ['Create and edit a window', 'Readability and transition treatment'], ''),
    ('area', 'WINDOWS-AND-AREAS.md', ['Areas, notifications, cursors and wait indicators'], ''),
    ('node', 'GRAPHS-MODELS-AND-PATHS.md', ['Graph card fields'], ''),
    ('prompt', 'INPUT-CURSORS-AND-WAIT.md', ['Prompt options'], ''),
    ('indicator', 'INPUT-CURSORS-AND-WAIT.md', ['Cursor and wait presentation'], ''),
    ('pause', 'LIFECYCLE-AND-TEARDOWN.md', ['Scene clock and pause'], ''),
    ('time', 'LIFECYCLE-AND-TEARDOWN.md', ['Scene clock and pause'], ''),
    ('stop', 'LIFECYCLE-AND-TEARDOWN.md', ['Stop, cancel and resume an emitter'], ''),
    ('cancel', 'LIFECYCLE-AND-TEARDOWN.md', ['Stop, cancel and resume an emitter'], ''),
    ('resume', 'LIFECYCLE-AND-TEARDOWN.md', ['Stop, cancel and resume an emitter'], ''),
    ('clear-instance', 'LIFECYCLE-AND-TEARDOWN.md', ['Release an emitter and clean its deposits'], ''),
    ('clear-deposits', 'LIFECYCLE-AND-TEARDOWN.md', ['Release an emitter and clean its deposits'], ''),
    ('clear', 'LIFECYCLE-AND-TEARDOWN.md', ['Clear a selected family'], ''),
    ('reset', 'LIFECYCLE-AND-TEARDOWN.md', ['Reset and start again'], ''),
    ('emitter', 'WEATHER-AND-EMITTERS.md', [
        'Identity and birth schedule', 'Birth geometry and motion', 'Forces',
        'Lifetime and ending', 'Appearance, depth and contact',
    ], ''),
]


def section_text(source, title):
    sections = re.split(r'^## (.+)$', source, flags=re.MULTILINE)
    matches = [sections[index + 1] for index in range(1, len(sections), 2)
               if sections[index].strip() == title]
    if len(matches) != 1:
        raise ValueError('Missing or duplicate manual section: ' + title)
    return matches[0]


def table_cells(line):
    return [cell.strip().replace(r'\|', '|')
            for cell in re.split(r'(?<!\\)\|', line.strip())[1:-1]]


def scriptJSON(value):
    """Keep closing tags out of script source while retaining decoded text."""
    return json.dumps(value, separators=(',', ':')).replace('<', r'\u003c')


def buildWorkshopHelp(root, metadata):
    root = Path(root)
    declared = {(row['op'], row['field']) for row in metadata['fields']}
    parameters = {}
    for operation, filename, sections, prefix in REGISTRY:
        if operation not in metadata['operations']:
            continue
        path = root / 'docs/manual' / filename
        original = path.read_bytes()
        source = original.decode('utf-8')
        source_hash = hashlib.sha256(original).hexdigest()
        for section in sections:
            header = None
            for line in section_text(source, section).splitlines():
                if not line.startswith('|'):
                    continue
                cells = table_cells(line)
                fields = re.findall(r'`([^`]+)`', cells[0]) if cells else []
                if not fields:
                    if cells and not all(re.fullmatch(r'[-: ]+', cell) for cell in cells):
                        header = cells
                    continue
                if header is None or not re.search(r'\b(fields?|options?|parameters?)\b', header[0], re.IGNORECASE):
                    continue
                if len(cells) not in (2, 3):
                    raise ValueError('Unsupported manual field table: ' + section)
                for name in fields:
                    if header[0].lower().startswith('command/'):
                        if not name.startswith(operation + '.'):
                            continue
                        field = name[len(operation) + 1:]
                    elif name.startswith(operation + '.'):
                        field = name[len(operation) + 1:]
                    else:
                        field = prefix + name
                    if (operation, field) not in declared:
                        raise ValueError('Unregistered manual field: ' + operation + '.' + field)
                    key = operation + '.' + field
                    if key in parameters:
                        raise ValueError('Duplicate manual field: ' + key)
                    parameters[key] = {
                        'default': cells[1] if len(cells) == 3 else None,
                        'defaultLabel': header[1] if len(cells) == 3 else None,
                        'description': cells[-1], 'sourceFields': fields,
                        'sourcePath': path.relative_to(root).as_posix(),
                        'section': section, 'sourceSha256': source_hash,
                    }
    return {
        'schema': 'nocturne.workshop-help.v1', 'parameters': parameters,
        'documentedFields': len(parameters), 'totalFields': len(declared),
        'manualComplete': False,
        'scope': 'Explicit component-table guidance only; not native semantic qualification',
        'pendingFields': sorted(operation + '.' + field for operation, field in declared
                                if operation + '.' + field not in parameters),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.output.exists():
        parser.error('Output already exists')
    from build_gallery import readWorkshopMetadata, ROOT
    result = buildWorkshopHelp(ROOT, readWorkshopMetadata())
    arguments.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['documentedFields', 'totalFields', 'manualComplete']}))


if __name__ == '__main__':
    main()
