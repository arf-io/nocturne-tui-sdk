#!/usr/bin/env python3
"""Lossless canonical-cell inspection plus full-resolution PNGs and review MP4.

PNG rendering is a controlled raster of actual framework cell surfaces where
available, not a screenshot of a physical terminal. PTY capture is separate.
Every planned tick is retained; H.264 MP4 is a lossy convenience, never an oracle.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, re, shutil, struct, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def decodeViewAnsi(text,width,height):
    """Strict reader for this SDK's View output, not an arbitrary terminal emulator."""
    out=np.zeros((height,width,4),dtype='<u4');out[:,:,0]=32
    x=y=0;fg=0xffffff;bg=0;i=0
    while i<len(text):
        if text[i]=='\x1b':
            m=re.match(r'\x1b\[([0-9;]*)m',text[i:])
            if not m:raise ValueError('Unexpected control sequence in framework View')
            ns=[int(v) for v in m.group(1).split(';') if v];j=0
            while j<len(ns):
                if ns[j]==0:fg=0xffffff;bg=0;j+=1
                elif ns[j] in (38,48) and ns[j+1:j+2]==[2] and j+4<len(ns):
                    val=(ns[j+2]<<16)|(ns[j+3]<<8)|ns[j+4]
                    if ns[j]==38:fg=val
                    else:bg=val
                    j+=5
                else:raise ValueError('Unsupported SGR in View contract')
            i+=len(m.group(0));continue
        ch=text[i];i+=1
        if ch=='\n':x=0;y+=1;continue
        if x>=width or y>=height:raise ValueError('View geometry overflow')
        out[y,x,:3]=(ord(ch),fg,bg);x+=1
    return out.tobytes()

def materializeAnsi(directory):
    for p in directory.rglob('*.ansi'):
        m=json.loads(p.with_suffix('.json').read_text());p.with_suffix('.cells').write_bytes(decodeViewAnsi(p.read_text(),m['width'],m['height']))

def readFrame(file):
    meta=json.loads(file.with_suffix('.json').read_text());w,h=meta['width'],meta['height'];raw=file.read_bytes()
    if not isinstance(w,int)or not isinstance(h,int)or not 1<=w<=512 or not 1<=h<=256 or len(raw)!=w*h*16:raise ValueError('Invalid frame geometry '+str(file))
    a=np.frombuffer(raw,dtype='<u4').reshape(h,w,4)
    if np.any(a[:,:,1:3]>0xffffff):raise ValueError('Invalid RGB word')
    g=a[:,:,0]
    if np.any(g>0x10ffff)or np.any((g>=0xd800)&(g<=0xdfff)):raise ValueError('Invalid Unicode scalar')
    return a,meta

def cellDifference(expected, actual, channels=4):
    """Exact changed-word/bit counts and first cell coordinates, not a perceptual score."""
    if expected.shape != actual.shape:
        return {'shapeMismatch': [list(expected.shape), list(actual.shape)]}
    x=np.bitwise_xor(expected[:,:,:channels],actual[:,:,:channels])
    affected=np.any(x!=0,axis=2);locations=np.argwhere(affected)
    return {'changedCells':int(np.sum(affected)),
            'changedWords':int(np.sum(x!=0)),
            'changedBits':sum(int(v).bit_count() for v in x[x!=0]),
            'firstCells':[{'x':int(col),'y':int(row),
               'expected':[int(v) for v in expected[row,col,:channels]],
               'actual':[int(v) for v in actual[row,col,:channels]]}
              for row,col in locations[:32]]}

def fontPath():
    candidates=[os.environ.get('NOCTURNE_CAPTURE_FONT',''),'/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf','/System/Library/Fonts/Menlo.ttc','/Library/Fonts/Courier New.ttf','/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf']
    for p in candidates:
        if p and Path(p).is_file():return p
    raise RuntimeError('Install a monospace Unicode font or set NOCTURNE_CAPTURE_FONT; no font is bundled')

