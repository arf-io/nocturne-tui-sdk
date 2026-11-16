"""Owned shaped glyph ink regions in the same coordinates as font_svg.

Ink-box hits return whole shaped source spans and persistent identities. They
do not guess caret stops inside ligatures or claim contour-level hit testing.
"""
from dataclasses import dataclass,replace
import math
from font_shaper import HarfBuzzFont,ShapedSegment,shape_scene_paragraph,_automatic_spans,_select_scene_fonts

@dataclass(frozen=True)
class FontParagraphLayout:
    segments:tuple
    line_ends:tuple
    line_widths:tuple
    overflow_lines:tuple

@dataclass(frozen=True)
class TextRunCapture:
    scene:object
    kind:int
    id:int
    host_epoch:int
    source:str
    clusters:tuple

def capture_text_run(scene,kind,id,*,host_epoch):
    """Capture source/identities for cached interaction geometry.

    The host increments its epoch before reset or context replacement. Native
    reset can reuse identifiers; source equality alone cannot distinguish it.
    Capture and geometry creation must be serialized against host mutations.
    """
    if type(host_epoch) is not int or host_epoch<0:raise ValueError('Nonnegative host epoch required')
    source=scene.text_run_source(kind,id);clusters=tuple(tuple(row) for row in scene.text_run_clusters(kind,id))
    if scene.text_run_source(kind,id)!=source or tuple(tuple(row) for row in scene.text_run_clusters(kind,id))!=clusters:raise RuntimeError('Source changed during text capture')
    return TextRunCapture(scene,kind,id,host_epoch,source,clusters)

def text_run_capture_current(scene,capture,*,host_epoch):
    """True only for the same scene, host epoch, source and cluster identities."""
    if not isinstance(capture,TextRunCapture):raise TypeError('Owned text-run capture required')
    if type(host_epoch) is not int or host_epoch<0:raise ValueError('Nonnegative host epoch required')
    if capture.scene is not scene or capture.host_epoch!=host_epoch:return False
    try:
        current=capture_text_run(scene,capture.kind,capture.id,host_epoch=host_epoch)
    except (ValueError,RuntimeError):return False
    return current.source==capture.source and current.clusters==capture.clusters

def shape_wrapped_paragraph(scene,kind,id,fonts,*,width,font_size=32,language,features=(),base_direction=2,break_opportunities=None,break_policy='grapheme',overflow_policy='grapheme'):
    """Greedy whole-grapheme font wrapping with contextual reshaping per line.

    Every candidate is reshaped after native full-paragraph bidi resolution and
    line reset/reordering. Width measures horizontal advances, including spaces,
    rather than ink boxes or terminal cells. One oversized grapheme is retained
    and reported for host clipping. This is an explicit grapheme-wrap policy;
    Host-supplied break opportunities prefer those scalar boundaries when a line
    overflows; oversized unbreakable spans still fall back to whole graphemes.
    overflow_policy='overflow' keeps an oversized unbreakable word intact and
    reports its measured line for host clipping; the default splits at graphemes.
    This accepts linguistic policy without guessing it from font metrics.
    """
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in (width,font_size)):raise ValueError('Positive finite font wrap geometry required')
    if break_policy not in ('grapheme','unicode'):raise ValueError('Unknown font line-break policy')
    if break_policy=='unicode' and break_opportunities is not None:raise ValueError('Explicit opportunities cannot replace the Unicode policy')
    if overflow_policy not in ('grapheme','overflow'):raise ValueError('Unknown font overflow policy')
    if overflow_policy=='overflow' and break_policy!='unicode' and break_opportunities is None:raise ValueError('Word opportunities required for intact overflow')
    fonts=tuple(fonts);features=tuple(features)
    source=scene.text_run_source(kind,id);identities=scene.text_run_clusters(kind,id)
    boundaries=scene.grapheme_boundaries(source)
    preferred=set()
    native_breaks=scene.line_break_details(source) if break_policy=='unicode' else None
    if native_breaks is not None:preferred={offset for offset,mandatory in native_breaks}.intersection(boundaries)-{0}
    if break_opportunities is not None:
        opportunities=tuple(break_opportunities)
        if len(opportunities)>2048:raise ValueError('Too many source break opportunities')
        previous=0;valid=set(boundaries)
        for end in opportunities:
            if type(end) is not int or end<=previous or end>len(source) or end not in valid:raise ValueError('Break opportunities must increase at complete grapheme boundaries')
            preferred.add(end);previous=end
    spans=_automatic_spans(scene,kind,id,fonts,language=language,features=features)
    selected_fonts=_select_scene_fonts(scene,kind,id,spans,base_direction=base_direction)
    hard=[]
    if native_breaks is not None:
        hard=[offset for offset,mandatory in native_breaks if mandatory and offset>0]
        if any(offset not in boundaries for offset in hard):raise RuntimeError('Mandatory break splits a grapheme')
    else:
        for start,end in zip(boundaries,boundaries[1:]):
            if any(c in '\r\n\x0b\x0c\x85\u2028\u2029' for c in source[start:end]):hard.append(end)
        if source and (not hard or hard[-1]!=len(source)):hard.append(len(source))
    def shape(ends,line_only=None):
        segments=shape_scene_paragraph(scene,kind,id,selected_fonts,base_direction=base_direction,line_ends=ends,_line_only=line_only)
        if any(g.glyph==0 for segment in segments for g in segment.run.glyphs):raise ValueError('Selected fonts cannot shape the complete contextual lines')
        return segments
    def widths(segments,lines):
        result=[0.0]*lines
        for segment in segments:
            result[segment.line]+=sum(g.x_advance for g in segment.run.glyphs)*font_size/segment.run.units_per_em
        if any(not math.isfinite(v) or v<0 for v in result):raise ValueError('Invalid horizontal font advance')
        return tuple(result)
    chosen=[];begin=0
    while begin<len(source):
        limit=next(end for end in hard if end>begin);selected=None;preferred_end=None
        for end in boundaries:
            if end<=begin:continue
            if end>limit:break
            trial=chosen+[end]+[stop for stop in hard if stop>end]
            measured=widths(shape(trial,len(chosen)),len(trial))[len(chosen)]
            if measured>width:
                if preferred_end is not None:selected=preferred_end
                elif overflow_policy=='overflow':selected=min((stop for stop in preferred if begin<stop<=limit),default=limit)
                elif selected is None:selected=end
                break
            selected=end
            if end in preferred:preferred_end=end
        if selected is None:raise RuntimeError('No grapheme wrap progress')
        chosen.append(selected);begin=selected
    segments=shape(chosen);measured=widths(segments,len(chosen))
    if scene.text_run_source(kind,id)!=source or scene.text_run_clusters(kind,id)!=identities:raise RuntimeError('Source changed during font wrapping')
    return FontParagraphLayout(segments,tuple(chosen),measured,tuple(i for i,value in enumerate(measured) if value>width))

