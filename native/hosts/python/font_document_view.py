"""Explicit-font application view over canonical native text and identities.

Hosts serialize presentation and interaction against their scene mutations and
increment host_epoch before resetting or replacing a native context. Fonts remain
caller-owned; this component does not discover, install or close them.
"""
from dataclasses import dataclass
import math
import xml.etree.ElementTree as E
from font_shaper import HarfBuzzFont
from font_layout import (capture_text_run,text_run_capture_current,
    shape_wrapped_paragraph,paragraph_source_edges,paragraph_ink_regions,
    clip_ink_regions,hit_source_edge)
from font_svg import shaped_paragraph_svg


@dataclass(frozen=True)
class FontDocumentPresentation:
    view:object
    capture:object
    layout:object
    edges:tuple
    ink:tuple
    viewport:tuple
    svg:str
    caret:object


class FontDocumentView:
    def __init__(self,fonts,*,language,features=()):
        self.fonts=tuple(fonts)
        if not 1<=len(self.fonts)<=32 or any(not isinstance(f,HarfBuzzFont) for f in self.fonts):
            raise ValueError('Explicit ordered HarfBuzz font pool required')
        self.language=dict(language) if isinstance(language,dict) else language
        self.features=tuple(features)

    def present(self,scene,*,kind=0,id=0,host_epoch,width=640,height=240,
                font_size=32,x=8,baseline=48,line_height=48,
                alignment='left',alpha=1):
        values=(width,height,font_size,x,baseline,line_height,alpha)
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):
            raise ValueError('Finite font document geometry required')
        if min(width,height,font_size,line_height)<=0 or x<0 or width<=2*x or not 0<=alpha<=1:
            raise ValueError('Invalid font document dimensions or alpha')
        if alignment not in ('left','center','right'):raise ValueError('Invalid alignment')
        capture=capture_text_run(scene,kind,id,host_epoch=host_epoch)
        layout=shape_wrapped_paragraph(scene,kind,id,self.fonts,width=width-2*x,
            font_size=font_size,language=self.language,features=self.features,
            break_policy='unicode')
        placement=dict(font_size=font_size,x=x,baseline=baseline,
                       line_height=line_height,alignment=alignment,content_width=width-2*x)
        boundaries=set(scene.grapheme_boundaries(capture.source))
        edges=tuple(edge for edge in paragraph_source_edges(layout.segments,**placement)
                    if edge.offset in boundaries)
        viewport=(0,0,width,height)
        ink=clip_ink_regions(paragraph_ink_regions(self.fonts,layout.segments,**placement),viewport)
        info=scene.info_complete()
        prompt=info['prompt'] if kind==0 and id==0 and info.get('inputOwner')=='prompt' else None
        selection=None
        if prompt and prompt['anchor']>=0:
            selection=tuple(sorted((prompt['anchor'],prompt['caret'])))
        svg=shaped_paragraph_svg(self.fonts,layout.segments,width=width,height=height,
            alpha=alpha,selection=selection,**placement)
        caret=None
        if prompt:
            candidates=[edge for edge in edges if edge.offset==prompt['caret']]
            edge=next((edge for edge in candidates if edge.affinity=='upstream'),
                      candidates[0] if candidates else None)
            if edge:caret=(edge.offset,edge.line,edge.x,edge.baseline)
            elif not capture.source:caret=(0,0,x,baseline)
        if caret and 0<=caret[2]<width and 0<=caret[3]<height:
            root=E.fromstring(svg);ns='{http://www.w3.org/2000/svg}'
            E.SubElement(root,ns+'rect',{'data-caret':str(caret[0]),'x':format(caret[2],'.9g'),
                'y':format(caret[3]-font_size,'.9g'),'width':'1',
                'height':format(font_size,'.9g'),'fill':'#e4dacc','opacity':format(alpha,'.9g')})
            svg=E.tostring(root,encoding='unicode')
        if not text_run_capture_current(scene,capture,host_epoch=host_epoch):
            raise RuntimeError('Source changed during font document presentation')
        return FontDocumentPresentation(self,capture,layout,edges,tuple(ink),viewport,svg,caret)

    def _prompt(self,scene,presentation,host_epoch):
        if not isinstance(presentation,FontDocumentPresentation) or presentation.view is not self:
            return None
        capture=presentation.capture
        if capture.kind!=0 or capture.id!=0 or not text_run_capture_current(scene,capture,host_epoch=host_epoch):
            return None
        info=scene.info_complete()
        return info['prompt'] if info.get('inputOwner')=='prompt' else None

    @staticmethod
    def _select(scene,prompt,offset,extend):
        anchor=(prompt['anchor'] if prompt['anchor']>=0 else prompt['caret']) if extend else offset
        boundaries=scene.grapheme_boundaries(scene.text_run_source(0,0))
        anchor=max(b for b in boundaries if b<=anchor)
        scene.command({'op':'select','anchor':anchor,'caret':offset,'unit':'grapheme'})
        return True

    def select_at(self,scene,presentation,x,y,*,host_epoch,extend=False):
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (x,y)):
            raise ValueError('Finite pointer coordinates required')
        prompt=self._prompt(scene,presentation,host_epoch)
        if prompt is None:return False
        left,top,right,bottom=presentation.viewport
        if not left<=x<right or not top<=y<bottom:return False
        if not presentation.capture.source:return self._select(scene,prompt,0,extend)
        edge=hit_source_edge(presentation.edges,x,y,viewport=presentation.viewport)
        return self._select(scene,prompt,edge.offset,extend) if edge else False

    def move(self,scene,presentation,key,*,host_epoch,extend=False):
        if key not in ('ArrowUp','ArrowDown','Home','End'):return False
        prompt=self._prompt(scene,presentation,host_epoch)
        if prompt is None:return False
        candidates=[edge for edge in presentation.edges if edge.offset==prompt['caret']]
        if not candidates:return False
        current=next((e for e in candidates if e.affinity=='upstream'),candidates[0])
        line=current.line+(-1 if key=='ArrowUp' else 1 if key=='ArrowDown' else 0)
        available=[edge for edge in presentation.edges if edge.line==line]
        if not available:return False
        if key=='Home':edge=min(available,key=lambda e:(e.x,-e.offset))
        elif key=='End':edge=max(available,key=lambda e:(e.x,e.offset))
        else:edge=min(available,key=lambda e:(abs(e.x-current.x),-e.offset,e.affinity!='downstream'))
        return self._select(scene,prompt,edge.offset,extend)
