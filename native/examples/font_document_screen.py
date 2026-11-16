"""Eight real native application screens using an explicit-font reusable view."""
import argparse,hashlib,html,json,sys
from pathlib import Path
from contextlib import ExitStack
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hosts/python'));sys.path.insert(0,str(ROOT/'bindings/python'))
sys.path.insert(0,str(ROOT/'examples'))
from nocturne_native import NativeScene
from font_shaper import HarfBuzzFont
from font_document_view import FontDocumentView
from screen_backdrop import world,application

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['library','font','output','evidence']:parser.add_argument('--'+name,required=True)
    args=parser.parse_args();reports=[];panels=[]
    with ExitStack() as stack:
        font=stack.enter_context(HarfBuzzFont(Path(args.font).read_bytes(),args.library))
        view=FontDocumentView([font],language={'Latn':'en','Arab':'ar','*':'und'})
        for context in ['isolated','application']:
            for index,(alignment,alpha,size) in enumerate([
                ('left',1,32),('center',.7,32),('right',.4,32),('left',1,64)]):
                scene=stack.enter_context(NativeScene())
                for command in world()+(application() if context=='application' else []):scene.command(command)
                text='Nocturne office é\nسلام\nContextual text in an application'
                scene.command({'op':'draft','text':text,'emitWeather':False})
                before=scene.snapshot()
                presentation=view.present(scene,host_epoch=1,width=640,height=300,
                    alignment=alignment,alpha=alpha,font_size=size)
                assert scene.snapshot()==before
                reference=next(s for s in presentation.layout.segments if 'سلام' in s.run.source)
                joined=font.shape(reference.run.source,direction='rtl',script='Arab',language='ar')
                assert reference.run.glyphs==joined.glyphs
                start=next(e for e in presentation.edges if e.offset==0)
                assert view.select_at(scene,presentation,start.x,start.baseline,host_epoch=1)
                end=max(presentation.edges,key=lambda e:e.offset)
                assert view.select_at(scene,presentation,end.x,end.baseline,host_epoch=1,extend=True)
                selected=view.present(scene,host_epoch=1,width=640,height=300,
                    alignment=alignment,alpha=alpha,font_size=size)
                assert scene.selected_text()==text
                frame=scene.render();base=[];words=frame.words()
                if context=='application':
                    for y in range(frame.height):
                        for x in range(frame.width):
                            glyph,foreground,background,owner=words[y*frame.width+x]
                            base.append(f'<rect x="{x*5}" y="{y*10}" width="5" height="10" fill="#{background:06x}"/>')
                            if glyph>32 and glyph<=0x10ffff:
                                base.append(f'<text x="{x*5}" y="{y*10+9}" font-size="9" fill="#{foreground:06x}">{html.escape(chr(glyph))}</text>')
                svg=selected.svg.replace('<svg ','<svg data-font-document="true" ',1)
                screen='<svg xmlns="http://www.w3.org/2000/svg" width="640" height="420" viewBox="0 0 640 420">'+''.join(base)+'<rect x="0" y="0" width="640" height="300" fill="#0b121b" opacity=".86"/>'+svg+'</svg>'
                identity=f'font-document-{context}-{index}'
                panels.append(f'<article id="{identity}"><h2>{context} · {alignment} · alpha {alpha} · size {size}</h2>{screen}</article>')
                reports.append({'id':identity,'source':text,'fontSha256':font.font_sha256,
                    'engineVersion':font.engine_version,'alignment':alignment,'alpha':alpha,
                    'fontSize':size,'lineEnds':selected.layout.line_ends,
                    'edges':[asdict(e) for e in selected.edges],
                    'snapshotSha256':hashlib.sha256(scene.snapshot()).hexdigest(),
                    'frameSha256':hashlib.sha256(frame.bytes).hexdigest(),
                    'nativeSelection':scene.selected_text(),'passed':True})
    document='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Nocturne contextual font document view</title><style>body{background:#111923;color:#e4dacc;font:16px system-ui;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(640px,1fr));gap:24px}article{overflow:auto}h2{font-size:18px}</style><h1>Nocturne: reusable contextual font view</h1><p>Actual native scene, source selection, HarfBuzz outlines and caller font provenance. Each panel varies alignment, alpha or wrapping size. Generated font outlines are presentation evidence; font files are not included.</p><main>'+''.join(panels)+'</main></html>'
    Path(args.output).write_text(document)
    Path(args.evidence).write_text(json.dumps({'cases':reports,'passed':True},indent=2)+'\n')

if __name__=='__main__':main()
