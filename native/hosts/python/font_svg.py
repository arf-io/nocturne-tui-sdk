"""Position exact shaped font outlines in an owned SVG; no platform font lookup."""
import html,json,math,re
from font_shaper import HarfBuzzFont,ShapedRun

def shaped_run_svg(font,run,*,width=640,height=120,font_size=32,x=8,baseline=64,foreground='#e4dacc',alpha=1):
    if not isinstance(font,HarfBuzzFont) or not isinstance(run,ShapedRun):raise TypeError('Explicit font and shaped run required')
    if (run.font_sha256,run.face_index,run.units_per_em,run.engine_version)!=(font.font_sha256,font.face_index,font.units_per_em,font.engine_version):raise ValueError('Shaped run and rendering font provenance differ')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (width,height,font_size,x,baseline,alpha)) or min(width,height,font_size)<=0 or not 0<=alpha<=1:raise ValueError('Invalid SVG geometry or alpha')
    if not isinstance(foreground,str) or not re.fullmatch('#[0-9a-fA-F]{6}',foreground):raise ValueError('Explicit RGB foreground required')
    scale=font_size/run.units_per_em;pen_x=pen_y=0;paths=[];outlines={}
    for index,glyph in enumerate(run.glyphs):
        if not glyph.glyph:raise ValueError('Missing glyph cannot be presented as accepted text')
        if glyph.glyph not in outlines:outlines[glyph.glyph]=font.glyph_outline(glyph.glyph)
        path=' '.join(command[0]+(' '.join(format(v,'.9g') for v in command[1:])) for command in outlines[glyph.glyph])
        gx=x+(pen_x+glyph.x_offset)*scale;gy=baseline-(pen_y+glyph.y_offset)*scale
        if not math.isfinite(gx) or not math.isfinite(gy):raise ValueError('Positioned outline overflow')
        if path:paths.append(f'<path data-index="{index}" data-glyph="{glyph.glyph}" data-start="{glyph.start}" data-end="{glyph.end}" d="{path}" transform="translate({gx:.9g} {gy:.9g}) scale({scale:.9g} {-scale:.9g})"/>')
        pen_x+=glyph.x_advance;pen_y+=glyph.y_advance
    metadata=dict(source=run.source,fontSha256=run.font_sha256,faceIndex=run.face_index,engineVersion=run.engine_version,unitsPerEm=run.units_per_em,direction=run.direction,script=run.script,language=run.language,features=run.features)
    title=''.join(c if ord(c) in (9,10,13) or 32<=ord(c)<=0xd7ff or 0xe000<=ord(c)<=0xfffd or 0x10000<=ord(c)<=0x10ffff else '\ufffd' for c in run.source)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.9g}" height="{height:.9g}" viewBox="0 0 {width:.9g} {height:.9g}" role="img"><title>{html.escape(title)}</title><metadata>{html.escape(json.dumps(metadata,sort_keys=True))}</metadata><svg width="100%" height="100%" overflow="hidden"><g fill="{foreground}" opacity="{alpha:.9g}">'+''.join(paths)+'</g></svg></svg>'