@dataclass(frozen=True)
class GlyphInkRegion:
    start:int
    end:int
    line:int
    level:int
    glyph:int
    identities:tuple
    left:float
    top:float
    right:float
    bottom:float

@dataclass(frozen=True)
class ShapedSourceEdge:
    offset:int
    line:int
    level:int
    identities:tuple
    x:float
    baseline:float
    affinity:str

def _owned_identities(identities):
    result=[]
    for pair in identities:
        if not isinstance(pair,(tuple,list)) or len(pair)!=2 or type(pair[0]) is not int or not 1<=pair[0]<=0xffffffff or type(pair[1]) is not int or not 0<=pair[1]<=0xffffffff:raise ValueError('Invalid persistent cluster identity')
        result.append(tuple(pair))
    if not result:raise ValueError('Shaped source span requires persistent ownership')
    return tuple(result)

def paragraph_source_edges(segments,*,font_size=32,x=8,baseline=48,line_height=48,alignment='left',content_width=None):
    """Whole shaped-span advance edges, including whitespace without ink.

    These are source boundaries at shaped glyph spans. Ligature interiors need
    font-provided caret data and are not invented here. Odd bidi levels reverse
    logical start/end edges. Both affinities survive visual run boundaries.
    """
    segments=tuple(segments)
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (baseline,line_height)) or line_height<=0:raise ValueError('Invalid source-edge geometry')
    origins=paragraph_line_origins(segments,font_size=font_size,x=x,alignment=alignment,content_width=content_width)
    pens={};result=[]
    for segment in segments:
        run=segment.run
        if type(segment.start) is not int or type(segment.end) is not int or not 0<=segment.start<=segment.end<=2048 or type(segment.level) is not int or not 0<=segment.level<=126:raise ValueError('Invalid shaped source range or bidi level')
        if segment.end-segment.start!=len(run.source) or len(segment.identities)!=len(run.glyphs):raise ValueError('Invalid shaped source ownership')
        pen=pens.get(segment.line,origins[segment.line]);row=baseline+segment.line*line_height;scale=font_size/run.units_per_em
        for index,glyph in enumerate(run.glyphs):
            if not 0<=glyph.start<glyph.end<=len(run.source):raise ValueError('Invalid shaped source span')
            end=pen+glyph.x_advance*scale
            owned=_owned_identities(segment.identities[index])
            startOffset=segment.start+glyph.start;endOffset=segment.start+glyph.end
            if segment.level&1:
                result.append(ShapedSourceEdge(endOffset,segment.line,segment.level,owned,pen,row,'upstream'))
                result.append(ShapedSourceEdge(startOffset,segment.line,segment.level,owned,end,row,'downstream'))
            else:
                result.append(ShapedSourceEdge(startOffset,segment.line,segment.level,owned,pen,row,'downstream'))
                result.append(ShapedSourceEdge(endOffset,segment.line,segment.level,owned,end,row,'upstream'))
            pen=end
        pens[segment.line]=pen
    if any(not math.isfinite(value) for edge in result for value in (edge.x,edge.baseline)):raise ValueError('Source-edge position overflow')
    return tuple(result)

