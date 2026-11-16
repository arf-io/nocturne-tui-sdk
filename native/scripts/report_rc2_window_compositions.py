#!/usr/bin/env python3
"""Build a self-contained cell comparison report from RC2 composition captures."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, NoReturn


EXPECTED_SAMPLES = 96
REQUIRED_FIELDS = {"id", "timeUs", "width", "height", "original", "native", "baseline"}
UINT32_MAX = (1 << 32) - 1


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def _is_u32_list(value: Any, expected_length: int, *, field: str, path: Path) -> bool:
    if not isinstance(value, list) or len(value) != expected_length:
        fail(f"{path}: {field} must contain exactly {expected_length} unsigned 32-bit words")
    if any(type(word) is not int or word < 0 or word > UINT32_MAX for word in value):
        fail(f"{path}: {field} contains a value outside the unsigned 32-bit range")
    return True


def load_captures(directory: Path) -> list[dict[str, Any]]:
    if not directory.is_dir():
        fail(f"capture directory does not exist: {directory}")
    paths = sorted(path for path in directory.rglob("*.json") if path.is_file())
    if len(paths) != EXPECTED_SAMPLES:
        fail(f"expected exactly {EXPECTED_SAMPLES} JSON samples in {directory}, found {len(paths)}")

    records = []
    for path in paths:
        raw_bytes = path.read_bytes()
        try:
            raw = raw_bytes.decode("utf-8")
            record = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            fail(f"{path}: invalid UTF-8 JSON: {error}")
        if not isinstance(record, dict):
            fail(f"{path}: capture must be a JSON object")
        missing = REQUIRED_FIELDS - record.keys()
        if missing:
            fail(f"{path}: missing required fields: {', '.join(sorted(missing))}")
        sample_id = record["id"]
        if not isinstance(sample_id, (str, int)) or isinstance(sample_id, bool) or sample_id == "":
            fail(f"{path}: id must be a nonempty string or integer")
        time_us = record["timeUs"]
        if type(time_us) is not int or time_us < 0:
            fail(f"{path}: timeUs must be a nonnegative integer")
        width, height = record["width"], record["height"]
        if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
            fail(f"{path}: width and height must be positive integers")
        if width > sys.maxsize // height // 4:
            fail(f"{path}: cell-buffer dimensions overflow host addressable size")
        words = width * height * 4
        for field in ("original", "native", "baseline"):
            _is_u32_list(record[field], words, field=field, path=path)
        records.append({
            "name": path.relative_to(directory).as_posix(),
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "raw": raw,
            "id": sample_id,
            "timeUs": time_us,
            "width": width,
            "height": height,
        })
    return records


def _script_json(value: Any) -> str:
    # Escaping `<` keeps untrusted capture text from terminating the data script.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def build_report(records: list[dict[str, Any]], gallery_url: str) -> str:
    entries = []
    for index, record in enumerate(records):
        entries.append({
            "index": index,
            "name": record["name"],
            "sha256": record["sha256"],
            "raw": record["raw"],
            "id": record["id"],
            "timeUs": record["timeUs"],
            "width": record["width"],
            "height": record["height"],
        })
    gallery_json = _script_json(gallery_url)
    captures_json = _script_json(entries)
    return f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nocturne · RC2 window compositions</title>
<style>
:root{{color-scheme:dark;background:#11161d;color:#e6e3db;font:16px/1.55 system-ui,sans-serif}}
*{{box-sizing:border-box}}body{{margin:0}}main{{max-width:1600px;margin:auto;padding:32px clamp(16px,3vw,48px)}}
a{{color:#a7d9e3}}h1{{font-size:clamp(26px,3vw,42px);line-height:1.2;margin:.4em 0}}h2{{font-size:20px;margin-top:2em}}
p{{max-width:95ch}}.kicker{{text-transform:uppercase;letter-spacing:.1em;font-size:12px;color:#9bb9c2}}
.subtle{{color:#b1bac6}}code{{font-size:.9em;overflow-wrap:anywhere}}.toolbar{{display:flex;align-items:center;flex-wrap:wrap;gap:12px;margin:24px 0 12px}}
select,button{{font:inherit;color:inherit;background:#202b37;border:1px solid #526376;border-radius:5px;padding:9px 12px}}
button,a{{cursor:pointer}}button:focus-visible,select:focus-visible,a:focus-visible{{outline:3px solid #b8e5eb;outline-offset:3px}}
.status{{background:#1b3430;border:1px solid #456d61;color:#c0ead2;padding:6px 12px;border-radius:4px}}
.frames{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}figure{{margin:0;min-width:0;border:1px solid #41505e;background:#151d26;border-radius:6px;overflow:hidden}}
figcaption{{padding:10px 14px;border-bottom:1px solid #41505e;font-size:14px}}canvas{{width:100%;height:auto;display:block;background:#112233}}
#case-info{{font-size:14px;white-space:pre-wrap;overflow-wrap:anywhere}}details{{border-top:1px solid #41505e;margin-top:24px;padding-top:15px}}summary{{cursor:pointer;font-weight:600}}
footer{{border-top:1px solid #37424f;margin-top:28px;padding-top:18px;font-size:13px;color:#b1bac6}}
table{{border-collapse:collapse;font-size:13px;width:100%;margin-top:12px}}th,td{{text-align:left;vertical-align:top;padding:5px 8px;border-bottom:1px solid #37424f}}td code{{font-size:12px}}
@media(max-width:760px){{.frames{{grid-template-columns:1fr}}main{{padding-top:20px}}select{{max-width:100%}}}}
</style>
<main><div class="kicker">Nocturne source restoration · RC2 window compositions</div>
<h1>Original JavaScript → current native C</h1>
<p>These 96 captured samples compare the original RC2 window-body compositor with the current native compositor. Each pair uses the same SDK background cells. Select a scene and sample time to inspect exact cell words, changed cells, and the source capture hash.</p>
<div class="toolbar"><label for="sample">Case / sample</label><select id="sample" aria-label="Select one of 96 case samples"></select>
<span class="status" id="match" role="status" aria-live="polite"></span><button id="download" type="button">Download selected raw JSON</button>
<a id="gallery" href="#">Open in live gallery</a></div>
<div class="frames"><figure><figcaption>Original RC2 JavaScript</figcaption><canvas id="original" aria-label="Original compositor cell buffer"></canvas></figure>
<figure><figcaption>Current native C</figcaption><canvas id="native" aria-label="Native compositor cell buffer"></canvas></figure>
<figure><figcaption>Exact diff · highlighted cells differ in any of four cell words</figcaption><canvas id="diff" aria-label="Cell-level difference map"></canvas></figure></div>
<p id="case-info" class="subtle"></p>
<p class="subtle">Braille masks and full/half blocks use explicit cell geometry; other glyphs use the browser monospace font. This viewer paints captured cell data, not screenshots or a live SDK session.</p>
<details><summary>Shared SDK background baseline</summary><p class="subtle">This is the caller-provided baseline used by both body compositor captures.</p>
<figure><figcaption>Same SDK background · baseline buffer</figcaption><canvas id="baseline" aria-label="Shared SDK background baseline"></canvas></figure></details>
<details><summary>SHA-256 of captured JSON source data (96 files)</summary><p>Each digest covers the exact UTF-8 JSON file bytes supplied to this generator.</p>
<table><thead><tr><th>Sample</th><th>SHA-256</th></tr></thead><tbody id="hashes"></tbody></table></details>
<h2>Comparison scope</h2>
<p>This report compares the generated window body compositor over an identical caller-owned SDK background. It does not compare the full original window chrome, and it does not claim coverage of the complete historical component inventory. Cell equality is exact across glyph, foreground RGB, background RGB, and hit ID; no color tolerance is applied.</p>
<p>The live gallery opens the selected recipe at the captured scene time. <a href="SUMMARY.json">Build identity and check results</a> · <a href="raw-evidence.json">Execution logs</a></p>
<footer>Generated as a standalone HTML artifact from the selected capture directory. The selected JSON download preserves the original capture text.</footer></main>
<script type="application/json" id="capture-index">{captures_json}</script>
<script>
const entries=JSON.parse(document.querySelector('#capture-index').textContent), galleryBase={gallery_json};
const selector=document.querySelector('#sample'), hashes=document.querySelector('#hashes');
const rgb=n=>'#'+(n>>>0).toString(16).padStart(6,'0');
function decode(entry){{return JSON.parse(entry.raw)}}
function paintBraille(ctx,g,x,y,w,h){{if(!Number.isInteger(g)||g<0x2800||g>0x28ff)return false;const mask=g-0x2800,dots=[[.2,.1],[.2,.3],[.2,.55],[.7,.1],[.7,.3],[.7,.55],[.2,.8],[.7,.8]];for(let bit=0;bit<8;bit++)if(mask&(1<<bit)){{const[c,r]=dots[bit];ctx.fillRect(x+c*w,y+r*h,w*.2,h*.1)}}return true}}
function paintBlock(ctx,g,x,y,w,h){{switch(g){{case 0x2588:ctx.fillRect(x,y,w,h);return true;case 0x2580:ctx.fillRect(x,y,w,h/2);return true;case 0x2584:ctx.fillRect(x,y+h/2,w,h/2);return true;case 0x258c:ctx.fillRect(x,y,w/2,h);return true;case 0x2590:ctx.fillRect(x+w/2,y,w/2,h);return true;default:return false}}}}
function prepareCanvas(id,d){{const c=document.getElementById(id),cw=9,ch=16;c.width=d.width*cw;c.height=d.height*ch;const ctx=c.getContext('2d');ctx.font='14px monospace';ctx.textBaseline='top';return{{ctx,cw,ch}}}}
function paint(id,words,d){{const{{ctx,cw,ch}}=prepareCanvas(id,d);for(let y=0;y<d.height;y++)for(let x=0;x<d.width;x++){{const i=(y*d.width+x)*4,g=words[i],px=x*cw,py=y*ch;ctx.fillStyle=rgb(words[i+2]);ctx.fillRect(px,py,cw,ch);ctx.fillStyle=rgb(words[i+1]);if(!paintBraille(ctx,g,px,py,cw,ch)&&!paintBlock(ctx,g,px,py,cw,ch)&&g>32)ctx.fillText(String.fromCodePoint(g),px,py,cw)}}}}
function paintDiff(original,native,d){{const{{ctx,cw,ch}}=prepareCanvas('diff',d);let changedCells=0,changedWords=0;for(let y=0;y<d.height;y++)for(let x=0;x<d.width;x++){{const i=(y*d.width+x)*4,cellDiff=original[i]!==native[i]||original[i+1]!==native[i+1]||original[i+2]!==native[i+2]||original[i+3]!==native[i+3];if(!cellDiff){{ctx.fillStyle=rgb(original[i+2]);ctx.fillRect(x*cw,y*ch,cw,ch);continue}}changedCells++;for(let j=0;j<4;j++)if(original[i+j]!==native[i+j])changedWords++;const px=x*cw,py=y*ch,g=native[i];ctx.fillStyle='#8f3150';ctx.fillRect(px,py,cw,ch);ctx.strokeStyle='#f2adc2';ctx.lineWidth=1;ctx.strokeRect(px+.5,py+.5,cw-1,ch-1);ctx.fillStyle='#fff1f5';if(!paintBraille(ctx,g,px,py,cw,ch)&&!paintBlock(ctx,g,px,py,cw,ch)&&g>32)ctx.fillText(String.fromCodePoint(g),px,py,cw)}}return{{changedCells,changedWords}}}}
function show(){{const entry=entries[Number(selector.value)],d=decode(entry);paint('original',d.original,d);paint('native',d.native,d);paint('baseline',d.baseline,d);const diff=paintDiff(d.original,d.native,d);document.querySelector('#match').textContent=diff.changedCells+' differing cells · '+diff.changedWords+' / '+d.original.length+' words';const info={{id:d.id,timeUs:d.timeUs,width:d.width,height:d.height,source:entry.name,sha256:entry.sha256}};document.querySelector('#case-info').textContent=JSON.stringify(info,null,2);const link=document.querySelector('#gallery');link.href=galleryBase+'#scene='+encodeURIComponent(String(d.id))+'&timeUs='+d.timeUs;document.documentElement.dataset.ready='true';document.documentElement.dataset.differingCells=String(diff.changedCells)}}
entries.forEach((entry,index)=>{{const d=decode(entry),option=new Option(String(index+1).padStart(2,'0')+' · '+d.id+' · '+d.timeUs+' µs',String(index));selector.add(option);const row=document.createElement('tr'),name=document.createElement('td'),digest=document.createElement('td'),code=document.createElement('code');name.textContent=String(index+1).padStart(2,'0')+' · '+d.id+' · '+d.timeUs+' µs';code.textContent=entry.sha256;digest.append(code);row.append(name,digest);hashes.append(row)}});
selector.addEventListener('change',show);document.querySelector('#download').addEventListener('click',()=>{{const entry=entries[Number(selector.value)],url=URL.createObjectURL(new Blob([entry.raw],{{type:'application/json;charset=utf-8'}})),link=document.createElement('a');link.href=url;link.download=entry.name.split('/').pop();link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}});show();
</script></html>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures", required=True, type=Path, help="directory containing the 96 JSON capture samples")
    parser.add_argument("--output", required=True, type=Path, help="HTML report output path")
    parser.add_argument("--gallery-url", default="gallery.html", help="relative/absolute live gallery URL (default: gallery.html)")
    args = parser.parse_args()
    try:
        records = load_captures(args.captures)
        report = build_report(records, args.gallery_url)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8", newline="\n")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"wrote {args.output} with {len(records)} exact capture hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
