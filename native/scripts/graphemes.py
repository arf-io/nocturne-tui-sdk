#!/usr/bin/env python3
"""Owned Python binding runner, no host segmentation substitute."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene
with NativeScene() as scene:
    for index,line in enumerate(sys.stdin):
        text=json.loads(line)['text'];print(json.dumps({'index':index,'boundaries':scene.grapheme_boundaries(text),'widths1':scene.grapheme_widths(text,1),'widths2':scene.grapheme_widths(text,2),'layouts':[scene.grapheme_layout(text,columns,policy) for columns in (1,3,8) for policy in (1,2)]}))
