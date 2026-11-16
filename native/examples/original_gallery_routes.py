"""Route catalogue identities to their current native source recipes."""
import copy

ORIGINAL_BACKGROUNDS = ("linear", "double-axis", "wave", "plasma", "caustics",
                       "vortex", "contours", "aurora", "woven", "moire",
                       "tunnel", "diamond", "bilinear", "checker", "warp")

def apply_original_gallery_routes(cases, catalogue):
    from atelier_windows import atelier_window_application_commands
    by_id = {case["id"]: case for case in cases}
    additions = []
    for entry in catalogue:
        source = entry.get("sourceIdentity") or ""
        if entry['contract']=='SurfaceField':
            for mode in ('isolated','application'):
                identity='study-'+entry['id'].replace('/','-')+'-'+mode
                case=by_id[identity];legacy=copy.deepcopy(case)
                legacy.update(id=identity+'-legacy',name=case['name']+' / legacy',demo=False)
                additions.append(legacy)
                field=next(c for c in case['commands'] if c['op']=='field' and c['effect']==entry['id'])
                for key in ('width','speed','lifeMs','strength'):field.pop(key,None)
                field['optics']='source';field['paint']='source';case.update(catalogueEffect=entry['id'],sourceIdentity=source)
            continue
        if source.startswith('window/atelier/'):
            effect=source.rsplit('/',1)[1]
            for mode in ('isolated','application'):
                identity='study-'+entry['id'].replace('/','-')+'-'+mode
                case=by_id[identity];compact=copy.deepcopy(case)
                compact.update(id=identity+'-compact',name=case['name']+' / compact',demo=False)
                additions.append(compact)
                case.update(commands=atelier_window_application_commands(effect),viewport={'width':136,'height':44},originalEffect=effect,catalogueEffect=entry['id'],sourceIdentity=source,autoActions=True,sampleTimesUs=[1425000,3425000],actions=[{'timeUs':1000000,'command':{'op':'window-action','id':1,'action':'minimize'}},{'timeUs':3000000,'command':{'op':'window-action','id':1,'action':'restore'}}],provenance={'release':'Atelier v0.5','component':'Original complete Atelier window application','htmlSha256':'01500ccd3106f40a7f0b3e21fe4a580f1e0666980e998930feaf94bff730aced'})
            continue
        if not source.startswith(("window/kinetic/", "text/kinetic/", "text/atelier/")):
            continue
        for mode in ("isolated", "application"):
            identity = "study-" + entry["id"].replace("/", "-") + "-" + mode
            case = by_id[identity]
            if source.startswith("window/"):
                compact = copy.deepcopy(case)
                compact.update(id=identity+"-compact", name=case["name"]+" / compact", demo=False)
                compact["demonstrates"] = {"feature":"compact-window", "effect":entry["id"], "contract":entry["contract"]}
                additions.append(compact)
                original = by_id["rc2-window-"+source.rsplit("/",1)[1]+"-"+mode]
                retained = {"id":identity, "name":case["name"], "demonstrates":case["demonstrates"]}
                case.clear();case.update(copy.deepcopy(original));case.update(retained)
            case.update(catalogueEffect=entry["id"], sourceIdentity=source)
            if source.startswith("text/atelier/"):
                target=next(c for c in case['commands'] if c['op']=='text' and c['id']==1)
                target.update(phaseModel='source-paint',durationMs=1200,material=15,seed=6137,alphabet=' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!?+-*/')
            if source.startswith("text/"):
                case["viewport"] = {"width":100,"height":40}
    original = by_id["rc2-windows-application"]
    for style in ORIGINAL_BACKGROUNDS:
        case=copy.deepcopy(original)
        case.update(id="original-background-"+style, name="Background / "+style,
                    originalBackground=style, demo=True,
                    demonstrates={"feature":"original-background","style":style})
        case["provenance"]["component"]="Kinetic background / "+style
        next(c for c in case["commands"] if c["op"]=="window-application")["backgroundStyle"]=style
        additions.append(case)
    return cases+additions
