"""Explicit host-owned OpenType shaping; no fonts, discovery, clock or scene edits.

Uses the HarfBuzz C API documented at https://harfbuzz.github.io/harfbuzz-hb-buffer.html
and https://harfbuzz.github.io/harfbuzz-hb-shape.html. Caller provides exact library
and font bytes and itemizes script/direction/language; this is not a bidi engine.
"""
import ctypes as C
from dataclasses import dataclass
import hashlib,re,math
from threading import RLock
@dataclass(frozen=True)
class PositionedGlyph:
    glyph:int
    start:int
    end:int
    x_advance:int
    y_advance:int
    x_offset:int
    y_offset:int
    flags:int
@dataclass(frozen=True)
class ShapedRun:
    source:str
    direction:str
    script:str
    language:str
    font_sha256:str
    face_index:int
    engine_version:str
    units_per_em:int
    features:tuple
    glyphs:tuple
class GlyphInfo(C.Structure):
    _fields_=[('codepoint',C.c_uint32),('mask',C.c_uint32),('cluster',C.c_uint32),('var1',C.c_uint32),('var2',C.c_uint32)]
class GlyphPosition(C.Structure):
    _fields_=[('x_advance',C.c_int32),('y_advance',C.c_int32),('x_offset',C.c_int32),('y_offset',C.c_int32),('var',C.c_uint32)]
class GlyphExtents(C.Structure):
    _fields_=[('x_bearing',C.c_int32),('y_bearing',C.c_int32),('width',C.c_int32),('height',C.c_int32)]
class Feature(C.Structure):
    _fields_=[('tag',C.c_uint32),('value',C.c_uint32),('start',C.c_uint32),('end',C.c_uint32)]
