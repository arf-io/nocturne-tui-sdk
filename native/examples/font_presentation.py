"""Explicit-font mixed-direction SVG example; no bundled fonts or discovery.

Run with --library /path/to/libharfbuzz --font /path/to/font.ttf --output screen.svg.
The font must cover Latin and Arabic. Optional --select START END paints logical
ink selection; --alpha controls glyph opacity. Native source stays authoritative.
"""
import argparse,json
from dataclasses import asdict
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hosts/python'));sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from font_shaper import HarfBuzzFont,shape_scene_with_fallback,shape_scene_automatic
from font_svg import shaped_paragraph_svg

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',required=True);parser.add_argument('--font',required=True)
    parser.add_argument('--fallback-font',action='append',default=[])
    parser.add_argument('--automatic-scripts',action='store_true',help='Use native Unicode script itemization with explicit English/Arabic language mapping')
    parser.add_argument('--wrap-width',type=float,help='Wrap whole graphemes using shaped pixel advances at font size 36')
    parser.add_argument('--break-opportunities',type=int,nargs='*',help='Explicit preferred scalar boundaries for wrapped lines')
    parser.add_argument('--break-policy',choices=['grapheme','unicode'],default='grapheme')
    parser.add_argument('--overflow-policy',choices=['grapheme','overflow'],default='grapheme')
    parser.add_argument('--alignment',choices=['left','center','right'],default='left')
    parser.add_argument('--content-width',type=float,default=944)
    parser.add_argument('--width',type=float,default=960);parser.add_argument('--height',type=float,default=280)
    parser.add_argument('--font-size',type=float,default=36);parser.add_argument('--line-height',type=float,default=64)
    parser.add_argument('--foreground',default='#e4dacc')
    parser.add_argument('--geometry-output',type=Path,help='Write owned clipped ink and source-edge geometry as JSON')
    parser.add_argument('--hit',type=float,nargs=2,help='Include viewport-gated ink and nearest-source hits in geometry JSON')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--select',type=int,nargs=2);parser.add_argument('--alpha',type=float,default=1)
    args=parser.parse_args()
    if args.hit is not None and args.geometry_output is None:parser.error('--hit requires --geometry-output')
    if args.break_opportunities is not None and args.wrap_width is None:parser.error('--break-opportunities requires --wrap-width')
    if args.break_policy=='unicode' and args.wrap_width is None:parser.error('--break-policy unicode requires --wrap-width')
    if args.break_policy=='unicode' and args.break_opportunities is not None:parser.error('Unicode policy cannot combine with explicit opportunities')
    if args.overflow_policy=='overflow' and (args.wrap_width is None or (args.break_policy!='unicode' and args.break_opportunities is None)):parser.error('Intact overflow requires wrapping with Unicode or explicit opportunities')
    from contextlib import ExitStack
    with ExitStack() as stack:
        fonts=[stack.enter_context(HarfBuzzFont(Path(path).read_bytes(),args.library)) for path in [args.font,*args.fallback_font]]
        scene=stack.enter_context(NativeScene())
        source='Nocturne office é\nسلام\nLayered text presentation'
        scene.command(dict(op='draft',text=source,emitWeather=False));before=scene.snapshot()
        arabic=source.index('سلام');arabic_end=arabic+len('سلام')
        spans=[dict(start=0,end=arabic,fonts=fonts,script='Latn',language='en'),dict(start=arabic,end=arabic_end,fonts=fonts,script='Arab',language='ar'),dict(start=arabic_end,end=len(source),fonts=fonts,script='Latn',language='en')]
        layout=None
        if args.wrap_width is not None:
            from font_layout import shape_wrapped_paragraph
            layout=shape_wrapped_paragraph(scene,0,0,fonts,width=args.wrap_width,font_size=args.font_size,language={'Latn':'en','Arab':'ar','*':'und'},break_opportunities=args.break_opportunities,break_policy=args.break_policy,overflow_policy=args.overflow_policy)
            segments=layout.segments
        else:
            segments=(shape_scene_automatic(scene,0,0,fonts,language={'Latn':'en','Arab':'ar','*':'und'})
                      if args.automatic_scripts else shape_scene_with_fallback(scene,0,0,spans))
        placement=dict(font_size=args.font_size,line_height=args.line_height,alignment=args.alignment,content_width=args.content_width)
        svg=shaped_paragraph_svg(fonts,segments,width=args.width,height=args.height,alpha=args.alpha,selection=args.select,foreground=args.foreground,**placement)
        if args.geometry_output is not None:
            from font_layout import paragraph_ink_regions,paragraph_source_edges,clip_ink_regions,hit_ink_region,hit_source_edge
            viewport=(0,0,args.width,args.height)
            regions=clip_ink_regions(paragraph_ink_regions(fonts,segments,**placement),viewport)
            edges=paragraph_source_edges(segments,**placement)
            report=dict(schema='nocturne.font-example-geometry.v1',source=source,viewport=viewport,placement=placement,ink=[asdict(r) for r in regions],edges=[asdict(e) for e in edges],fonts=[dict(sha256=f.font_sha256,faceIndex=f.face_index,engineVersion=f.engine_version) for f in fonts])
            if layout is not None:report['wrapping']=dict(lineEnds=layout.line_ends,lineWidths=layout.line_widths,overflowLines=layout.overflow_lines,breakOpportunities=args.break_opportunities,breakPolicy=args.break_policy,overflowPolicy=args.overflow_policy)
            if args.hit is not None:
                ink=hit_ink_region(regions,*args.hit,viewport=viewport);edge=hit_source_edge(edges,*args.hit,viewport=viewport)
                report['hit']=dict(point=args.hit,ink=asdict(ink) if ink else None,edge=asdict(edge) if edge else None)
            args.geometry_output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8')
        if scene.snapshot()!=before:raise RuntimeError('Presentation modified native scene')
        args.output.write_text(svg,encoding='utf-8')

if __name__=='__main__':main()
