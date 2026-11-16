#!/usr/bin/env python3
"""Render every Gallery library entry once through the real built Gallery (WASM + canvas) and record
objective frame measures, for the provenance census.

For each entry of nativeLab.recipes (the library the Gallery ships, after nullification) this loads the
entry, holds the clock, advances to one declared time, paints, and keeps:
  - a reduced JPEG thumbnail of the actual canvas (for contact sheets);
  - measures of the actual cell frame: cells, non-blank cells, distinct glyphs, distinct foreground and
    background colours, and an FNV-1a hash of the cell bytes (duplicate detection);
  - whether the entry is in the attract rotation (nativeLab.demoRecipes).

The time is the entry's latest sampleTimesUs not after 3 s, else 2 s. One frame per entry: this is a
census for review, not motion acceptance.

Usage: render_gallery_census.py --gallery native/Nocturne-RC4-Source-Build.html --output DIR [--only id,id]
"""
from pathlib import Path
import argparse, base64, json, os, shutil, sys, time

JS_RENDER = r"""
async ([id, timeUs, thumbWidth]) => {
  const r = nativeLab.recipes.find(x => x.id === id);
  if (!r) return {error: 'missing'};
  try {
    nativeLab.load(r); nativeLab.hold(true);
    const s = nativeLab.scene;
    s.command({op:'pause', paused:false}); s.advanceTo(timeUs); s.command({op:'pause', paused:true});
    nativeLab.draw();
  } catch (e) { return {error: String(e && e.message || e)}; }
  const f = window.nativeView && window.nativeView.frame;
  const cv = document.querySelector('canvas');
  let m = null;
  if (f && f.bytes) {
    const b = f.bytes, w = new Uint32Array(b.buffer, b.byteOffset, b.byteLength >> 2);
    const n = w.length >> 2; let nonblank = 0; const glyphs = new Set(), fgs = new Set(), bgs = new Set();
    let h = 0x811c9dc5 >>> 0;
    for (let i = 0; i < b.length; i++) { h ^= b[i]; h = Math.imul(h, 0x01000193) >>> 0; }
    const bg0 = w[2];
    for (let i = 0; i < n; i++) { const g = w[4*i], fg = w[4*i+1], bg = w[4*i+2];
      if ((g !== 32 && g !== 0) || bg !== bg0) nonblank++;
      glyphs.add(g); if (g !== 32 && g !== 0) fgs.add(fg); bgs.add(bg); }
    m = {width: f.width, height: f.height, cells: n, nonblank, glyphs: glyphs.size, fg: fgs.size, bg: bgs.size, hash: h.toString(16).padStart(8,'0')};
  }
  let thumb = null;
  if (cv && cv.width) {
    const t = document.createElement('canvas'); const sc = thumbWidth / cv.width;
    t.width = thumbWidth; t.height = Math.max(1, Math.round(cv.height * sc));
    const c = t.getContext('2d'); c.imageSmoothingQuality = 'high'; c.drawImage(cv, 0, 0, t.width, t.height);
    thumb = t.toDataURL('image/jpeg', 0.82).split(',')[1];
  }
  return {m, thumb, canvas: cv ? [cv.width, cv.height] : null};
}
"""


def chromium():
    if os.environ.get('CHROMIUM'):
        return os.environ['CHROMIUM']
    found = shutil.which('chromium')
    if found:
        return found
    caches = sorted(Path.home().glob('Library/Caches/ms-playwright/chromium-*/chrome-mac*/*.app/Contents/MacOS/*'))
    return str(caches[-1]) if caches else None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--gallery', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--only', default='')
    p.add_argument('--thumb-width', type=int, default=360)
    a = p.parse_args()
    from playwright.sync_api import sync_playwright
    out = a.output; (out / 'thumbs').mkdir(parents=True, exist_ok=True)
    records = []
    started = time.time()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=chromium(), args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1800, 'height': 1300}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content(a.gallery.read_text(), timeout=600000)
        page.wait_for_function('window.nativeLab', timeout=600000)
        index = page.evaluate("""() => nativeLab.recipes.map(r => ({id: r.id, name: r.name || null,
            demonstrates: r.demonstrates || null, provenance: r.provenance || null, sourceIdentity: r.sourceIdentity || null,
            originalScene: r.originalScene || null, originalEffect: r.originalEffect || null, originalScenic: r.originalScenic || null,
            sampleTimesUs: r.sampleTimesUs || null, mode: r.mode || null,
            attract: nativeLab.demoRecipes.some(d => d.id === r.id)}))""")
        only = set(filter(None, a.only.split(',')))
        for n, row in enumerate(index):
            if only and row['id'] not in only:
                continue
            times = [t for t in (row['sampleTimesUs'] or []) if isinstance(t, (int, float)) and t <= 3_000_000]
            t = int(max(times)) if times else 2_000_000
            if t == 0:
                t = 2_000_000
            before = len(errors)
            try:
                res = page.evaluate(JS_RENDER, [row['id'], t, a.thumb_width])
            except Exception as e:  # a page crash or evaluation failure is recorded, never skipped silently
                res = {'error': 'evaluate: ' + str(e).splitlines()[0]}
            thumb = None
            if res.get('thumb'):
                thumb = f"{n:05d}.jpg"
                (out / 'thumbs' / thumb).write_bytes(base64.b64decode(res['thumb']))
            records.append({**{k: v for k, v in row.items() if k != 'sampleTimesUs'}, 'position': n, 'timeUs': t,
                            'measures': res.get('m'), 'thumb': thumb, 'error': res.get('error'),
                            'pageErrors': errors[before:]})
            if n % 250 == 0:
                print(n, len(index), round(time.time() - started), 's', flush=True)
        browser.close()
    report = {'schema': 'nocturne.gallery-census.v1', 'gallery': str(a.gallery), 'entries': len(records),
              'scope': 'One frame per Gallery library entry from the real built Gallery (WASM, canvas). A census for provenance review, not motion or artistic acceptance.',
              'records': records}
    (out / 'census.json').write_text(json.dumps(report, indent=1) + '\n')
    print('rendered', len(records), 'entries in', round(time.time() - started), 's')


if __name__ == '__main__':
    main()