class HarfBuzzFont:
    def __init__(self,font_bytes,library,face_index=0):
        if not isinstance(font_bytes,bytes) or not 1<=len(font_bytes)<=64*1024*1024:raise ValueError('Explicit font bytes required (1..64 MiB)')
        if type(face_index) is not int or not 0<=face_index<=65535:raise ValueError('Invalid font face index')
        self._lock=RLock();self._font=None;self.font_sha256=hashlib.sha256(font_bytes).hexdigest();self.face_index=face_index
        self._lib=C.CDLL(str(library));l=self._lib
        signatures={
          'hb_blob_create':([C.c_void_p,C.c_uint,C.c_int,C.c_void_p,C.c_void_p],C.c_void_p),
          'hb_blob_destroy':([C.c_void_p],None),'hb_face_create':([C.c_void_p,C.c_uint],C.c_void_p),'hb_face_destroy':([C.c_void_p],None),
          'hb_face_get_upem':([C.c_void_p],C.c_uint),'hb_face_get_glyph_count':([C.c_void_p],C.c_uint),
          'hb_font_create':([C.c_void_p],C.c_void_p),'hb_font_destroy':([C.c_void_p],None),'hb_ot_font_set_funcs':([C.c_void_p],None),
          'hb_font_set_scale':([C.c_void_p,C.c_int,C.c_int],None),'hb_version_string':([],C.c_char_p),
          'hb_buffer_create':([],C.c_void_p),'hb_buffer_destroy':([C.c_void_p],None),'hb_buffer_allocation_successful':([C.c_void_p],C.c_int),
          'hb_buffer_add_utf32':([C.c_void_p,C.POINTER(C.c_uint32),C.c_int,C.c_uint,C.c_int],None),
          'hb_direction_from_string':([C.c_char_p,C.c_int],C.c_int),'hb_script_from_string':([C.c_char_p,C.c_int],C.c_uint32),
          'hb_language_from_string':([C.c_char_p,C.c_int],C.c_void_p),
          'hb_buffer_set_direction':([C.c_void_p,C.c_int],None),'hb_buffer_set_script':([C.c_void_p,C.c_uint32],None),
          'hb_buffer_set_language':([C.c_void_p,C.c_void_p],None),'hb_buffer_set_cluster_level':([C.c_void_p,C.c_int],None),
          'hb_feature_from_string':([C.c_char_p,C.c_int,C.POINTER(Feature)],C.c_int),
          'hb_shape_full':([C.c_void_p,C.c_void_p,C.POINTER(Feature),C.c_uint,C.POINTER(C.c_char_p)],C.c_int),
          'hb_buffer_get_glyph_infos':([C.c_void_p,C.POINTER(C.c_uint)],C.POINTER(GlyphInfo)),
          'hb_buffer_get_glyph_positions':([C.c_void_p,C.POINTER(C.c_uint)],C.POINTER(GlyphPosition)),
          'hb_glyph_info_get_glyph_flags':([C.POINTER(GlyphInfo)],C.c_uint32)}
        for name,(args,result) in signatures.items():fn=getattr(l,name);fn.argtypes=args;fn.restype=result
        data=C.create_string_buffer(font_bytes);blob=l.hb_blob_create(data,len(font_bytes),0,None,None)
        if not blob:raise MemoryError('Font blob allocation')
        face=None
        try:
            face=l.hb_face_create(blob,face_index)
            if not face or not l.hb_face_get_glyph_count(face):raise ValueError('Font has no usable glyph face')
            self.glyph_count=l.hb_face_get_glyph_count(face)
            self.units_per_em=l.hb_face_get_upem(face)
            if not 1<=self.units_per_em<=16384:raise ValueError('Invalid font units per em')
            self._font=l.hb_font_create(face)
            if not self._font:raise MemoryError('Font allocation')
            l.hb_ot_font_set_funcs(self._font);l.hb_font_set_scale(self._font,self.units_per_em,self.units_per_em)
            self.engine_version=l.hb_version_string().decode('ascii')
        except BaseException:
            self.close();raise
        finally:
            if face:l.hb_face_destroy(face)
            l.hb_blob_destroy(blob)
    def close(self):
        with self._lock:
            if self._font:self._lib.hb_font_destroy(self._font);self._font=None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def shape(self,text,*,direction,script,language,features=()):
        if not isinstance(text,str) or len(text)>2048 or any(0xd800<=ord(c)<=0xdfff for c in text):raise ValueError('Valid Unicode scalar source required (<=2048)')
        if direction not in ('ltr','rtl','ttb','btt'):raise ValueError('Explicit run direction required')
        if not isinstance(script,str) or not re.fullmatch('[A-Z][a-z]{3}',script):raise ValueError('Explicit ISO15924 script tag required')
        if not isinstance(language,str) or not re.fullmatch('[A-Za-z0-9-]{1,63}',language):raise ValueError('Explicit language tag required')
        features=tuple(features)
        if len(features)>64 or any(not isinstance(f,str) or not f.isascii() or len(f)>127 for f in features):raise ValueError('Invalid OpenType feature list')
        with self._lock:
            if not self._font:raise RuntimeError('Font shaper is closed')
            l=self._lib;parsed=(Feature*len(features))()
            for i,f in enumerate(features):
                if not l.hb_feature_from_string(f.encode(),len(f),C.byref(parsed[i])):raise ValueError('Invalid OpenType feature: '+f)
            buffer=l.hb_buffer_create()
            try:
                if not buffer or not l.hb_buffer_allocation_successful(buffer):raise MemoryError('Shape buffer allocation')
                source=(C.c_uint32*len(text))(*map(ord,text));l.hb_buffer_add_utf32(buffer,source,len(text),0,len(text))
                l.hb_buffer_set_direction(buffer,l.hb_direction_from_string(direction.encode(),len(direction)))
                l.hb_buffer_set_script(buffer,l.hb_script_from_string(script.encode(),4));l.hb_buffer_set_language(buffer,l.hb_language_from_string(language.encode(),len(language)))
                l.hb_buffer_set_cluster_level(buffer,0)
                if not l.hb_shape_full(self._font,buffer,parsed,len(features),None) or not l.hb_buffer_allocation_successful(buffer):raise RuntimeError('OpenType shaping failed')
                n=C.c_uint();m=C.c_uint();infos=l.hb_buffer_get_glyph_infos(buffer,C.byref(n));positions=l.hb_buffer_get_glyph_positions(buffer,C.byref(m))
                if n.value!=m.value or n.value>65536:raise RuntimeError('Invalid shaped glyph count')
                starts=sorted(set(infos[i].cluster for i in range(n.value)))
                if starts and (starts[0]<0 or starts[-1]>=len(text)):raise RuntimeError('Invalid shaped source clusters')
                ends=dict(zip(starts,starts[1:]+[len(text)]));glyphs=[]
                for i in range(n.value):
                    q,p=infos[i],positions[i];flags=l.hb_glyph_info_get_glyph_flags(C.byref(infos[i]))
                    glyphs.append(PositionedGlyph(q.codepoint,q.cluster,ends[q.cluster],p.x_advance,p.y_advance,p.x_offset,p.y_offset,flags))
                return ShapedRun(text,direction,script,language,self.font_sha256,self.face_index,self.engine_version,self.units_per_em,features,tuple(glyphs))
            finally:
                if buffer:l.hb_buffer_destroy(buffer)
    def ligature_carets(self,glyph,*,direction):
        """Owned GDEF caret coordinates, in font units and font table order.

        An empty tuple means the font supplies no positions. These coordinates
        are unshaped: callers account for glyph placement/kerning and do not
        infer source offsets or synthesize absent carets.
        """
        if type(glyph) is not int or not 0<=glyph<self.glyph_count:raise ValueError('Invalid font glyph ID')
        if direction not in ('ltr','rtl','ttb','btt'):raise ValueError('Explicit caret direction required')
        with self._lock:
            if not self._font:raise RuntimeError('Font shaper is closed')
            fn=self._lib.hb_ot_layout_get_ligature_carets
            fn.argtypes=[C.c_void_p,C.c_int,C.c_uint32,C.c_uint,C.POINTER(C.c_uint),C.POINTER(C.c_int32)];fn.restype=C.c_uint
            code=self._lib.hb_direction_from_string(direction.encode(),len(direction));count=C.c_uint()
            total=fn(self._font,code,glyph,0,C.byref(count),None)
            if total>65536:raise ValueError('Oversized font caret table')
            if not total:return ()
            positions=(C.c_int32*total)();count.value=total
            actual=fn(self._font,code,glyph,0,C.byref(count),positions)
            if actual!=total or count.value!=total:raise RuntimeError('Inconsistent font caret table')
            return tuple(positions)
    def glyph_extents(self,glyph):
        """Owned font-unit ink bearing/size, or None when unavailable."""
        if type(glyph) is not int or not 0<=glyph<self.glyph_count:raise ValueError('Invalid font glyph ID')
        with self._lock:
            if not self._font:raise RuntimeError('Font shaper is closed')
            fn=self._lib.hb_font_get_glyph_extents
            fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(GlyphExtents)];fn.restype=C.c_int
            extents=GlyphExtents()
            if not fn(self._font,glyph,C.byref(extents)):return None
            return (extents.x_bearing,extents.y_bearing,extents.width,extents.height)
    def glyph_outline(self,glyph):
        """Owned M/L/Q/C/Z font-unit outline; requires HB outline failure API."""
        if type(glyph) is not int or not 0<=glyph<self.glyph_count:raise ValueError('Invalid font glyph ID')
        with self._lock:
            if not self._font:raise RuntimeError('Font shaper is closed')
            l=self._lib
            try:draw=l.hb_font_draw_glyph_or_fail
            except AttributeError as error:raise RuntimeError('Outline rendering requires HarfBuzz 11.2 or newer') from error
            draw.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_void_p];draw.restype=C.c_int
            l.hb_draw_funcs_create.argtypes=[];l.hb_draw_funcs_create.restype=C.c_void_p
            l.hb_draw_funcs_destroy.argtypes=[C.c_void_p];l.hb_draw_funcs_destroy.restype=None
            l.hb_draw_funcs_make_immutable.argtypes=[C.c_void_p];l.hb_draw_funcs_make_immutable.restype=None
            output=[];failed=[False];callbacks=[]
            def collect(verb,coordinates):
                if failed[0]:return
                try:
                    if len(output)>=65536 or any(not math.isfinite(v) or abs(v)>1e9 for v in coordinates):failed[0]=True;return
                    output.append((verb,*coordinates))
                except BaseException:failed[0]=True
            funcs=l.hb_draw_funcs_create()
            if not funcs:raise MemoryError('Outline function allocation')
            try:
                for name,verb,count in [('move_to','M',2),('line_to','L',2),('quadratic_to','Q',4),('cubic_to','C',6),('close_path','Z',0)]:
                    prototype=C.CFUNCTYPE(None,C.c_void_p,C.c_void_p,C.c_void_p,*([C.c_float]*count),C.c_void_p)
                    def callback(*args,verb=verb,count=count):collect(verb,args[3:3+count])
                    cb=prototype(callback);callbacks.append(cb);setter=getattr(l,'hb_draw_funcs_set_'+name+'_func');setter.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];setter.restype=None
                    setter(funcs,C.cast(cb,C.c_void_p),None,None)
                l.hb_draw_funcs_make_immutable(funcs)
                if not draw(self._font,glyph,funcs,None):
                    extents=GlyphExtents();fn=l.hb_font_get_glyph_extents;fn.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(GlyphExtents)];fn.restype=C.c_int
                    if not fn(self._font,glyph,C.byref(extents)) or extents.width or extents.height:raise ValueError('Font glyph has no supported outline')
                if failed[0]:raise ValueError('Invalid or oversized glyph outline')
                return tuple(output)
            finally:l.hb_draw_funcs_destroy(funcs)
    def features_for_slice(self,features,start,end):
        """Rebase scalar-index feature ranges from an itemized span to a slice."""
        if type(start) is not int or type(end) is not int or not 0<=start<=end<=2048:raise ValueError('Invalid feature slice')
        features=tuple(features)
        if len(features)>64 or any(not isinstance(f,str) or not f.isascii() or len(f)>127 for f in features):raise ValueError('Invalid OpenType feature list')
        with self._lock:
            if not self._font:raise RuntimeError('Font shaper is closed')
            result=[]
            for text in features:
                feature=Feature()
                if not self._lib.hb_feature_from_string(text.encode(),len(text),C.byref(feature)):raise ValueError('Invalid OpenType feature: '+text)
                first=max(start,feature.start);last=min(end,feature.end)
                if first>=last:continue
                tag=feature.tag.to_bytes(4,'big').decode('ascii').rstrip(' ')
                result.append(f'{tag}[{first-start}:{last-start}]={feature.value}')
            return tuple(result)
    def shape_scene_run(self,scene,kind,id,**options):
        """Caller serializes the source/identity capture against scene mutations."""
        source=scene.text_run_source(kind,id);clusters=scene.text_run_clusters(kind,id)
        shaped=self.shape(source,**options)
        if scene.text_run_source(kind,id)!=source or scene.text_run_clusters(kind,id)!=clusters:raise RuntimeError('Source changed during shaping')
        mapping=tuple(tuple((r[0],r[3]) for r in clusters if r[1]<glyph.end and r[2]>glyph.start) for glyph in shaped.glyphs)
        return shaped,mapping

