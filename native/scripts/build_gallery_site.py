"""Build a complete HTTP gallery bundle; preserve the standalone builder.

The library is the one the standalone page embeds: native/recipes.json and the generated studies passed through
build_gallery.nullifiedRecipes, the Gallery's choke point for the operator's nullification contract, so the bundle
omits what the contract strikes (native/docs/NULLIFICATION.md). Nothing is removed from the native core."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import tempfile
import sys
from build_gallery import main as standalone,nullifiedRecipes
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--nullification',type=Path,help='Operator nullification contract (default native/contract/NULLIFICATION.json)');a=p.parse_args()
    output=a.output.resolve()
    if output.exists():p.error('Output already exists')
    sys.path.insert(0,str(ROOT/'examples'));from gallery_cases import build_cases
    library=json.loads((ROOT/'recipes.json').read_text())+build_cases()
    recipes=nullifiedRecipes(library,a.nullification);omitted=len(library)-len(recipes)
    if len({r['id'] for r in recipes})!=len(recipes):raise ValueError('Duplicate recipe identities')
    encoded=json.dumps(recipes,separators=(',',':'));limit=8*1024*1024
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        stage=Path(temp);source=stage/'standalone.html';standalone(output=source,nullification=a.nullification)
        html=source.read_text();source.unlink();scripts=['<script>window.nocturneRecipeAssets=[];</script>'];chunk=[];size=0;index=0
        def emit(rows,number):
            name=f'recipes-{number:03d}.js';data=('window.nocturneRecipeAssets.push(...'+json.dumps(rows,separators=(',',':'))+');\n').encode()
            if len(data)>=16*1024*1024:raise ValueError('Recipe asset exceeds publishing limit')
            (stage/name).write_bytes(data);integrity=base64.b64encode(hashlib.sha256(data).digest()).decode()
            scripts.append(f'<script src="{name}" integrity="sha256-{integrity}"></script>')
        for recipe in recipes:
            entrySize=len(json.dumps(recipe,separators=(',',':')).encode())+1
            if chunk and size+entrySize>limit:emit(chunk,index);chunk=[];size=0;index+=1
            chunk.append(recipe);size+=entrySize
        if chunk:emit(chunk,index)
        token='const recipes='+encoded+';'
        if token not in html:raise ValueError('Standalone recipe token differs')
        guard=f'''if(!Array.isArray(window.nocturneRecipeAssets)||window.nocturneRecipeAssets.length!=={len(recipes)}){{document.getElementById('error').textContent='Gallery recipe assets could not be verified. Reload the complete bundle.';throw Error('Incomplete recipe assets');}}
const recipes=window.nocturneRecipeAssets;'''
        html=html.replace(token,guard,1).replace('<script type="module">','\n'.join(scripts)+'\n<script type="module">',1)
        (stage/'gallery.html').write_text(html)
        files={path.name:{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(stage.iterdir())}
        if any(record['bytes']>=16*1024*1024 for record in files.values()):raise ValueError('Bundle file exceeds publishing limit')
        manifest={'schema':'nocturne.gallery-site.v1','recipes':len(recipes),'wasmSha256':hashlib.sha256((ROOT/'dist/nocturne_native.wasm').read_bytes()).hexdigest(),'files':files,'scope':'Complete current recipe library and workshop; not every parameter combination or final SDK qualification'}
        if omitted:manifest.update(nullifiedRecipes=omitted,scope='Current recipe library and workshop without the '+str(omitted)+' recipes the nullification contract strikes; not every parameter combination or final SDK qualification')
        (stage/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');stage.rename(output)
    print(json.dumps({'output':str(output),'recipes':len(recipes),'files':len(files),**({'nullifiedRecipes':omitted} if omitted else {})}))
if __name__=='__main__':main()
