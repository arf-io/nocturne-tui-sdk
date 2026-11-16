#!/usr/bin/env python3
"""Compiler dependencies, linked imports and import-free WASM; not full process tracing."""
from pathlib import Path
import hashlib,json,subprocess,sys,os,shlex
from toolchain import discover
from release_archive import _path as archivePath, _object as manifestObject
ROOT=Path(__file__).resolve().parents[1]

# These exact compiler-generated guards remain within the existing libc memory
# dependency boundary. Do not accept arbitrary *_chk or __* names: fortified I/O
# and process functions would still introduce a forbidden host dependency.
MEMORY_FUNCTIONS=frozenset({'bcmp','memcmp','memcpy','memmove','memset','strcmp','strlen','strncmp','strrchr'})
COMPILER_MEMORY_GUARDS=frozenset({'__memcpy_chk','__memmove_chk','__memset_chk','__stack_chk_fail'})
# Exact Apple compiler memory fills, stack probe, and stack-canary data import.
DARWIN_MEMORY_RUNTIME=frozenset({'bzero','memset_pattern16','__chkstk_darwin','__stack_chk_guard'})
def allowedSymbols():
 return MEMORY_FUNCTIONS|COMPILER_MEMORY_GUARDS|(DARWIN_MEMORY_RUNTIME if sys.platform=='darwin' else frozenset())

def compilerSdkSettings(cc):
 # Use the SDK selected by the actual compiler, not xcrun's default.
 trace=subprocess.run([cc,'-###','-c',str(ROOT/'src/math.c')],capture_output=True,text=True,check=True)
 for line in trace.stderr.splitlines():
  words=shlex.split(line)
  if '-cc1' in words and '-isysroot' in words:
   return (Path(words[words.index('-isysroot')+1])/'SDKSettings.json').resolve()
 raise RuntimeError('Compiler did not report its Darwin SDK')

def inspectNativeSymbols(library):
 # Linux/AArch64 imports the canary as data. A same-named function is not allowed.
 elfImportTypes={};elfCanaryRelocations=[]
 if sys.platform.startswith('linux'):
  table=subprocess.run(['readelf','--dyn-syms','--wide',str(library)],capture_output=True,text=True,check=True)
  for line in table.stdout.splitlines():
   words=line.split()
   if len(words)>=8 and words[6]=='UND':elfImportTypes[words[7].split('@')[0]]=words[3]
  relocations=subprocess.run(['readelf','--relocs','--wide',str(library)],capture_output=True,text=True,check=True)
  for line in relocations.stdout.splitlines():
   words=line.split()
   if len(words)>=5 and any(word.split('@')[0]=='__stack_chk_guard' for word in words[3:]):elfCanaryRelocations.append(words[2])
 r=subprocess.run(['nm','-u',str(library)],capture_output=True,text=True,check=True)
 symbols=[];errors=[]
 for line in r.stdout.splitlines():
  parts=line.split()
  if (len(parts)>1 and parts[-2]=='U') or (sys.platform=='darwin' and len(parts)==1 and parts[0].startswith('_')):
   name=parts[-1].split('@')[0]
   if sys.platform=='darwin':name=name.removeprefix('_')
   symbols.append(name)
   canaryData=sys.platform.startswith('linux') and name=='__stack_chk_guard' and elfImportTypes.get(name)=='OBJECT' and bool(elfCanaryRelocations) and all(kind in {'R_AARCH64_GLOB_DAT','R_X86_64_GLOB_DAT'} for kind in elfCanaryRelocations)
   if name not in allowedSymbols() and not canaryData:errors.append('Unexpected linked function: '+name)
 return {'symbols':symbols,'elfImportTypes':elfImportTypes,'elfCanaryRelocations':elfCanaryRelocations,'compilerCanaryData':[name for name in symbols if name=='__stack_chk_guard' and elfImportTypes.get(name)=='OBJECT'],'compilerMemoryGuards':[name for name in symbols if name in COMPILER_MEMORY_GUARDS],'errors':errors}

def shadowExports(names):
 # Shadow-check builds (NOCTURNE_SHADOW_CHECK, test only) export nrShadow* functions; a shipped artefact must not.
 return sorted(name for name in names if name.startswith('nrShadow'))

def nativeDefinedSymbols(library):
 # The library's defined dynamic symbols, for the shadow-export check.
 argv=['nm','-gU',str(library)] if sys.platform=='darwin' else ['nm','-D','--defined-only',str(library)]
 r=subprocess.run(argv,capture_output=True,text=True,check=True)
 names=[line.split()[-1].split('@')[0] for line in r.stdout.splitlines() if len(line.split())>=2]
 return [name.removeprefix('_') for name in names] if sys.platform=='darwin' else names