@dataclass(frozen=True)
class ShapedSegment:
    start:int
    end:int
    line:int
    level:int
    run:ShapedRun
    identities:tuple

def shape_scene_paragraph(scene,kind,id,spans,*,base_direction=2,line_ends=None,_line_only=None):
    """Shape explicit script/font spans in native visual run order.

    Spans cover source exactly and end at native grapheme boundaries. Each has
    start/end/font/script/language and optional feature strings. The caller owns
    itemization/font fallback and serializes source capture against mutations.
    Optional line_ends select whole-grapheme soft lines without changing source.
    Returned placements are font metrics, not terminal-cell width estimates.
    """
    source=scene.text_run_source(kind,id);clusters=scene.text_run_clusters(kind,id)
    if _line_only is not None and (type(_line_only) is not int or _line_only<0):raise ValueError('Invalid measured line')
    boundaries=set(scene.grapheme_boundaries(source));spans=list(spans);previous=0
    for span in spans:
        if not isinstance(span,dict) or set(span)-{'start','end','font','script','language','features'}:raise ValueError('Invalid shaping span')
        start,end=span.get('start'),span.get('end')
        if type(start) is not int or type(end) is not int or start!=previous or end<=start or start not in boundaries or end not in boundaries:raise ValueError('Shaping spans must partition whole graphemes')
        if not isinstance(span.get('font'),HarfBuzzFont) or 'script' not in span or 'language' not in span:raise ValueError('Explicit font/script/language required')
        previous=end
    if previous!=len(source):raise ValueError('Shaping spans do not cover source')
    visual=(scene.bidi_layout(source,0xffffffff,direction=base_direction) if line_ends is None
            else scene.bidi_lines(source,line_ends,direction=base_direction));groups=[]
    for start,end,column,line,width,level,mapped in visual:
        if _line_only is not None and line!=_line_only:continue
        if any(c in '\r\n\x0b\x0c\x85\u2028\u2029' for c in source[start:end]):continue
        index=next((i for i,span in enumerate(spans) if span['start']<=start and end<=span['end']),None)
        if index is None:raise ValueError('Native cluster crosses itemized span')
        if groups and groups[-1]['index']==index and groups[-1]['line']==line and groups[-1]['level']==level and (end==groups[-1]['start'] if level&1 else start==groups[-1]['end']):
            groups[-1]['start']=min(start,groups[-1]['start']);groups[-1]['end']=max(end,groups[-1]['end'])
        else:groups.append(dict(index=index,start=start,end=end,line=line,level=level))
    result=[]
    for group in groups:
        span=spans[group['index']];start,end=group['start'],group['end']
        run=span['font'].shape(source[start:end],direction='rtl' if group['level']&1 else 'ltr',script=span['script'],language=span['language'],features=span['font'].features_for_slice(span.get('features',()),start-span['start'],end-span['start']))
        identities=tuple(tuple((r[0],r[3]) for r in clusters if r[1]<start+glyph.end and r[2]>start+glyph.start) for glyph in run.glyphs)
        result.append(ShapedSegment(start,end,group['line'],group['level'],run,identities))
    if scene.text_run_source(kind,id)!=source or scene.text_run_clusters(kind,id)!=clusters:raise RuntimeError('Source changed during paragraph shaping')
    return tuple(result)

