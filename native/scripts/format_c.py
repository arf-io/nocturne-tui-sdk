#!/usr/bin/env python3
"""Whitespace-only formatter for the current C translation units.

Keeps strings, character literals, comments and preprocessing lines byte-intact.
Breaks top-level statements and braces so the reconstruction is inspectable.
The build/tests, not this formatter, establish C syntax and behavior.
"""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
TOKENS=re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*|^[ \t]*\#(?:[^\n\\]|\\.|\\\n)*|\s+|[^\s]',re.M)
def format_source(text):
 out=[];line='';depth=0;paren=0
 def flush():
  nonlocal line
  if line.strip():out.append('    '*max(depth,0)+line.strip())
  line=''
 tokens=list(TOKENS.finditer(text))
 for n,match in enumerate(tokens):
  t=match.group()
  if t.isspace():
   if line and not line.endswith(' '):line+=' '
   continue
  if t.lstrip().startswith('#'):
   flush();out.append(t.strip());continue
  if t.startswith('//')or t.startswith('/*'):
   flush();out.extend('    '*max(depth,0)+l for l in t.splitlines());continue
  if t.startswith(('"',"'"))and len(t)>1:line+=t;continue
  if t=='(':paren+=1
  elif t==')':paren-=1
  if t=='{':
   line=line.rstrip()+' {';flush();depth+=1
  elif t=='}':
   flush();depth-=1;line='}'
   nxt=next((m.group()for m in tokens[n+1:]if not m.group().isspace()),'')
   if nxt not in (';',',',')',']'):flush()
  elif t==';':
   line=line.rstrip()+';'
   if paren==0:flush()
   else:line+=' '
  else:line+=t
 flush();return '\n'.join(out)+'\n'
if __name__=='__main__':
 for path in sorted((ROOT/'src').glob('*.c'))+[(ROOT/'src/internal.h')]:
  old=path.read_text();new=format_source(old)
  # Except whitespace, every token must remain exactly the same.
  def nonspace(s):return [m.group()for m in TOKENS.finditer(s)if not m.group().isspace() and not m.group().startswith(('/*','//'))]
  assert nonspace(old)==nonspace(new),path
  path.write_text(new)
