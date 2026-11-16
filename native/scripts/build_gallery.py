#!/usr/bin/env python3
"""Deterministically embed freshly built WASM and data into the source host template."""
from pathlib import Path
import argparse,base64,json,hashlib,sys,re
ROOT=Path(__file__).resolve().parents[1]
def readWorkshopMetadata(root=ROOT):
    data=json.loads((root/'web/workshop_fields.json').read_text())
    actual=hashlib.sha256((root/'bindings/typescript/contracts.ts').read_bytes()).hexdigest()
    if data.get('sourceSha256')!=actual:raise ValueError('Workshop metadata differs from current command interface; regenerate inventory')
    return data

def readWorkshopHelp(root=ROOT,metadata=None):
    metadata=metadata or readWorkshopMetadata(root)
    data=json.loads((root/'web/workshop_help.json').read_text())
    actual=hashlib.sha256((root/'bindings/typescript/contracts.ts').read_bytes()).hexdigest()
    if data.get('schema')!='nocturne.workshop-help.v1' or data.get('sourceSha256')!=actual or metadata.get('sourceSha256')!=actual:raise ValueError('Workshop guidance differs from current command interface')
    declared={row['op']+'.'+row['field'] for row in metadata['fields']}
    if not isinstance(data.get('parameters'),dict) or not set(data['parameters'])<=declared:raise ValueError('Workshop guidance names an undeclared field')
    return data

def nullifiedRecipes(recipes,path=None,strict=True,admission=True):
    """The Gallery library without what the operator's nullification contract strikes: every recipe or study that
    names a nullified catalogue identity, and every nullified recipe. Both Gallery builders take their library from
    here: this script's standalone page and build_gallery_site.py's HTTP bundle, which embeds that page. The attract
    rotation draws from the library (demoRecipes filters it in the page). A missing or invalid contract stops the
    build; it is never read as empty. Nothing is removed from the native core."""
    here=str(Path(__file__).resolve().parent)
    if here not in sys.path:sys.path.insert(0,here)
    import gallery_provenance,nullification
    # Provenance admission first (native/contract/GALLERY-ADMISSION.json): only original artwork, or RC4-era work the
    # operator admitted by name, enters the Gallery. A partial library (a feature filter) is admitted without the
    # completeness check; the complete library must hold every admitted id.
    if admission:recipes=gallery_provenance.admit(recipes,strict=strict)
    try:resolved=nullification.load_contract(ROOT.parent,path)
    except nullification.NullificationError as error:raise SystemExit(str(error)) from None
    return nullification.gallery_recipes(recipes,resolved)

HARNESS='Nocturne-Test-Harness.html'
def publicTreeFixtures(root=ROOT):
    """How many fixture generators the public tree left out (PUBLIC-TREE-REPORT.json at the tree root, written by
    tools/release/export_public_tree.py, which counts them and does not name them); 0 in a source tree. The shipped Gallery
    admits no fixture entry, so it builds the same either way; only the test harness, which holds every study, differs."""
    report=root.parent/'PUBLIC-TREE-REPORT.json'
    return json.loads(report.read_text())['fixtureGenerators']['count'] if report.is_file() else 0