def _select_scene_fonts(scene,kind,id,spans,*,base_direction=2):
    """Ordered explicit font pools; reject unresolved whole-grapheme coverage.

    Caller itemizes script/language ranges. Prefer one covering font for a whole
    span, then choose per native grapheme and merge adjacent same-font spans.
    Missing coverage is an explicit error, never a replacement of source text.
    """
    source=scene.text_run_source(kind,id);clusters=scene.text_run_clusters(kind,id)
    boundaries=scene.grapheme_boundaries(source);boundary_set=set(boundaries);spans=list(spans)
    visual=scene.bidi_layout(source,0xffffffff,direction=base_direction);levels={r[0]:r[5] for r in visual}
    selected=[];previous=0
    for span in spans:
        if not isinstance(span,dict) or set(span)-{'start','end','fonts','script','language','features'}:raise ValueError('Invalid fallback span')
        start,end=span.get('start'),span.get('end');fonts=span.get('fonts')
        if type(start) is not int or type(end) is not int or start!=previous or end<=start or start not in boundary_set or end not in boundary_set:raise ValueError('Fallback spans must partition whole graphemes')
        if not isinstance(fonts,(list,tuple)) or not 1<=len(fonts)<=32 or any(not isinstance(f,HarfBuzzFont) for f in fonts):raise ValueError('Explicit ordered font pool required (1..32)')
        if 'script' not in span or 'language' not in span:raise ValueError('Explicit fallback script/language required')
        options=dict(script=span['script'],language=span['language'],features=span.get('features',()))
        def covering(text,offset):
            direction='rtl' if levels.get(offset,0)&1 else 'ltr'
            for font in fonts:
                slice_options=dict(options);slice_options['features']=font.features_for_slice(options['features'],offset-start,offset-start+len(text))
                run=font.shape(text,direction=direction,**slice_options)
                if all(g.glyph!=0 for g in run.glyphs):return font
            return None
        whole=covering(source[start:end],start)
        if whole is not None:selected.append(dict(start=start,end=end,font=whole,feature_origin=start,**options))
        else:
            edges=[b for b in boundaries if start<=b<=end]
            for begin,last in zip(edges,edges[1:]):
                text=source[begin:last]
                font=fonts[0] if all(c in '\r\n\x0b\x0c\x85\u2028\u2029' for c in text) else covering(text,begin)
                if font is None:raise ValueError(f'No declared font covers grapheme [{begin},{last})')
                if selected and selected[-1]['end']==begin and selected[-1]['start']>=start and selected[-1]['font'] is font:selected[-1]['end']=last
                else:
                    selected.append(dict(start=begin,end=last,font=font,feature_origin=start,**options))
        previous=end
    if previous!=len(source):raise ValueError('Fallback spans do not cover source')
    if scene.text_run_source(kind,id)!=source or scene.text_run_clusters(kind,id)!=clusters:raise RuntimeError('Source changed during font selection')
    for span in selected:
        origin=span.pop('feature_origin');span['features']=span['font'].features_for_slice(span['features'],span['start']-origin,span['end']-origin)
    return selected

