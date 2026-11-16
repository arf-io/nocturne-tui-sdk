#!/usr/bin/env python3
"""Contact sheets of the Gallery provenance census: one sheet per generator (every entry it renders, or an even
sample of at most --per-sheet), labelled with entry id and provenance class, from the thumbnails that
render_gallery_census.py took of the real built Gallery.

Usage: census_contact_sheets.py --census DIR --report PROVENANCE-CENSUS.json --output DIR [--per-sheet 36]
"""
from pathlib import Path
import argparse, json, re
from PIL import Image, ImageDraw, ImageFont

COLOURS = {'original': (120, 210, 150), 'original-framed': (230, 190, 90), 'rc4-authored': (150, 170, 240),
           'unresolved-claim': (240, 110, 110), 'synthetic': (200, 120, 200)}


def font(size):
    for path in ('/System/Library/Fonts/Menlo.ttc', '/usr/share/fonts/TTF/DejaVuSansMono.ttf'):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def sheet(rows, thumbs, title, width=240, cols=6):
    f, big = font(11), font(16)
    cell_h = int(width * 0.62) + 30
    n = len(rows)
    img = Image.new('RGB', (cols * width + (cols + 1) * 6, 40 + ((n + cols - 1) // cols) * (cell_h + 6) + 6), (12, 12, 18))
    d = ImageDraw.Draw(img)
    d.text((8, 10), title, fill=(235, 235, 240), font=big)
    for i, r in enumerate(rows):
        x = 6 + (i % cols) * (width + 6)
        y = 40 + (i // cols) * (cell_h + 6)
        if r.get('thumb'):
            t = Image.open(thumbs / r['thumb']).convert('RGB')
            t = t.resize((width, int(t.height * width / t.width)))
            img.paste(t.crop((0, 0, width, min(t.height, cell_h - 30))), (x, y))
        c = COLOURS.get(r['class'], (200, 200, 200))
        d.rectangle([x, y + cell_h - 30, x + width, y + cell_h], fill=(24, 24, 32))
        d.rectangle([x, y + cell_h - 30, x + 4, y + cell_h], fill=c)
        d.text((x + 8, y + cell_h - 28), r['id'][:36], fill=(230, 230, 235), font=f)
        d.text((x + 8, y + cell_h - 14), r['class'], fill=c, font=f)
    return img


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--census', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--per-sheet', type=int, default=36)
    a = p.parse_args()
    report = json.loads(a.report.read_text())
    a.output.mkdir(parents=True, exist_ok=True)
    groups = {}
    for r in report['entries']:
        groups.setdefault(r['generator'], []).append(r)
    index = []
    for g, rows in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        sample = rows if len(rows) <= a.per_sheet else [rows[round(i * (len(rows) - 1) / (a.per_sheet - 1))] for i in range(a.per_sheet)]
        name = re.sub(r'[^A-Za-z0-9_.-]', '_', g) + '.jpg'
        classes = {}
        for r in rows:
            classes[r['class']] = classes.get(r['class'], 0) + 1
        title = f"{g}: {len(rows)} entries ({', '.join(f'{k} {v}' for k, v in sorted(classes.items()))})" + ('' if sample is rows else f'; even sample of {len(sample)}')
        sheet(sample, a.census / 'thumbs', title).save(a.output / name, quality=72, optimize=True)
        index.append({'generator': g, 'sheet': name, 'entries': len(rows), 'shown': len(sample), 'classes': classes})
    (a.output / 'SHEETS.json').write_text(json.dumps(index, indent=1) + '\n')
    print(len(index), 'sheets')


if __name__ == '__main__':
    main()