def originalSourceFiles(repository):
 # Prefer this exact checkout's index; never inherit a parent repository index
 # or use an archive manifest to admit an untracked checkout dependency.
 try:
  top=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=repository,capture_output=True,text=True)
 except FileNotFoundError:
  top=None
 if top is not None and top.returncode==0 and Path(top.stdout.strip()).resolve()==repository:
  tracked=subprocess.run(['git','ls-files','--stage','-z','--','src','include'],
                         cwd=repository,capture_output=True,text=True,check=True)
  sources={}
  for entry in tracked.stdout.split('\0'):
   if not entry:continue
   metadata,name=entry.split('\t',1);mode,blob,stage=metadata.split()
   candidate=repository/name
   if stage=='0' and mode in {'100644','100755'} and candidate.is_file() and not candidate.is_symlink() and candidate.resolve()==candidate:
    sources[candidate]=None
  return sources
 marker=repository/'.git'
 if marker.exists() or marker.is_symlink():raise ValueError('Own Git source index unavailable')
 # A verified SDK extraction has a canonical payload manifest and history
 # bundle, but no checkout index. The manifest is integrity data, not a signature.
 manifestPath=repository/'MANIFEST.json'
 if not manifestPath.is_file() or manifestPath.is_symlink() or manifestPath.resolve()!=manifestPath:
  raise ValueError('Missing or unsafe source dependency manifest')
 if manifestPath.stat().st_size>16*1024**2:raise ValueError('Oversized manifest')
 manifest=json.loads(manifestPath.read_text(),object_pairs_hook=manifestObject)
 files=manifest.get('files') if isinstance(manifest,dict) else None
 if not isinstance(files,dict) or not files:raise ValueError('Nonempty payload manifest required')
 sources={}
 for relative,entry in files.items():
  parts=archivePath('nocturne-sdk/'+relative).parts[1:]
  if relative=='MANIFEST.json':raise ValueError('Manifest cannot list itself')
  if not isinstance(entry,dict) or type(entry.get('bytes')) is not int or entry['bytes']<0:raise ValueError('Invalid payload size')
  digest=entry.get('sha256')
  if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('Invalid SHA-256 field')
  if len(parts)>1 and parts[0] in {'src','include'}:
   candidate=repository.joinpath(*parts)
   verifyManifestSource(candidate,entry)
   sources[candidate]=entry
 return sources

def verifyManifestSource(path,entry):
 if not path.is_file() or path.is_symlink() or path.resolve()!=path:raise ValueError('Manifest source missing or unsafe: '+str(path))
 data=path.read_bytes()
 if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Manifest source integrity mismatch: '+str(path))

def compilerSourceClosure(cc,root=ROOT):
 root=Path(root).resolve();repository=root.parent
 paths=set();errors=[];sdkMetadata=set();rootSources=originalSourceFiles(repository)
 sdkSettings=compilerSdkSettings(cc) if sys.platform=='darwin' else None
 for source in sorted((root/'src').glob('*.c')):
  if source.name=='wasm_mem.c':continue
  r=subprocess.run([cc,'-MM','-Iinclude','-Isrc',str(source)],cwd=root,capture_output=True,text=True,check=True)
  words=r.stdout.replace('\\\n',' ').split(':',1)[1].split()
  for path in words:
   resolved=(root/path).resolve()
   if resolved==sdkSettings:sdkMetadata.add(resolved)
   elif resolved.is_relative_to(root) or (resolved in rootSources and resolved==Path(os.path.abspath(root/path))):paths.add(resolved)
   else:errors.append('External source dependency: '+str(resolved))
 # Recheck archive identities after the compiler has consumed their bytes.
 for path,entry in rootSources.items():
  if entry is not None:verifyManifestSource(path,entry)
 return {'sources':[{'path':Path(os.path.relpath(p,root)).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(paths)],
         'compilerSdkMetadata':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(sdkMetadata)],
         'errors':errors}

def main(output=None):
 cc=discover()['cc'];closure=compilerSourceClosure(cc,ROOT);errors=list(closure['errors'])
 node=subprocess.run(['node','--input-type=module','-e',"import fs from 'node:fs';const m=new WebAssembly.Module(fs.readFileSync(process.argv[1]));console.log(JSON.stringify({imports:WebAssembly.Module.imports(m),exports:WebAssembly.Module.exports(m).map(e=>e.name)}))",str(ROOT/'dist/nocturne_native.wasm')],capture_output=True,text=True,check=True)
 module=json.loads(node.stdout);imports=module['imports']
 if imports:errors.append('WASM has imports')
 errors.extend('Shadow-check export: '+name for name in shadowExports(module['exports']))
 lib=ROOT/'dist'/('libnocturne_native.dylib'if sys.platform=='darwin'else'libnocturne_native.so')
 if os.environ.get('NOCTURNE_COVERAGE')=='1':lib=lib.parent/'dependency-audit'/lib.name
 linked=inspectNativeSymbols(lib);symbols=linked['symbols'];errors.extend(linked['errors'])
 errors.extend('Shadow-check export: '+name for name in shadowExports(nativeDefinedSymbols(lib)))
 nativeOnly=[]
 payload=b'{"op":"input","text":"no subprocess required"}\n'
 for label,argv in [('python',[sys.executable,str(ROOT/'scripts/replay.py')]),('go',[str(ROOT/'dist/go-replay')])]:
  r=subprocess.run(argv,cwd=ROOT,input=payload,capture_output=True,env={**os.environ,'PATH':''},timeout=30)
  nativeOnly.append({'language':label,'exitCode':r.returncode,'records':len(r.stdout.splitlines())})
  if r.returncode:errors.append(label+' failed with empty PATH')
 result={'auditedLibrary':{'path':str(lib),'sha256':hashlib.sha256(lib.read_bytes()).hexdigest(),'coverageInstrumented':False},'scope':'Current C compiler source closure, native undefined symbols including exact compiler memory guards, zero WASM imports, direct native clients with empty PATH. Not full OS tracing or historical visual approval.','sources':closure['sources'],'compilerSdkMetadata':closure['compilerSdkMetadata'],'nativeUndefinedSymbols':symbols,'compilerMemoryGuards':linked['compilerMemoryGuards'],'allowedNativeFunctions':sorted(allowedSymbols()),'darwinMemoryRuntimeSymbols':[name for name in symbols if name in DARWIN_MEMORY_RUNTIME],'wasmImports':imports,'nativeClientsWithoutExecutableSearchPath':nativeOnly,'errors':errors,'passed':not errors}
 (Path(output) if output is not None else ROOT/'evidence/dependencies.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if not errors else 2
if __name__=='__main__':raise SystemExit(main())
