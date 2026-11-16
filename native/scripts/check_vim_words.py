from pathlib import Path
import json,subprocess,tempfile,sys
sys.path.insert(0,str(Path.cwd()/'native/bindings/python'))
from nocturne_native import NativeScene
texts=['ab.cd 日本語','ab\n\ncd','\n\na','a\n\n',' \t ab  cd','éx y','x é','a','   ','a\n b\n\nc']
cases=[]
for text in texts:
 for caret in range(len(text)):
  if text[caret]=='\n' and caret and text[caret-1]!='\n':continue
  row=text[:caret].count('\n')+1;col=len(text[:caret].rsplit('\n',1)[-1].encode())+1
  for key in ['W','B','E']:cases.append((text,caret,key,row,col))
with tempfile.TemporaryDirectory() as tmp:
 out=Path(tmp)/'out';script=Path(tmp)/'script.vim';lines=['set encoding=utf-8','let result = []']
 for text,caret,key,row,col in cases:
  lines+=['enew!', 'call setline(1, '+json.dumps(text.split('\n'),ensure_ascii=False)+')',f'call cursor({row},{col})',f'normal! {key}',"call add(result, string(line('.')).','.string(col('.')))"]
 lines+=['call writefile(result, '+json.dumps(str(out))+')','qa!'];script.write_text('\n'.join(lines)+'\n')
 subprocess.run(['/usr/bin/vim','-Nu','NONE','-n','-es','-S',str(script)],check=True)
 positions=out.read_text().splitlines()
 if len(positions)!=len(cases):raise RuntimeError('Vim oracle output count mismatch')
 failures=[]
 with NativeScene() as s:
  for case,position in zip(cases,positions):
   text,caret,key,_,_=case;row,col=map(int,position.split(','));parts=text.split('\n');expected=sum(len(x)+1 for x in parts[:row-1])+len(parts[row-1].encode()[:col-1].decode())
   s.command(dict(op='prompt',mode='vim-full'));s.command(dict(op='draft',text=text,caret=caret,emitWeather=False));s.command(dict(op='key',key='Escape'));s.command(dict(op='key',key=key,unit='grapheme'));actual=s.info()['prompt']['caret']
   if actual!=expected:failures.append(dict(text=text,caret=caret,key=key,expected=expected,actual=actual))
 result=dict(oracle='Actual /usr/bin/vim 9.1 with -Nu NONE',cases=len(cases),failures=failures,passed=not failures)
 print(json.dumps(result,indent=2,ensure_ascii=False));sys.exit(bool(failures))
