"""AFD augmentation seam, not an assumed API inside an inaccessible AFD checkout.

Call renderStatus(timeMs, paletteId, width, title) from AFD's existing scheduler.
The function returns tmux styled text; it does not set options, spawn a daemon,
read a clock, or supersede any AFD component. Actual AFD plugin wiring is pending.
"""
from pathlib import Path
import json,sys,unicodedata
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from studio import Studio,Node
ROOT=Path(__file__).resolve().parents[1]
PALETTES={p['id']:p for p in json.loads((ROOT/'palettes.json').read_text())['palettes']}

def escapeTmux(text):
    """Escape literal format/strftime metacharacters and discard all control codes."""
    return ''.join(c for c in text if not unicodedata.category(c).startswith('C')).replace('#','##').replace('%','%%')

def renderStatus(timeMs,paletteId='smart-dark',width=48,title='NOCTURNE  /  AFD'):
    """Return a deterministic single-row tmux format string, not ANSI sequences.

    width 1..160 cells. Title is inert text. Example: renderStatus(1200,'copper').
    Raises KeyError for unknown palette, ValueError for dimensions/config.
    """
    if type(width)is not int or not 1<=width<=160:raise ValueError('status width 1..160')
    palette=PALETTES[paletteId]
    s=Studio(width=width,height=1,pattern=3,brightness=260,stars=1,starDensity=160,pixelMode=0,palette=palette['colors'],baseColor=palette['background'],novaChance=0)
    f=s.render(timeMs,nodes=[Node('text',1,0,max(0,width-2),1,text=escapeTmux(title).replace('##','#').replace('%%','%')[:width-2],colorAnimation=2,hueSpeed=30)])
    return ''.join(f'#[fg=#{c.fg:06x},bg=#{c.bg:06x}]'+escapeTmux(chr(c.glyph)) for c in f.cells)+'#[default]'
