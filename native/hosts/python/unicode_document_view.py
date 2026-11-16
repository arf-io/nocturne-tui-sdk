"""Opt-in ANSI document view over native Unicode layout and source mapping."""
class UnicodeDocumentView:
    def __init__(self):self.columns=1;self.rows=1;self.scroll=0;self.drag=None;self.drag_identity=None;self.max_scroll=0;self.last_caret=None;self.preferred_column=None;self.last_source=None
    def state(self,scene):
        info=scene.info_complete()
        return info['prompt'] if info.get('inputOwner')=='prompt' else None
    def caret(self,scene,text,p):
        boundaries=scene.document_boundaries(text)
        offset=max(b for b in boundaries if b<=p['caret'])
        return scene.document_caret(text,self.columns,offset)
    def presentation(self,scene,columns,rows):
        p=self.state(scene)
        if p is None:self.cancel_drag();return None
        self.columns=max(1,columns);self.rows=max(0,rows-1)
        text=scene.text_run_source(0,0);layout=scene.document_layout(text,self.columns)
        try:caret=self.caret(scene,text,p)
        except ValueError:caret=None
        signature=(text,p['caret'],self.columns,self.rows)
        if text!=self.last_source:self.preferred_column=None
        self.last_source=text
        bottom=max([r[3] for r in layout]+([caret[1]] if caret else [0]))
        self.max_scroll=max(0,bottom-self.rows+1)
        if caret and signature!=self.last_caret:
            if caret[1]<self.scroll:self.scroll=caret[1]
            elif caret[1]>=self.scroll+self.rows:self.scroll=max(0,caret[1]-self.rows+1)
        self.scroll=min(self.scroll,self.max_scroll);self.last_caret=signature
        cells=[]
        first,last=sorted((p['anchor'],p['caret'])) if p['anchor']>=0 else (-1,-1)
        for start,end,x,y,width,level,mapped in layout:
            y-=self.scroll
            if width==0 or y<0 or y>=self.rows or x+width>self.columns:continue
            cluster=text[start:end]
            if cluster.startswith('\t'):cluster=' '*width
            else:
                cluster=chr(mapped)+cluster[1:]
                cluster=''.join(c for c in cluster if ord(c)>=32 and not 0x7f<=ord(c)<=0x9f)
            background='67;99;127' if start<last and end>first else '11;18;27'
            cells.append((x,y+1,width,cluster,background))
        cursor=(min(caret[0],self.columns-1),caret[1]-self.scroll+1) if caret and 0<=caret[1]-self.scroll<self.rows else None
        return dict(title='NOCTURNE Unicode document'[:columns],cells=cells,cursor=cursor)
    def paint(self,scene,columns,rows):
        presentation=self.presentation(scene,columns,rows)
        if presentation is None:return None
        out=['\x1b[?25l\x1b[0m\x1b[2J\x1b[H',presentation['title']]
        for x,y,width,cluster,background in presentation['cells']:
            out.append(f'\x1b[{y+1};{x+1}H\x1b[38;2;228;218;204;48;2;{background}m'+cluster)
        if presentation['cursor']:
            x,y=presentation['cursor'];out.append(f'\x1b[{y+1};{x+1}H\x1b[?25h')
        return ''.join(out)
    def move(self,scene,key,shift=False):
        if key not in ('ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End','PageUp','PageDown'):return False
        p=self.state(scene)
        if p is None:return False
        text=scene.text_run_source(0,0)
        try:x,y,_=self.caret(scene,text,p)
        except ValueError:return False
        if key in ('ArrowUp','ArrowDown','PageUp','PageDown'):
            if self.preferred_column is None:self.preferred_column=x
            x=self.preferred_column
            step=max(1,self.rows) if key in ('PageUp','PageDown') else 1
            y+=-step if key in ('ArrowUp','PageUp') else step
        elif key=='Home':self.preferred_column=None;x=0
        elif key=='End':self.preferred_column=None;x=self.columns
        else:
            self.preferred_column=None
            x+=(-1 if key=='ArrowLeft' else 1 if key=='ArrowRight' else 0)
            y+=(-1 if key=='ArrowUp' else 1 if key=='ArrowDown' else 0)
        offset=scene.document_hit(text,self.columns,max(0,x),max(0,y))
        anchor=(p['anchor'] if p['anchor']>=0 else p['caret']) if shift else offset
        anchor=max(b for b in scene.document_boundaries(text) if b<=anchor)
        scene.command(dict(op='select',anchor=anchor,caret=offset,unit='grapheme'));return True
    def scroll_by(self,scene,delta):
        if self.state(scene) is None:return False
        self.scroll=max(0,min(self.max_scroll,self.scroll+delta));return True
    def cancel_drag(self):
        self.drag=None;self.drag_identity=None
    def capture_drag(self,scene,text,anchor):
        self.drag=anchor;rows=scene.text_run_clusters(0,0)
        if not rows:self.drag_identity=(0,0,0,'');return
        row=next((r for r in rows if r[1]==anchor),rows[-1]);edge=0 if row[1]==anchor else 1
        self.drag_identity=(row[0],row[3],edge,text[row[1]:row[2]])
    def resolve_drag(self,scene,text):
        if self.drag is None:return None
        identity,generation,edge,source=self.drag_identity
        if not identity:
            if text:self.cancel_drag();return None
            return 0
        for row in scene.text_run_clusters(0,0):
            if row[0]==identity and row[3]==generation and text[row[1]:row[2]]==source:
                self.drag=row[2] if edge else row[1];return self.drag
        self.cancel_drag();return None
    def pointer(self,scene,phase,x,y,shift):
        p=self.state(scene)
        if p is None:self.cancel_drag();return False
        if y<1:
            if phase=='up':self.cancel_drag()
            return True
        text=scene.text_run_source(0,0)
        offset=scene.document_hit(text,self.columns,max(0,x),max(0,y-1+self.scroll))
        if phase=='down':
            self.preferred_column=None
            anchor=(p['anchor'] if p['anchor']>=0 else p['caret']) if shift else offset
            anchor=max(b for b in scene.document_boundaries(text) if b<=anchor)
            self.capture_drag(scene,text,anchor)
        anchor=self.resolve_drag(scene,text)
        if anchor is not None:scene.command(dict(op='select',anchor=anchor,caret=offset,unit='grapheme'))
        if phase=='up':self.cancel_drag()
        return True