def _viewport_bounds(viewport):
    if viewport is None:return None
    if not isinstance(viewport,(tuple,list)) or len(viewport)!=4:raise ValueError('Viewport requires left/top/right/bottom')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in viewport):raise ValueError('Finite viewport bounds required')
    left,top,right,bottom=viewport
    if right<left or bottom<top:raise ValueError('Reversed viewport bounds')
    return tuple(viewport)

def hit_source_edge(edges,x,y,*,viewport=None):
    """Nearest shaped-span edge: baseline distance, then x, then later offset.

    Equal source/position ties prefer downstream affinity. Empty presentations
    return None; document-end/empty-line carets remain a separate host concern.
    """
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (x,y)):raise ValueError('Finite hit coordinates required')
    edges=tuple(edges)
    if any(not isinstance(edge,ShapedSourceEdge) for edge in edges):raise TypeError('Owned shaped source edges required')
    for edge in edges:
        if type(edge.offset) is not int or not 0<=edge.offset<=2048 or type(edge.line) is not int or edge.line<0 or type(edge.level) is not int or not 0<=edge.level<=126 or edge.affinity not in ('upstream','downstream'):raise ValueError('Invalid source-edge metadata')
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (edge.x,edge.baseline)):raise ValueError('Invalid source-edge position')
        _owned_identities(edge.identities)
    bounds=_viewport_bounds(viewport)
    if bounds is not None and not (bounds[0]<=x<bounds[2] and bounds[1]<=y<bounds[3]):return None
    return min(edges,key=lambda edge:(abs(y-edge.baseline),abs(x-edge.x),-edge.offset,edge.affinity!='downstream'),default=None)

def paragraph_line_origins(segments,*,font_size=32,x=8,alignment='left',content_width=None):
    """Owned line origins from shaped advances in an explicit content box.

    Alignment is physical left/center/right. Overflow keeps the same alignment
    and is clipped by the host; it never changes font size or source content.
    """
    if alignment not in ('left','center','right'):raise ValueError('Invalid physical text alignment')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (font_size,x)) or font_size<=0:raise ValueError('Invalid font alignment geometry')
    if content_width is not None and (isinstance(content_width,bool) or not isinstance(content_width,(int,float)) or not math.isfinite(content_width) or content_width<=0):raise ValueError('Positive finite content width required')
    if alignment!='left' and content_width is None:raise ValueError('Aligned text requires explicit content width')
    widths={};previous=-1
    for segment in segments:
        if not isinstance(segment,ShapedSegment):raise TypeError('Shaped segments required')
        if segment.line<previous or segment.line<0 or segment.run.units_per_em<=0:raise ValueError('Invalid visual line metadata')
        previous=segment.line
        widths[segment.line]=widths.get(segment.line,0)+sum(g.x_advance for g in segment.run.glyphs)*font_size/segment.run.units_per_em
    factor={'left':0,'center':.5,'right':1}[alignment]
    origins={line:x+factor*((content_width or 0)-width) for line,width in widths.items()}
    if any(not math.isfinite(value) for value in (*widths.values(),*origins.values())):raise ValueError('Font alignment overflow')
    return origins