def shape_scene_with_fallback(scene,kind,id,spans,*,base_direction=2,line_ends=None):
    """Shape declared whole-grapheme font pools, optionally on explicit lines."""
    source=scene.text_run_source(kind,id);clusters=scene.text_run_clusters(kind,id)
    selected=_select_scene_fonts(scene,kind,id,spans,base_direction=base_direction)
    result=shape_scene_paragraph(scene,kind,id,selected,base_direction=base_direction,line_ends=line_ends)
    if scene.text_run_source(kind,id)!=source or scene.text_run_clusters(kind,id)!=clusters:raise RuntimeError('Source changed during font fallback shaping')
    if any(g.glyph==0 for segment in result for g in segment.run.glyphs):raise ValueError('Selected fonts cannot shape the complete contextual runs')
    return result

def _automatic_spans(scene,kind,id,fonts,*,language,features=()):
    """Native Unicode-17 script spans plus explicit host fonts/language/features.

    Language is a single explicit tag or a script->language mapping with optional
    '*' default. Feature ranges use global source scalar offsets and are rebased
    for each itemized span. Native bidi and whole-grapheme font fallback remain
    the existing presentation path; source and persistent identities stay owned.
    """
    if not isinstance(fonts,(list,tuple)) or not 1<=len(fonts)<=32 or any(not isinstance(font,HarfBuzzFont) for font in fonts):raise ValueError('Explicit ordered font pool required (1..32)')
    if not isinstance(language,(str,dict)):raise ValueError('Explicit language or script-language mapping required')
    tags=[language] if isinstance(language,str) else list(language.values())
    if any(not isinstance(tag,str) or not re.fullmatch('[A-Za-z0-9-]{1,63}',tag) for tag in tags):raise ValueError('Explicit language tag required')
    features=tuple(features)
    source=scene.text_run_source(kind,id);clusters=scene.text_run_clusters(kind,id);spans=[]
    for start,end,script in scene.script_runs(source):
        selected=language if isinstance(language,str) else language.get(script,language.get('*'))
        if not isinstance(selected,str) or not selected:raise ValueError(f'No explicit language for {script}')
        spans.append(dict(start=start,end=end,fonts=fonts,script=script,language=selected,features=fonts[0].features_for_slice(features,start,end)))
    if scene.text_run_source(kind,id)!=source or scene.text_run_clusters(kind,id)!=clusters:raise RuntimeError('Source changed during automatic script itemization')
    return spans

def shape_scene_automatic(scene,kind,id,fonts,*,language,features=(),base_direction=2,line_ends=None):
    """Shape native script spans with explicit fonts, languages and features."""
    source=scene.text_run_source(kind,id);clusters=scene.text_run_clusters(kind,id)
    spans=_automatic_spans(scene,kind,id,fonts,language=language,features=features)
    result=shape_scene_with_fallback(scene,kind,id,spans,base_direction=base_direction,line_ends=line_ends)
    if scene.text_run_source(kind,id)!=source or scene.text_run_clusters(kind,id)!=clusters:raise RuntimeError('Source changed during automatic paragraph shaping')
    return result