def main(output=None,features=(),nullification=None,harness=False):
    """Build the Gallery (admitted artwork only) or, with harness=True, the test harness: the same template and WASM
    with every recipe and generated study, unfiltered, for the browser checks that execute study fixtures. The harness
    is a test artefact, never shipped or published as the Gallery. The default build writes both."""
    sys.path.insert(0,str(ROOT/'examples'))
    from gallery_cases import build_cases
    demonstrations=build_cases()
    if features:
        requested=set(features)
        available={case.get('demonstrates',{}).get('feature') for case in demonstrations}
        if not requested<=available:raise ValueError('Unknown gallery features: '+', '.join(sorted(requested-available)))
        demonstrations=[case for case in demonstrations if case.get('demonstrates',{}).get('feature') in requested]
    library=json.loads((ROOT/'recipes.json').read_text())+demonstrations
    recipes=library if harness else nullifiedRecipes(library,nullification,strict=not features);omitted=len(library)-len(recipes)
    template=(ROOT/'web/template.html').read_text()
    wasm=(ROOT/'dist/nocturne_native.wasm').read_bytes()
    source=(ROOT/'bindings/typescript/native_scene.mjs').read_text().replace('export { NativeScene };','')
    workshop=(ROOT/'bindings/typescript/workshop_composition.mjs').read_text()
    workshop=workshop.replace("import {NativeScene} from './native_scene.mjs';",'').replace('export async function','async function').replace('export function','function')
    template=template.replace('@@WORKSHOP_MODEL@@',workshop)
    composition=[]
    for name in ['composition_project.mjs','composition_codegen.mjs','composition_presets.mjs','composition_editor.mjs']:
        module=(ROOT/'bindings/typescript'/name).read_text()
        while module.startswith('import '):module=module.partition('\n')[2]
        module=re.sub(r'^export (?=(?:const|function|class)\b)','',module,flags=re.M)
        composition.append(module)
    template=template.replace('@@COMPOSITION_EDITOR@@','const {bindCompositionEditor,createProject,projectFromCommands,importProject,exportProject,prepareProject,generateProjectFiles,PROJECT_PRESETS,createPreset}=(()=>{\n'+'\n'.join(composition)+'\nreturn {bindCompositionEditor,createProject,projectFromCommands,importProject,exportProject,prepareProject,generateProjectFiles,PROJECT_PRESETS,createPreset};})();')

    modal=(ROOT/'bindings/typescript/source_modal.mjs').read_text()
    modal=re.sub(r'\bexport (?=(?:const|function|class)\b)','',modal)
    template=template.replace('@@SOURCE_MODAL@@','const {SOURCE_MODAL_KINDS,SourceModalController}=(()=>{\n'+modal+'\nreturn {SOURCE_MODAL_KINDS,SourceModalController};})();')
    scenic=(ROOT/'bindings/typescript/scenic_original.mjs').read_text()
    scenic=re.sub(r'\bexport (?=(?:const|function|class)\b)','',scenic)
    template=template.replace('@@SCENIC_ORIGINAL@@','const {ScenicOriginalSession,SCENIC_PRESETS,SCENIC_WORLD_FIELDS,SCENIC_DETAIL_FIELDS}=(()=>{\n'+scenic+'\nreturn {ScenicOriginalSession,SCENIC_PRESETS,SCENIC_WORLD_FIELDS,SCENIC_DETAIL_FIELDS};})();')
    metadata=readWorkshopMetadata()
    from workshop_help import scriptJSON
    template=template.replace('@@WORKSHOP_FIELDS@@',scriptJSON(metadata))
    helpData=readWorkshopHelp(ROOT,metadata)
    template=template.replace('@@WORKSHOP_HELP@@',scriptJSON(helpData))
    location=(ROOT/'bindings/typescript/gallery_location.mjs').read_text().replace('export function','function')
    template=template.replace('@@GALLERY_LOCATION@@',location)
    attract=re.sub(r'\bexport (?=(?:const|function|class)\b)','',(ROOT/'bindings/typescript/gallery_attract.mjs').read_text())
    if '@@GALLERY_ATTRACT@@' not in template:raise RuntimeError('Missing template token @@GALLERY_ATTRACT@@')
    template=template.replace('@@GALLERY_ATTRACT@@','const {GALLERY_SCENIC_FEATURES,isAttractRecipe,createAttractRotation,recipeProvenance}=(()=>{\n'+attract+'\nreturn {GALLERY_SCENIC_FEATURES,isAttractRecipe,createAttractRotation,recipeProvenance};})();')
    template=template.replace('@@CANVAS_BRAILLE@@',(ROOT/'bindings/typescript/canvas_braille.mjs').read_text().replace('export function','function'))
    template=template.replace('@@FONT_GALLERY@@',(ROOT/'bindings/typescript/font_gallery.mjs').read_text().replace('export function','function'))
    template=template.replace('@@OBJ_MODEL@@',(ROOT/'bindings/typescript/obj_model.mjs').read_text().replace('export function','function'))
    template=template.replace('@@OBJ_EXAMPLE@@',(ROOT/'tests/fixtures/source-model/continuity-example-mesh.mjs').read_text().replace('export const','const'))
    template=template.replace('@@GALLERY_RESOURCES@@',(ROOT/'bindings/typescript/gallery_resources.mjs').read_text().replace('export function','function'))
    pearlModules=[]
    for name in ['pearl_fleet_original.mjs','pearl_authored_data.mjs','pearl_data.mjs','pearl_stage.mjs','pearl_observatory_original.mjs','pearl_observatory_stage.mjs','pearl_observatory_audio.mjs']:
        module=(ROOT/'bindings/typescript'/name).read_text()
        module=re.sub(r'^import .*?;\n','',module,flags=re.M)
        module=re.sub(r'\bexport (?=(?:const|function|class)\b)','',module)
        pearlModules.append(module)
    template=template.replace('@@PEARL_DATA@@','const {StudioDataSource,observatorySample,PearlStageSession,PearlObservatoryOriginal,PearlObservatorySession,createObservatoryAudio}=(()=>{\n'+'\n'.join(pearlModules)+'\nreturn {StudioDataSource,observatorySample,PearlStageSession,PearlObservatoryOriginal,PearlObservatorySession,createObservatoryAudio};})();')
    import gallery_provenance
    examples=gallery_provenance.workshop_examples(json.loads((ROOT/'recipes.json').read_text()))
    examples=[] if harness else [r for r in examples if r['id'] in {x['id'] for x in nullifiedRecipes(examples,nullification,strict=False,admission=False)}]
    for key,value in {'@@BUILD@@':json.loads((ROOT.parent/'RELEASE.json').read_text())['build'],'@@BINDING@@':source,'@@RECIPES@@':json.dumps(recipes,separators=(',',':')),'@@WORKSHOP_EXAMPLES@@':json.dumps(examples,separators=(',',':')),'@@PALETTES@@':json.dumps(json.loads((ROOT/'palettes.json').read_text()),separators=(',',':')),'@@WASM@@':base64.b64encode(wasm).decode(),'@@WASM_SHA256@@':hashlib.sha256(wasm).hexdigest()}.items():
        if key not in template:raise RuntimeError(f'Missing template token {key}')
        template=template.replace(key,value)
    destination=Path(output) if output is not None else ROOT/(HARNESS if harness else 'Nocturne-RC4-Source-Build.html')
    destination.write_text(template)
    if output is None and not harness:(ROOT.parent/'Nocturne-RC4.html').write_text(template)
    print(destination.name,destination.stat().st_size,'bytes; embedded WASM SHA-256',hashlib.sha256(wasm).hexdigest()+('; test harness with every study'+('' if not publicTreeFixtures() else ' present in this tree, without the '+str(publicTreeFixtures())+' fixture generators it leaves out') if harness else '; '+str(len(recipes))+' admitted artworks, '+str(omitted)+' entries not admitted (provenance admission and nullification)'))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Write one gallery here, preserving the default gallery files')
    parser.add_argument('--feature',action='append',default=[],help='Include this study feature (repeatable; default includes all)')
    parser.add_argument('--nullification',type=Path,help='Operator nullification contract (default native/contract/NULLIFICATION.json)')
    parser.add_argument('--harness',action='store_true',help='Build only the test harness (every study, no admission)')
    args=parser.parse_args()
    if args.harness:main(args.output,args.feature,args.nullification,harness=True)
    else:
        main(args.output,args.feature,args.nullification)
        if args.output is None and not args.feature:
            if publicTreeFixtures():print('test harness not built: this public tree leaves out the fixture studies it holds (build_gallery.py --harness builds one without them)')
            else:main(None,(),args.nullification,harness=True)