def raster(a,cellWidth,cellHeight,font):
    h,w,_=a.shape;b=a[:,:,2];rgb=np.stack(((b>>16)&255,(b>>8)&255,b&255),axis=2).astype('uint8')
    image=Image.fromarray(np.repeat(np.repeat(rgb,cellHeight,axis=0),cellWidth,axis=1),'RGB');draw=ImageDraw.Draw(image)
    for y in range(h):
        for x in range(w):
            g,f=int(a[y,x,0]),int(a[y,x,1]);fg=(f>>16&255,f>>8&255,f&255);px,py=x*cellWidth,y*cellHeight
            if g in(0,32,0x2800):continue
            if g==0x2588:draw.rectangle((px,py,px+cellWidth-1,py+cellHeight-1),fill=fg)
            elif g in(0x2580,0x2584,0x258c,0x2590):
                left,top,right,bottom=px,py,px+cellWidth-1,py+cellHeight-1
                if g==0x2580:bottom=py+cellHeight//2-1
                if g==0x2584:top=py+cellHeight//2
                if g==0x258c:right=px+cellWidth//2-1
                if g==0x2590:left=px+cellWidth//2
                draw.rectangle((left,top,right,bottom),fill=fg)
            elif 0x2800<=g<=0x28ff:
                bits=g-0x2800;pattern=((0,0,0),(0,1,1),(0,2,2),(1,0,3),(1,1,4),(1,2,5),(0,3,6),(1,3,7))
                for col,row,bit in pattern:
                    if bits&(1<<bit):
                        cx=px+(col+.5)*cellWidth/2;cy=py+(row+.5)*cellHeight/4;r=max(1,min(cellWidth/7,cellHeight/12));draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=fg)
            else:
                # Clip each glyph to its cell so a font mismatch cannot hide overdraw.
                mask=Image.new('L',(cellWidth,cellHeight));md=ImageDraw.Draw(mask);md.text((cellWidth/2,cellHeight/2),chr(g),font=font,anchor='mm',fill=255);image.paste(fg,(px,py,px+cellWidth,py+cellHeight),mask)
    return image

