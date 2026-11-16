#!/usr/bin/env python3
"""Stage the unchanged Gallery and verified current reference for GitHub Pages."""
from pathlib import Path,PurePosixPath
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import argparse,hashlib,html,importlib.util,json,re,shutil,stat,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2]
SDK_URL='https://github.com/arf-io/nocturne-tui-sdk/releases'
PUBLIC_SUFFIXES={'.md','.html','.pdf','.json','.png','.jpg','.jpeg','.webp','.svg','.css','.js','.mjs','.ts','.py','.c','.h','.go','.rs','.toml','.mod','.lock','.txt','.woff','.woff2'}
PRIVATE_NAMES={'BUILD.json','CAPTURES.json'}
PRIVATE_DIRS={'.git','history','logs','cache','profiles','node_modules','target','dist','manual'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def record(path):return {'bytes':path.stat().st_size,'sha256':sha(path)}
def name_path(name):
 if not isinstance(name,str) or not name or '\\' in name or '\x00' in name:raise ValueError('Unsafe path')
 q=PurePosixPath(name)
 if q.is_absolute() or any(x in ('','..','.') for x in q.parts) or q.as_posix()!=name:raise ValueError('Unsafe path: '+name)
 return q

def checked(root,name):
 q=name_path(name);p=root.joinpath(*q.parts)
 for part in [p,*list(p.parents)[:len(q.parts)-1]]:
  if part.is_symlink():raise ValueError('Symlink input: '+name)
 if not p.is_file():raise ValueError('Missing file: '+name)
 return p

def public_name(name):
 q=name_path(name)
 if any(x.startswith('.') or x.lower() in PRIVATE_DIRS for x in q.parts) or q.suffix.lower() not in PUBLIC_SUFFIXES:raise ValueError('Not a public asset: '+name)
 return q.name not in PRIVATE_NAMES

def external(url):
 u=urlsplit(url)
 if u.scheme!='https' or u.username or u.password or u.port not in (None,443) or not (u.hostname=='github.com' or (u.hostname or '').endswith('.github.io') or u.hostname=='nocturne.arf.io'):raise ValueError('External URL is not HTTPS GitHub: '+url)
 return True

class Links(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.links=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  for key,value in attrs:
   if not value:continue
   if key=='id' or tag=='a' and key=='name':self.ids.add(value)
   if key in ('href','src','action','poster'):self.links.append(value)
   if key=='srcset':self.links.extend(x.strip().split()[0] for x in value.split(',') if x.strip())
 handle_startendtag=handle_starttag

def validate_links(root):
 files={p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()};parsed={};count=0
 for name,p in files.items():
  if p.suffix not in ('.html','.md','.css','.js','.mjs','.json','.svg'):continue
  text=p.read_text();links=[];ids=set()
  if p.suffix in ('.html','.svg'):
   parser=Links();parser.feed(text);links+=parser.links;ids=parser.ids
  elif p.suffix=='.md':
   links+=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text)
   ids={re.sub(r'[^\w -]','',h.lower()).replace(' ','-') for h in re.findall(r'^#{1,6} (.+)$',text,re.M)}
  if p.suffix in ('.html','.css','.svg'):links+=re.findall(r'url\(\s*[\x22\x27]?([^\s)\x22\x27]+)',text)
  for url in re.findall(r'https?://[^\s<>\x22\x27)\\]+',text,re.I):external(html.unescape(url))
  for url in re.findall(r'[\x22\x27](//[^\s<>\x22\x27)]+)',text):external(html.unescape(url))
  parsed[name]=(links,ids)
 for name,(links,_) in parsed.items():
  for value in links:
   url=html.unescape(value).strip();u=urlsplit(url);count+=1
   if u.scheme in ('http','https') or u.netloc:external(url);continue
   if u.scheme:
    if u.scheme in ('data','blob') and files[name].suffix in ('.html','.svg'):continue
    raise ValueError('Unsafe link scheme: '+url)
   if '\\' in unquote(u.path) or unquote(u.path).startswith('/'):raise ValueError('Local link escapes site: '+url)
   target=(files[name].parent/unquote(u.path)).resolve() if u.path else files[name]
   if not target.is_relative_to(root.resolve()):raise ValueError('Local link escapes site: '+url)
   target_name=target.relative_to(root.resolve()).as_posix()
   if target_name not in files:raise ValueError('Missing local link '+url+' in '+name)
   if u.fragment and target.suffix in ('.html','.md','.svg') and unquote(u.fragment) not in parsed.get(target_name,([],set()))[1]:raise ValueError('Missing anchor '+url+' in '+name)
 return count

def reference_module():
 path=Path(__file__).with_name('build_reference_docs.py');spec=importlib.util.spec_from_file_location('github_site_reference',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def documentation_inputs(source,rendered):
 build=json.loads(checked(rendered,'BUILD.json').read_text())
 if build.get('schema')!='nocturne.reference-build.v1':raise ValueError('Documentation BUILD schema')
 manifest=checked(source,'manifest.json')
 if sha(manifest)!=build.get('manifestSha256'):raise ValueError('Documentation source hash: manifest.json')
 names=build.get('sources',{});assets=build.get('sourceAssets',{});outputs=build.get('outputs',{})
 if not names or not outputs or set(names)!=set(build.get('pageSources',[])):raise ValueError('Documentation inventory')
 for name,digest in {**names,**assets}.items():
  public_name(name);p=checked(source,name)
  if sha(p)!=digest:raise ValueError('Documentation source hash: '+name)
 for name,expected in outputs.items():
  public_name(name);p=checked(rendered,name)
  if record(p)!=expected:raise ValueError('Documentation output hash: '+name)
 reference_module().validate(source)
 return build,{name:checked(source,name) for name in [*names,*assets] if public_name(name)},{name:checked(rendered,name) for name in outputs if public_name(name)}

def public_captures(path):
 original=json.loads(path.read_text());rows=original.get('captures',[])
 keys=('component','state','label','image','pngSha256','cellSha256','nativeCellSha256','nativeWasmEqual','snapshotBytes','snapshotSha256','width','height','timeUs','build','schema')
 sources=[]
 for name,digest in original.get('sources',{}).items():
  if not re.fullmatch('[0-9a-f]{64}',digest):raise ValueError('Capture source hash')
  sources.append({'name':Path(name).name,'sha256':digest})
 derived={'schema':'nocturne.public-reference-captures.v1','originalSchema':original.get('schema'),'originalManifestSha256':sha(path),'scope':original.get('scope'),'captureCount':len(rows),'sourceArtifacts':sources,'captures':[{key:row[key] for key in keys if key in row} for row in rows]}
 return (json.dumps(derived,indent=2)+'\n').encode()

def inventory(root):
 result={}
 for p in sorted(root.rglob('*')):
  if p.is_symlink():raise ValueError('Symlink site asset')
  if p.is_file():result[p.relative_to(root).as_posix()]=record(p)
 return result

def verify(output):
 output=Path(output).resolve();root=output/'site';manifest_path=checked(root,'MANIFEST.json');manifest=json.loads(manifest_path.read_text())
 if manifest.get('schema')!='nocturne.github-site.v1':raise ValueError('Site manifest schema')
 expected=manifest.get('files',{});actual=inventory(root);actual.pop('MANIFEST.json',None)
 for name in expected:name_path(name)
 if set(actual)!=set(expected):raise ValueError('Site asset inventory differs')
 for name,row in actual.items():
  if row!=expected[name]:raise ValueError('Asset hash differs: '+name)
 if checked(output,'MANIFEST.json').read_bytes()!=manifest_path.read_bytes():raise ValueError('Manifest copy differs')
 external(manifest['sdkUrl']);links=validate_links(root)
 with zipfile.ZipFile(checked(output,'site.zip')) as archive:
  rows=archive.infolist();names=[x.filename for x in rows]
  if len(names)!=len(set(names)):raise ValueError('Duplicate ZIP member')
  if set(names)!=set(expected)|{'MANIFEST.json'}:raise ValueError('ZIP inventory differs')
  for row in rows:
   name_path(row.filename)
   if stat.S_ISLNK(row.external_attr>>16):raise ValueError('Symlink ZIP member')
   if archive.read(row)!=checked(root,row.filename).read_bytes():raise ValueError('ZIP bytes differ: '+row.filename)
 return {'files':len(expected)+1,'bytes':sum(x['bytes'] for x in actual.values())+manifest_path.stat().st_size,'zipBytes':(output/'site.zip').stat().st_size,'zipSha256':sha(output/'site.zip'),'manifestSha256':sha(manifest_path),'checkedLinks':links,'published':False}

def build(output,documentation_output,documentation_source=None,gallery=None,sdk_url=SDK_URL):
 output=Path(output).absolute();source=Path(documentation_source or ROOT/'docs/current').resolve();rendered=Path(documentation_output).resolve();gallery=Path(gallery or ROOT/'native/Nocturne-RC4-Source-Build.html').absolute()
 if output.exists() or output.is_symlink():raise ValueError('Output already exists')
 if gallery.is_symlink():raise ValueError('Symlink Gallery')
 external(sdk_url);doc,source_files,rendered_files=documentation_inputs(source,rendered);gallery_hash=sha(gallery);doc_hash=sha(rendered/'BUILD.json')
 output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='.github-site-',dir=output.parent) as temp:
  stage=Path(temp)/'bundle';site=stage/'site';site.mkdir(parents=True)
  shutil.copyfile(gallery,site/'gallery.html');(site/'.nojekyll').write_bytes(b'')
  index='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Nocturne</title><h1>Nocturne</h1><ul><li><a href="gallery.html">Gallery</a></li><li><a href="gallery.html#workshop-panel">Workshop</a></li><li><a href="docs/rendered/README.html">Reference</a></li><li><a href="docs/current/README.md">Markdown reference</a></li><li><a href="'+html.escape(sdk_url,quote=True)+'">SDK releases on GitHub</a></li></ul></html>\n'
  (site/'index.html').write_text(index)
  (site/'Nocturne-Gallery.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=gallery.html"><title>Nocturne Gallery</title><a href="gallery.html">Open Gallery and Workshop</a></html>\n')
  for prefix,inputs in [('docs/current',source_files),('docs/rendered',rendered_files)]:
   for name,path in inputs.items():
    destination=site/prefix/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
  capture=source/'images/CAPTURES.json'
  if capture.is_file():
   public=public_captures(capture)
   for prefix in ('docs/current','docs/rendered'):
    target=site/prefix/'images/CAPTURES.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(public)
  # Recheck consumed sources after copying; the public copy must match the original receipt.
  documentation_inputs(source,rendered)
  if sha(gallery)!=gallery_hash or sha(site/'gallery.html')!=gallery_hash or sha(rendered/'BUILD.json')!=doc_hash:raise ValueError('Inputs changed during staging')
  for prefix,inputs in [('docs/current',source_files),('docs/rendered',rendered_files)]:
   for name,path in inputs.items():
    if sha(site/prefix/name)!=sha(path):raise ValueError('Copied asset differs')
  validate_links(site)
  manifest={'schema':'nocturne.github-site.v1','sdkUrl':sdk_url,'inputs':{'gallerySha256':gallery_hash,'documentationBuildSha256':doc_hash},'files':inventory(site)}
  encoded=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode();(site/'MANIFEST.json').write_bytes(encoded);(stage/'MANIFEST.json').write_bytes(encoded)
  with zipfile.ZipFile(stage/'site.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
   for name in sorted([*manifest['files'],'MANIFEST.json']):
    info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(stat.S_IFREG|0o644)<<16;archive.writestr(info,(site/name).read_bytes())
  report=verify(stage);report['inputs']={'gallery':str(gallery),'documentationSource':str(source),'documentationOutput':str(rendered)};(stage/'BUILD-REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
  if output.exists():raise ValueError('Output already exists')
  stage.rename(output)
 return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--documentation-output',type=Path);p.add_argument('--documentation-source',type=Path);p.add_argument('--gallery',type=Path);p.add_argument('--sdk-url',default=SDK_URL);p.add_argument('--verify',action='store_true');a=p.parse_args()
 if not a.verify and a.documentation_output is None:p.error('--documentation-output is required for build')
 print(json.dumps(verify(a.output) if a.verify else build(a.output,a.documentation_output,a.documentation_source,a.gallery,a.sdk_url),indent=2))
if __name__=='__main__':main()
