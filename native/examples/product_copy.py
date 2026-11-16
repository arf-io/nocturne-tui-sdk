"""Product labels for authored demonstration data. Imported user data is untouched."""
import copy,re
NARRATION=re.compile(r'\b(?:original|recovered|restored|retained|first[ -]version)\b[ :/-]*',re.I)
VERSIONS=re.compile(r'\b(?:v?0\.\d+(?:\.\d+)?(?:-rc\.?\d+)?|RC[1-9]\d*)\b',re.I)
PHRASES=[r'full geometry\.?',r'no block substitutions\.?',r'no foreign controller',r'direct C components',r'coverage and glyph family remain stable[;,.]?',r'all data is synthetic\.?',r'light, motion, documents, and shared contracts\.?',r'eight-dot atelier',r'geometry uses all eight dots\.?',r'full text remains in metadata; overflow is an explicit policy\.?',r'the animation never delivers an external command\.?']
def clean_display_text(text):
 if not isinstance(text,str):return text
 out=VERSIONS.sub('',NARRATION.sub('',text))
 for phrase in PHRASES:out=re.sub(phrase,'',out,flags=re.I)
 out=re.sub(r'[ \t]{2,}',' ',out).strip(' /;,.:-')
 return out[:1].upper()+out[1:] if out else ''
def public_recipe(recipe):
 out=copy.deepcopy(recipe)
 if 'name' in out:out['name']=clean_display_text(out['name'])
 # Details live in controls and the reference, not narrative caption cards.
 if 'subtitle' in out:out['subtitle']=''
 def command_copy(command):
  if command.get('op') in {'widget','text','window','status','indicator','node'}:
   for key in ('text','title','label','detail'):
    if key in command:command[key]=clean_display_text(command[key])
  for child in command.get('commands',[]):command_copy(child)
  if isinstance(command.get('command'),dict):command_copy(command['command'])
 for command in out.get('commands',[]):command_copy(command)
 for action in out.get('actions',[]):
  if isinstance(action.get('command'),dict):command_copy(action['command'])
 return out
