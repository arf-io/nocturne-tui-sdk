#!/usr/bin/env python3
"""Compress embedded JSON for the 16 MiB artifact publisher; preserve every item."""
import argparse,base64,gzip,json,re
from pathlib import Path

DECODER='''async function decodeArtifactData(payload){
 const bytes=Uint8Array.from(atob(payload),c=>c.charCodeAt(0));
 const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
 return JSON.parse(await new Response(stream).text());
}
'''

def package_html(source):
 if 'NOCTURNE_GZIP_DATA' in source:raise ValueError('Artifact is already packaged')
 if '<script type="module">' in source and '\nconst recipes=' in source:
  start=source.index('\nconst recipes=')+len('\nconst recipes=')
  value,end=json.JSONDecoder().raw_decode(source[start:]);raw=source[start:start+end]
  if not isinstance(value,list) or not value or source[start+end:start+end+1]!=';':raise ValueError('Invalid recipe data')
  kind='gallery'
 elif '<script type="application/json" id="capture-index">' in source:
  match=re.search(r'(<script type="application/json" id="capture-index">)(.*?)(</script>)',source,re.S)
  if not match:raise ValueError('Missing captured data')
  raw=match[2];value=json.loads(raw)
  if not isinstance(value,list) or len(value)!=96:raise ValueError('Incomplete comparison data')
  kind='report'
 else:raise ValueError('Unknown artifact format')
 payload=base64.b64encode(gzip.compress(raw.encode(),mtime=0)).decode()
 if kind=='gallery':
  source=source[:start]+f'await decodeArtifactData("{payload}")'+source[start+end:]
  source=source.replace('<script type="module">','<script type="module">\n'+DECODER,1)
 else:
  source=source[:match.start(2)]+payload+source[match.end(2):]
  source=source.replace('<script type="application/json" id="capture-index">','<script type="application/octet-stream" id="capture-index">',1)
  source=source.replace('<script>','<script type="module">\n'+DECODER,1)
  expression="JSON.parse(document.querySelector('#capture-index').textContent)"
  if source.count(expression)!=1:raise ValueError('Unexpected report initialization')
  source=source.replace(expression,"await decodeArtifactData(document.querySelector('#capture-index').textContent)",1)
 source=source.replace('</html>','<!-- NOCTURNE_GZIP_DATA -->\n</html>',1)
 if len(source.encode())>16*1024*1024:raise ValueError('Packaged artifact still exceeds publisher limit')
 return source,raw

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
 result,_=package_html(args.source.read_text())
 with args.output.open('x') as destination:destination.write(result)
 print(args.output, len(result.encode()), 'bytes')

if __name__=='__main__':main()