def shaped_paragraph_svg(fonts,segments,*,width=640,height=240,font_size=32,x=8,baseline=48,line_height=48,foreground='#e4dacc',alpha=1,selection=None,selection_identities=None,selection_color='#3975a8',selection_alpha=.5,alignment='left',content_width=None):
    """Compose native visual-order runs using actual font advances per line.

    Caller provides the fonts referenced by segment provenance. Source line breaks
    are respected; this operation does not rewrap using terminal-cell metrics.
    Glyph metadata retains global scalar spans and persistent cluster ownership.
    """
    import xml.etree.ElementTree as E
    from font_shaper import ShapedSegment
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (width,height,font_size,x,baseline,line_height,alpha)) or min(width,height,font_size,line_height)<=0 or not 0<=alpha<=1:raise ValueError('Invalid paragraph presentation geometry')
    if not isinstance(foreground,str) or not re.fullmatch('#[0-9a-fA-F]{6}',foreground):raise ValueError('Explicit RGB foreground required')
    fonts=list(fonts);segments=tuple(segments)
    if any(not isinstance(f,HarfBuzzFont) for f in fonts) or any(not isinstance(s,ShapedSegment) for s in segments):raise TypeError('Explicit fonts and shaped segments required')
    from font_layout import paragraph_line_origins
    origins=paragraph_line_origins(segments,font_size=font_size,x=x,alignment=alignment,content_width=content_width)
    if selection is not None and selection_identities is not None:raise ValueError('Choose logical or retained selection')
    if not isinstance(selection_color,str) or not re.fullmatch('#[0-9a-fA-F]{6}',selection_color) or isinstance(selection_alpha,bool) or not isinstance(selection_alpha,(int,float)) or not math.isfinite(selection_alpha) or not 0<=selection_alpha<=1:raise ValueError('Invalid selection paint')
    ns='http://www.w3.org/2000/svg';E.register_namespace('',ns)
    root=E.Element('{'+ns+'}svg',dict(width=format(width,'.9g'),height=format(height,'.9g'),viewBox=f'0 0 {width:.9g} {height:.9g}',role='img'))
    if selection is not None or selection_identities is not None:
        from font_layout import paragraph_ink_regions,select_ink_regions,select_identity_regions
        regions=paragraph_ink_regions(fonts,segments,font_size=font_size,x=x,baseline=baseline,line_height=line_height,alignment=alignment,content_width=content_width)
        if selection is not None:
            if not isinstance(selection,(tuple,list)) or len(selection)!=2:raise ValueError('Logical selection needs start/end')
            chosen=select_ink_regions(regions,*selection)
        else:chosen=select_identity_regions(regions,selection_identities)
        paint=E.SubElement(root,'{'+ns+'}g',{'data-selection':'ink','fill':selection_color,'opacity':format(selection_alpha,'.9g')})
        for region in chosen:
            if region.right<=region.left or region.bottom<=region.top:continue
            E.SubElement(paint,'{'+ns+'}rect',dict(x=format(region.left,'.9g'),y=format(region.top,'.9g'),width=format(region.right-region.left,'.9g'),height=format(region.bottom-region.top,'.9g'),**{'data-start':str(region.start),'data-end':str(region.end),'data-identities':json.dumps(region.identities,separators=(',',':'))}))
    pen={};previous=-1
    for segment in segments:
        if segment.line<previous or segment.line<0 or segment.end-segment.start!=len(segment.run.source) or len(segment.identities)!=len(segment.run.glyphs):raise ValueError('Invalid visual-order segment metadata')
        previous=segment.line;run=segment.run
        font=next((f for f in fonts if (f.font_sha256,f.face_index,f.engine_version,f.units_per_em)==(run.font_sha256,run.face_index,run.engine_version,run.units_per_em)),None)
        if font is None:raise ValueError('Missing exact font for positioned segment')
        left=pen.get(segment.line,origins[segment.line]);top=baseline+segment.line*line_height
        svg=E.fromstring(shaped_run_svg(font,run,width=width,height=height,font_size=font_size,x=left,baseline=top,foreground=foreground,alpha=alpha))
        svg.set('data-source-start',str(segment.start));svg.set('data-source-end',str(segment.end));svg.set('data-line',str(segment.line));svg.set('data-level',str(segment.level))
        for path in svg.findall('.//{'+ns+'}path'):
            index=int(path.attrib['data-index']);glyph=run.glyphs[index]
            path.set('data-start',str(segment.start+glyph.start));path.set('data-end',str(segment.start+glyph.end))
            path.set('data-identities',json.dumps(segment.identities[index],separators=(',',':')))
        root.append(svg);pen[segment.line]=left+sum(g.x_advance for g in run.glyphs)*font_size/run.units_per_em
        if not math.isfinite(pen[segment.line]):raise ValueError('Paragraph advance overflow')
    return E.tostring(root,encoding='unicode')
