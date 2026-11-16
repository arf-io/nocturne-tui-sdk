"""Capability-negotiated app commands; hosts own key normalization and delivery.

No keyboard or terminal is opened by this example. The host supplies its actual
capability table, may reserve shell/OS chords, and calls dispatch on normalized
input. The same assignment table drives the displayed help and input routing.
"""
class ShortcutApplication:
    SAVE,REFRESH,CLOSE=1,2,3
    def __init__(self,scene,host):
        self.scene=scene;self.saved=None;self.closed=False;self.refreshes=0
        self.assignments=scene.negotiate_shortcuts([self.SAVE,self.REFRESH,self.CLOSE],
            [[self.SAVE,ord('s'),2],[self.SAVE,ord('s'),8],
             [self.REFRESH,ord('r'),2],[self.REFRESH,ord('r'),8],
             [self.CLOSE,ord('q'),2],[self.CLOSE,ord('q'),8]],host)
        labels=[]
        for action,key,mod,assigned in self.assignments:
            name={self.SAVE:'Save',self.REFRESH:'Refresh',self.CLOSE:'Close'}[action]
            chord='+'.join([n for bit,n in [(1,'Shift'),(2,'Ctrl'),(4,'Alt'),(8,'Meta')] if mod&bit]+[chr(key)]) if assigned else 'unassigned'
            labels.append(f'{name}: {chord}')
        scene.command(dict(op='window',id=1,title='Application shortcuts',text='\n'.join(labels)))
    def dispatch(self,key,modifiers):
        action=next((a for a,k,m,assigned in self.assignments if assigned and k==key and m==modifiers),None)
        if action==self.SAVE:self.saved=self.scene.text_run_source(0,0)
        elif action==self.REFRESH:self.refreshes+=1
        elif action==self.CLOSE:self.closed=True
        else:return False
        return True
