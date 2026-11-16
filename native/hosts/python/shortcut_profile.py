"""Prompt Toolkit normalized shortcut map. No probing of OS key ownership.

Modifiers follow nr-shortcut-negotiation-v1. F1..F12 use 0x110001..0x11000c.
Ctrl-C remains an emergency host exit and is never offered for reassignment.
"""
FUNCTION=0x110000
ACTIONS={1:'Quit',2:'Hold',3:'Scene',4:'Copy',5:'Cut',6:'Paste',7:'Help',8:'Reader'}
PREFERENCES={1:[(ord('q'),2),(ord('q'),4)],2:[(FUNCTION+2,0),(FUNCTION+3,0)],
 3:[(FUNCTION+4,0),(FUNCTION+5,0)],4:[(ord('w'),4),(ord('c'),4)],
 5:[(ord('w'),2),(ord('x'),4)],6:[(ord('y'),2),(ord('v'),4)],
 7:[(FUNCTION+1,0),(FUNCTION+7,0)],8:[(FUNCTION+6,0),(FUNCTION+8,0)]}
def key_tokens(key,mod):
 if FUNCTION<key<=FUNCTION+12 and mod==0:return ('f'+str(key-FUNCTION),)
 if mod==2 and ord('a')<=key<=ord('z'):return ('c-'+chr(key),)
 if mod==4 and ord('a')<=key<=ord('z'):return ('escape',chr(key))
 raise ValueError('Unsupported Prompt Toolkit normalized chord')
def chord_label(key,mod):
 if FUNCTION<key<=FUNCTION+12:return 'F'+str(key-FUNCTION)
 return {2:'Ctrl+',4:'Alt+'}[mod]+chr(key)
class ShortcutProfile:
 def __init__(self,scene,reserved=()):
  chords=list(dict.fromkeys(chord for candidates in PREFERENCES.values() for chord in candidates))
  reserved=set(reserved)
  if not reserved.issubset(set(chords)):raise ValueError('Reservation is outside managed host shortcuts')
  host=[[key,mod,int((key,mod) in reserved)] for key,mod in chords]
  candidates=[[action,key,mod] for action,preferences in PREFERENCES.items() for key,mod in preferences]
  self.rows=scene.negotiate_shortcuts(list(ACTIONS),candidates,host)
  self.bindings=[(action,key_tokens(key,mod)) for action,key,mod,assigned in self.rows if assigned]
  self.hints=' | '.join(f'{ACTIONS[action]}: {chord_label(key,mod) if assigned else "unassigned"}' for action,key,mod,assigned in self.rows)
 def action_for(self,key,mod):
  return next((action for action,k,m,assigned in self.rows if assigned and (k,m)==(key,mod)),None)
def parse_reservations(labels):
 chords={chord_label(key,mod):(key,mod) for preferences in PREFERENCES.values() for key,mod in preferences}
 try:return [chords[label] for label in labels]
 except KeyError as error:raise ValueError('Unknown shortcut reservation: '+str(error.args[0])) from error