def analyze(root:Path,plan:dict,noVideo=False):
    output=root/'visual';output.mkdir(exist_ok=True);issues=[];stats=[];digests={};cache={};fontFile=fontPath();font=ImageFont.truetype(fontFile,plan['cellHeight']-2)
    materializeAnsi(root/'surfaces/go')
    counts={};surfaceCounts={};missing=[]
    for language in plan['languages']:
        source=root/'frames'/language;surface=root/'surfaces'/language;paths=sorted(source.rglob('*.cells')) if source.exists() else []
        counts[language]=len(paths);surfaceCounts[language]=len(list(surface.rglob('*.cells'))) if surface.exists() else 0
        if len(paths)!=plan['expectedFrames']:missing.append({'language':language,'expected':plan['expectedFrames'],'found':len(paths)})
        previous={}
        for file in paths:
            relative=file.relative_to(source);a,meta=readFrame(file);case=str(relative.parent);rawHash=sha(file)
            key=str(relative)
            if key in digests and rawHash!=digests[key][1]:
                reference,_=readFrame(root/'frames'/digests[key][0]/relative)
                issues.append({'severity':'FAIL','kind':'canonical_mismatch','frame':key,'language':language,'reference':digests[key][0],'difference':cellDifference(reference,a)})
            else:digests[key]=(language,rawHash)
            sp=surface/relative;surfaceVerified=False
            if sp.exists():
                actual,_=readFrame(sp)
                if actual.shape!=a.shape or not np.array_equal(actual[:,:,:3],a[:,:,:3]):issues.append({'severity':'FAIL','kind':'framework_surface_mismatch','frame':key,'language':language,'difference':cellDifference(a,actual,3)})
                surfaceVerified=True;display=actual
            else:display=a
            # Compare visibility, not semantic IDs, between actual framework surfaces.
            p=output/language/relative.with_suffix('.png');p.parent.mkdir(parents=True,exist_ok=True)
            displayHash=hashlib.sha256(display[:,:,:3].tobytes()).hexdigest()
            if displayHash in cache:
                try:os.link(cache[displayHash],p)
                except OSError:shutil.copyfile(cache[displayHash],p)
            else:raster(display,plan['cellWidth'],plan['cellHeight'],font).save(p,optimize=False);cache[displayHash]=p
            bg=a[:,:,2];mean=float(np.mean(((bg>>16)&255)*.2126+((bg>>8)&255)*.7152+(bg&255)*.0722)/255)
            changed=0.
            if case in previous:
                old=previous[case];changed=float(np.mean(np.any(a[:,:,:3]!=old[:,:,:3],axis=2)))
                if changed>.92:issues.append({'severity':'REVIEW','kind':'large_temporal_change','language':language,'frame':key,'changedFraction':changed})
            previous[case]=a
            stats.append({'language':language,'frame':key,'timeMs':meta.get('timeMs'),'sourceSHA256':rawHash,'pngSHA256':sha(p),'widthPx':a.shape[1]*plan['cellWidth'],'heightPx':a.shape[0]*plan['cellHeight'],'frameworkSurfaceVerified':surfaceVerified,'changedFraction':changed,'encodedRgbLuma':mean})
        # Every tick for every successfully replayed case, no strides or missing frame tolerance.
        if not noVideo:
            for case in plan['cases']:
                folder=output/language/case['name'];pngs=list(folder.glob('frame-*.png')) if folder.exists() else []
                if len(pngs)!=case['frames']:continue
                movie=folder/'review.mp4';log=folder/'ffmpeg.log'
                cmd=['ffmpeg','-v','error','-y','-framerate',str(plan['fps']),'-i',str(folder/'frame-%06d.png'),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(movie)]
                try:
                    with log.open('w')as f:subprocess.run(cmd,stdout=f,stderr=f,check=True,timeout=1800)
                    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,width,height','-of','json',str(movie)],timeout=30))
                    if int(info['streams'][0]['nb_read_frames'])!=case['frames']:raise ValueError('MP4 frame count mismatch')
                    (folder/'video.json').write_text(json.dumps(info,indent=2))
                except Exception as e:issues.append({'severity':'FAIL','kind':'video','language':language,'case':case['name'],'error':str(e)})
    requiredSurfaceMissing=[l for l in plan['languages'] if surfaceCounts[l]!=plan['expectedFrames']]
    report={'schema':'nocturne.visual.v1','scope':'canonical byte comparison + real framework offscreen surfaces where executed + deterministic cell raster; NOT physical terminal screenshots','frames':counts,'frameworkSurfaceFrames':surfaceCounts,'missing':missing,'missingFrameworkSurfaces':requiredSurfaceMissing,'issues':issues,'fontSHA256':sha(Path(fontFile)),'cellPixels':[plan['cellWidth'],plan['cellHeight']],'mp4':'lossy review only; PNG and cell bytes authoritative','humanVisualReview':'PENDING','automatedComplete':not missing and not requiredSurfaceMissing and not any(i['severity']=='FAIL' for i in issues)}
    (root/'VISUAL-REPORT.json').write_text(json.dumps(report,indent=2));(root/'FRAME-MANIFEST.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in stats))
    index='<!doctype html><meta charset="utf-8"><title>Nocturne qualification</title><style>body{background:#10141c;color:#d6e0ec;font:16px system-ui;margin:2rem}img,video{max-width:100%}details{margin:1rem;border:1px solid #456;padding:1rem}a{color:#8ccfcc}</style><h1>Nocturne capture review</h1><p>Canonical cell raster, not a physical terminal capture. Review all flagged frames and complete sequences. PNGs retain full declared resolution.</p>'
    for language in plan['languages']:
        for case in plan['cases']:
            folder=output/language/case['name']
            if (folder/'frame-000000.png').exists():
                base=f'visual/{language}/{case["name"]}';index+=f'<details><summary>{language} / {case["name"]}</summary><video controls src="{base}/review.mp4"></video><p><a href="{base}/frame-000000.png">First full-resolution frame</a> · {case["frames"]} sequential PNGs</p></details>'
    (root/'REVIEW.html').write_text(index)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--no-video',action='store_true');a=p.parse_args();report=analyze(a.root,json.loads((a.root/'CAPTURE-PLAN.json').read_text()),a.no_video);print(json.dumps({k:v for k,v in report.items() if k!='issues'},indent=2));return 0 if report['automatedComplete'] else 2
if __name__=='__main__':raise SystemExit(main())
