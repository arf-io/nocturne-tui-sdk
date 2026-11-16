#!/usr/bin/env python3
"""Run real 5-second per-scene benchmark at 160x48 comparing Canvas2D vs WebGL paint."""

import os
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
GALLERY_HTML = ROOT / 'Nocturne-RC4-Source-Build.html'

TOP_10_HEAVY_SCENES = [
    ('pearl-observatory-bbs-config', 'Observatory BBS Config (Text Dense)'),
    ('pearl-observatory-scope', 'Observatory Scope (Dense Text)'),
    ('source-modal-drawer-right-application', 'Modal Drawer Right (Layered Windows)'),
    ('pearl-observatory-tmux', 'Observatory tmux (Terminal Multiplexer)'),
    ('rc2-window-drawer-top-application', 'Window Drawer Top (Window Animation)'),
    ('original-copper-causeway', 'Copper Causeway (Scenic Diorama)'),
    ('pearl-observatory-pico', 'Observatory pico (Full-Screen Editor)'),
    ('rc2-window-orbital-bloom-application', 'Window Orbital Bloom (Modal Geometry)'),
    ('pearl-fleet-original', 'Fleet Workspace (Multi-Agent Windows)'),
    ('autumn', 'Autumn Drift (Subcell Braille Weather)'),
]


def run_benchmark():
    print(f'Starting real 5-second benchmark on 10 heaviest admitted scenes at 160x48...')
    print(f'Gallery HTML: {GALLERY_HTML}')
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=os.environ.get('CHROMIUM')
        )
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.goto(GALLERY_HTML.as_uri())
        page.wait_for_function('window.nativeLab')
        page.evaluate('nativeLab.hold()')
        
        results = []
        frames_per_scene = 300 # 5 seconds at 60fps (300 frames * 16666 us = 5,000,000 us)
        
        for scene_id, scene_name in TOP_10_HEAVY_SCENES:
            print(f'Benchmarking: {scene_id} ({scene_name})...')
            
            res = page.evaluate('''async ({ id, frames }) => {
                const r = nativeLab.recipes.find(x => x.id === id);
                if (!r) throw new Error("Recipe not found: " + id);
                
                // --- 1. Canvas2D Measurement ---
                nativeLab.load(r);
                nativeLab.hold();
                document.getElementById('columns').value = '160';
                document.getElementById('rows').value = '48';
                document.getElementById('resize').click();
                nativeLab.setPaintMode('canvas2d');
                
                // Warm up 30 frames
                for (let i = 0; i < 30; i++) {
                    nativeLab.advance(16666);
                    nativeLab.draw();
                }
                
                let r2dSum = 0, p2dSum = 0;
                for (let i = 0; i < frames; i++) {
                    nativeLab.advance(16666);
                    nativeLab.draw();
                    const p = nativeLab.perf();
                    r2dSum += p.renderMs;
                    p2dSum += p.paintMs;
                }
                
                // --- 2. WebGL Measurement ---
                nativeLab.load(r);
                nativeLab.hold();
                document.getElementById('columns').value = '160';
                document.getElementById('rows').value = '48';
                document.getElementById('resize').click();
                nativeLab.setPaintMode('webgl');
                
                // Warm up 30 frames
                for (let i = 0; i < 30; i++) {
                    nativeLab.advance(16666);
                    nativeLab.draw();
                }
                
                let rglSum = 0, pglSum = 0;
                for (let i = 0; i < frames; i++) {
                    nativeLab.advance(16666);
                    nativeLab.draw();
                    const p = nativeLab.perf();
                    rglSum += p.renderMs;
                    pglSum += p.paintMs;
                }
                
                return {
                    id: id,
                    canvas2d: {
                        renderMs: r2dSum / frames,
                        paintMs: p2dSum / frames,
                        totalMs: (r2dSum + p2dSum) / frames,
                        fps: 1000.0 / ((r2dSum + p2dSum) / frames)
                    },
                    webgl: {
                        renderMs: rglSum / frames,
                        paintMs: pglSum / frames,
                        totalMs: (rglSum + pglSum) / frames,
                        fps: 1000.0 / ((rglSum + pglSum) / frames)
                    }
                };
            }''', {'id': scene_id, 'frames': frames_per_scene})
            
            p2d = res['canvas2d']['paintMs']
            pgl = res['webgl']['paintMs']
            t2d = res['canvas2d']['totalMs']
            tgl = res['webgl']['totalMs']
            res['paintSpeedup'] = p2d / pgl if pgl > 0 else 0
            res['totalSpeedup'] = t2d / tgl if tgl > 0 else 0
            res['name'] = scene_name
            results.append(res)
            
            print(f"  Canvas2D: Render {res['canvas2d']['renderMs']:5.2f} ms | Paint {p2d:5.2f} ms | Total {t2d:5.2f} ms ({res['canvas2d']['fps']:4.1f} FPS)")
            print(f"  WebGL:    Render {res['webgl']['renderMs']:5.2f} ms | Paint {pgl:5.2f} ms | Total {tgl:5.2f} ms ({res['webgl']['fps']:4.1f} FPS)")
            print(f"  Paint Speedup: {res['paintSpeedup']:5.1f}x | Total Speedup: {res['totalSpeedup']:4.2f}x\n")
            
        browser.close()
        
    print('\n========================================================================================================================')
    print('                      NOCTURNE GALLERY v1.0.0 PAINT BENCHMARK (160x48, 5.0s per scene, 300 frames)')
    print('========================================================================================================================')
    print(f"{'Scene ID':<38} | {'Canvas2D (ms)':^22} | {'WebGL (ms)':^22} | {'Speedup':^16}")
    print(f"{'':<38} | {'Render':>6} {'Paint':>7} {'Total':>7} | {'Render':>6} {'Paint':>7} {'Total':>7} | {'Paint':>7} {'Total':>7}")
    print('-'*110)
    
    avg_p2d = sum(r['canvas2d']['paintMs'] for r in results) / len(results)
    avg_r2d = sum(r['canvas2d']['renderMs'] for r in results) / len(results)
    avg_t2d = sum(r['canvas2d']['totalMs'] for r in results) / len(results)
    
    avg_pgl = sum(r['webgl']['paintMs'] for r in results) / len(results)
    avg_rgl = sum(r['webgl']['renderMs'] for r in results) / len(results)
    avg_tgl = sum(r['webgl']['totalMs'] for r in results) / len(results)
    
    for r in results:
        c2 = r['canvas2d']
        gl = r['webgl']
        print(f"{r['id']:<38} | {c2['renderMs']:6.2f} {c2['paintMs']:7.2f} {c2['totalMs']:7.2f} | {gl['renderMs']:6.2f} {gl['paintMs']:7.2f} {gl['totalMs']:7.2f} | {r['paintSpeedup']:6.1f}x {r['totalSpeedup']:6.2f}x")
        
    print('-'*110)
    print(f"{'MEAN AVERAGE':<38} | {avg_r2d:6.2f} {avg_p2d:7.2f} {avg_t2d:7.2f} | {avg_rgl:6.2f} {avg_pgl:7.2f} {avg_tgl:7.2f} | {avg_p2d/avg_pgl:6.1f}x {avg_t2d/avg_tgl:6.2f}x")
    print('========================================================================================================================\n')
    
    # Save JSON summary
    out_json = ROOT / 'tests/webgl_paint_benchmark_results.json'
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'Benchmark results saved to {out_json}')


if __name__ == '__main__':
    run_benchmark()
