"""Explicit RC2 human-copy supersession; never edits retained original files.

The original renderer and all geometry remain intact. Only named literal display
copy changes in the in-memory reference program, before it paints any cells.
"""
REPLACEMENTS={
 'kinetic':[
  ('NOCTURNE / KINETIC       VOL V · 0.5       ${Math.round(o.fps)} FPS · OKLCh','NOCTURNE / KINETIC · ${Math.round(o.fps)} FPS · OKLCh'),
  ("'WINDOW THEATRE / spatial glass'","'WINDOW THEATRE'"),
  ("'SHAPES / beyond the rectangle'","'SHAPES'"),
  ("this.notice = KINETIC_SCENES.find(s => s.id === scene).name + ' / v0.5';","this.notice = KINETIC_SCENES.find(s => s.id === scene).name + '';"),
 ],
 'atelier':[
  ('v${ATELIER_VERSION}   ${Math.round(o.fps)} FPS TARGET   OKLCh','${Math.round(o.fps)} FPS TARGET   OKLCh'),
  ('Spatial glass, shaped surfaces, large tools and a recovery dock.','Windows, surfaces and tools.'),
  ('INPUT IS IMMEDIATE  /  SPACE pause on stage  /  H home  /  ? controls','SPACE pause on stage  /  H home  /  ? controls'),
 ]}
def current_presentation(source,kind):
 for old,new in REPLACEMENTS[kind]:
  if source.count(old)!=1:raise AssertionError('Pinned human-copy literal changed: '+repr(old))
  source=source.replace(old,new,1)
 return source


def assert_current_chrome(test,actual,historical,width,height,kind):
 """Archived snapshots keep exact art; only enumerated caption spans changed.

 Live-source tests paint all current cells through the independent original
 renderer with the literal bridge above. Here exact old/new glyph assertions
 bound the exception to caption spans; geometry and ownership stay word-exact.
 """
 import array,re
 a=array.array('I');a.frombytes(bytes(actual));b=array.array('I');b.frombytes(bytes(historical))
 test.assertEqual(len(a),width*height*4);test.assertEqual(len(a),len(b))
 def row(y):return ''.join(chr(b[(y*width+x)*4])for x in range(width))
 spans=[]
 if kind=='kinetic':
  match=re.match(r'NOCTURNE / KINETIC       VOL V · 0\.5       (\d+) FPS · OKLCh',row(1)[2:])
  test.assertIsNotNone(match,'Historical header must have the exact superseded format')
  spans.append((2,1,match.group(0),'NOCTURNE / KINETIC · '+match.group(1)+' FPS · OKLCh'))
  footer=row(height-2)[3:]
  old=next((x for x in ['WINDOW THEATRE / spatial glass / v0.5','SHAPES / beyond the rectangle / v0.5']if footer.startswith(x)),None)
  test.assertIsNotNone(old,'Historical footer must identify the changed caption')
  spans.append((3,height-2,old,'SHAPES' if old.startswith('SHAPES')else'WINDOW THEATRE'))
 elif kind=='stage':
  spans.append((1,0,'NOCTURNE RC4 | F1 Help | F6 Reader | Input is immediate','NOCTURNE | F1 Help | F6 Reader'))
 elif kind=='atelier':
  if width>100:
   match=re.match(r'v0\.5\.0   (\d+) FPS TARGET   OKLCh',row(1)[width-54:])
   test.assertIsNotNone(match,'Historical Atelier version header required')
   spans.append((width-54,1,match.group(0),match.group(1)+' FPS TARGET   OKLCh'))
  spans.extend([(2,3,'Spatial glass, shaped surfaces, large tools and a recovery dock.','Windows, surfaces and tools.'),(3,height-2,'INPUT IS IMMEDIATE  /  SPACE pause on stage  /  H home  /  ? controls','SPACE pause on stage  /  H home  /  ? controls')])
 else:raise AssertionError('Unknown presentation family')
 permitted=set()
 for x,y,old,new in spans:
  old=old[:width-x-2];new=new[:width-x-2]
  start=y*width+x
  test.assertEqual(''.join(chr(b[(start+i)*4])for i in range(len(old))),old)
  test.assertEqual(''.join(chr(a[(start+i)*4])for i in range(len(new))),new)
  for i in range(max(len(old),len(new))):
   cell=start+i;permitted.add(cell)
   test.assertEqual(a[cell*4+3],b[cell*4+3],'Display copy must not change ownership')
   if i<len(new):test.assertEqual(a[cell*4+1:cell*4+3],b[cell*4+1:cell*4+3],'Changed caption keeps the original source colors')
   if i>=len(new):test.assertFalse(chr(a[cell*4]).isalnum(),'Removed caption must expose its background')
 differences=[i for i in range(len(a))if i//4 not in permitted and a[i]!=b[i]]
 test.assertEqual(differences,[],str(differences[:16]))


def assert_snapshot_presentation(test,scene,historical):
 frame=scene.render();application=scene.info().get('windowApplication')
 kind='stage' if not application else 'atelier' if application['scene']=='atelier-windows' else 'kinetic'
 assert_current_chrome(test,frame.bytes,historical,frame.width,frame.height,kind)