def paragraph_ink_regions(fonts,segments,*,font_size=32,x=8,baseline=48,line_height=48,alignment='left',content_width=None):
    geometry=(font_size,x,baseline,line_height)
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in geometry) or min(font_size,line_height)<=0:raise ValueError('Invalid positioned paragraph geometry')
    fonts=tuple(fonts);segments=tuple(segments)
    if any(not isinstance(f,HarfBuzzFont) for f in fonts) or any(not isinstance(s,ShapedSegment) for s in segments):raise TypeError('Explicit fonts and shaped segments required')
    origins=paragraph_line_origins(segments,font_size=font_size,x=x,alignment=alignment,content_width=content_width)
    result=[];pens={};previous=-1
    for segment in segments:
        run=segment.run
        if segment.line<previous or segment.line<0 or segment.end-segment.start!=len(run.source) or len(segment.identities)!=len(run.glyphs):raise ValueError('Invalid visual-order segment metadata')
        previous=segment.line
        font=next((f for f in fonts if (f.font_sha256,f.face_index,f.engine_version,f.units_per_em)==(run.font_sha256,run.face_index,run.engine_version,run.units_per_em)),None)
        if font is None:raise ValueError('Missing exact rendering font')
        scale=font_size/run.units_per_em;left=pens.get(segment.line,origins[segment.line]);top=baseline+segment.line*line_height;px=py=0
        for index,glyph in enumerate(run.glyphs):
            if not glyph.glyph:raise ValueError('Missing glyph cannot be accepted')
            extents=font.glyph_extents(glyph.glyph)
            if extents is None:raise ValueError('Font glyph ink extents unavailable')
            xb,yb,w,h=extents
            gx=left+(px+glyph.x_offset+xb)*scale;gy=top-(py+glyph.y_offset+yb)*scale
            bounds=(min(gx,gx+w*scale),min(gy,gy-h*scale),max(gx,gx+w*scale),max(gy,gy-h*scale))
            if any(not math.isfinite(v) for v in bounds):raise ValueError('Positioned glyph extent overflow')
            result.append(GlyphInkRegion(segment.start+glyph.start,segment.start+glyph.end,segment.line,segment.level,glyph.glyph,segment.identities[index],*bounds))
            px+=glyph.x_advance;py+=glyph.y_advance
        pens[segment.line]=left+px*scale
        if not math.isfinite(pens[segment.line]):raise ValueError('Paragraph advance overflow')
    return tuple(result)

def clip_ink_regions(regions,viewport):
    """Copy visible ink intersections while retaining whole source ownership.

    Clipping changes geometry only, never ligature spans or retained identities.
    Empty intersections are omitted. Original regions remain unchanged.
    """
    bounds=_viewport_bounds(viewport)
    if bounds is None:raise ValueError('Explicit viewport required')
    regions=tuple(regions)
    if any(not isinstance(r,GlyphInkRegion) for r in regions):raise TypeError('Owned ink regions required')
    result=[]
    for region in regions:
        left=max(region.left,bounds[0]);top=max(region.top,bounds[1]);right=min(region.right,bounds[2]);bottom=min(region.bottom,bounds[3])
        if left<right and top<bottom:result.append(replace(region,left=left,top=top,right=right,bottom=bottom))
    return tuple(result)

def hit_ink_region(regions,x,y,*,viewport=None):
    """Return the last painted nonempty ink box containing the point, or None."""
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (x,y)):raise ValueError('Finite hit coordinates required')
    regions=tuple(regions)
    if any(not isinstance(r,GlyphInkRegion) for r in regions):raise TypeError('Owned ink regions required')
    bounds=_viewport_bounds(viewport)
    if bounds is not None and not (bounds[0]<=x<bounds[2] and bounds[1]<=y<bounds[3]):return None
    return next((r for r in reversed(regions) if r.left<=x<r.right and r.top<=y<r.bottom),None)

def select_ink_regions(regions,start,end):
    """Whole painted glyphs intersecting a half-open logical scalar selection.

    Visual order is preserved even when selected bidi text has disjoint geometry.
    A selection inside a ligature returns its full source span, not a fabricated
    partial glyph. Empty selections return no regions.
    """
    if type(start) is not int or type(end) is not int or not 0<=start<=end<=2048:raise ValueError('Invalid logical source selection')
    regions=tuple(regions)
    if any(not isinstance(r,GlyphInkRegion) for r in regions):raise TypeError('Owned ink regions required')
    if start==end:return ()
    return tuple(r for r in regions if r.start<end and r.end>start)

def select_identity_regions(regions,identities):
    """Select whole glyphs by exact persistent (identity,generation) pairs.

    Unknown or retired pairs select nothing. Generation zero is the native
    animated-text namespace. Pairs belong to one scene/run key; callers must not
    reuse them across run keys and discard them before scene reset.
    """
    regions=tuple(regions);identities=tuple(identities)
    if any(not isinstance(r,GlyphInkRegion) for r in regions):raise TypeError('Owned ink regions required')
    selected=set()
    for pair in identities:
        if not isinstance(pair,(tuple,list)) or len(pair)!=2 or type(pair[0]) is not int or not 1<=pair[0]<=0xffffffff or type(pair[1]) is not int or not 0<=pair[1]<=0xffffffff:raise ValueError('Exact nonzero identity and uint32 generation required')
        selected.add(tuple(pair))
    return tuple(r for r in regions if any(pair in selected for pair in r.identities))
