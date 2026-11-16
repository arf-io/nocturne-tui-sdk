"""Actual source-depth pick and original projector witnesses, with public gestures."""
from pathlib import Path
import ctypes as C
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bindings/python"))
from nocturne_native import NativeScene

HELPER = r"""
#include "internal.h"
#include "scenic_native.h"
#include "scenic_source_raster.h"
#include <math.h>
/* Projection-only witness: no coverage callback is invoked. */
static void unused(void*u,int32_t x,int32_t y,int32_t d,uint32_t rgb,int32_t a,int32_t t){(void)u;(void)x;(void)y;(void)d;(void)rgb;(void)a;(void)t;}
int picked_sample(NrContext*c,double*out){
 if(!c->sourceActive)return 0;
 for(unsigned y=c->state.height/3;y<c->state.height*3/4;y++)
 for(unsigned x=c->state.width/4;x<c->state.width*2/5;x++){
  int32_t best=0;unsigned generic=0;
  for(unsigned yy=0;yy<4;yy++)for(unsigned xx=0;xx<2;xx++){
   size_t i=(size_t)(y*4+yy)*c->screenWidth+x*2+xx;
   if(c->sourceDepth[i]>best)best=c->sourceDepth[i];generic+=c->fragmentCounts[i];
  }
  if(best>0&&!generic){out[0]=x+.3;out[1]=y+.6;out[2]=c->sourceOrthographic?(268435456.0-best)/256.0:67108864.0/(256.0*best);out[3]=best;return 1;}
 }
 return 0;
}
static int32_t sampledDepth[120*40*8],sampledAlpha[120*40*8];
static void record(void*u,int32_t x,int32_t y,int32_t d,uint32_t rgb,int32_t a,int32_t t){
 (void)u;(void)rgb;(void)t;if(x<0||x>=240||y<0||y>=160||a<=0)return;
 size_t i=(size_t)y*240+x;if(d>sampledDepth[i]){sampledDepth[i]=d;sampledAlpha[i]=a;}
}
int translucent_sample(NrContext*c,double*out){
 NrScenicArtConfig q;NrScenicSourceRaster r;
 if(!nrSceneArtEffective(&c->state,120,40,&q)||!nrScenicSourceRasterInit(&r,&q,120,40,record,0))return 0;
 memset(sampledDepth,0,sizeof(sampledDepth));memset(sampledAlpha,0,sizeof(sampledAlpha));
 if(!nrScenicArtDraw(&q,425,nrScenicSourceRasterSink(&r)))return 0;
 for(unsigned y=8;y<35;y++)for(unsigned x=15;x<105;x++){
  int32_t nearest=0,opaque=0,alpha=0;
  for(unsigned yy=0;yy<4;yy++)for(unsigned xx=0;xx<2;xx++){
   size_t i=(size_t)(y*4+yy)*240+x*2+xx;
   if(sampledDepth[i]>nearest){nearest=sampledDepth[i];alpha=sampledAlpha[i];}
   if(c->sourceDepth[i]>opaque)opaque=c->sourceDepth[i];
  }
  if(nearest>opaque&&alpha>0&&alpha<950){out[0]=x+.3;out[1]=y+.6;out[2]=r.orthographic?(268435456.0-nearest)/256.0:67108864.0/(256.0*nearest);out[3]=nearest;out[4]=opaque;out[5]=alpha;return 1;}
 }
 return 0;
}
int project_grab(NrContext*c,double*out){
 NrScenicArtConfig q;NrScenicSourceRaster r;Vec3 p=c->state.originalCamera.grabbed;
 if(!nrSceneArtEffective(&c->state,c->state.width,c->state.height,&q)||!nrScenicSourceRasterInit(&r,&q,c->state.width,c->state.height,unused,0))return 0;
 int32_t a,b,z,x,y,d;
 if(!nrScenicSourceRasterProjectPoint(&r,(int32_t)floor(p.x*256+.5),(int32_t)floor(p.y*256+.5),(int32_t)floor(-p.z*256+.5),&a,&b,&z,&x,&y,&d))return 0;
 out[0]=x/32.0;out[1]=y/64.0;out[2]=z/256.0;return 1;
}
"""

class ScenicPointerAnchor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="scenic-pointer-witness-")
        out = Path(cls.temp.name)
        source = out / "witness.c"
        source.write_text(HELPER)
        library = out / ("witness.dylib" if sys.platform == "darwin" else "witness.so")
        sdk = Path(os.environ.get("NOCTURNE_REVIEW_LIBRARY", ROOT / "dist" / ("libnocturne_native.dylib" if sys.platform == "darwin" else "libnocturne_native.so")))
        cls.scene_kwargs = {"library": sdk}
        subprocess.run(["cc", "-std=c11", "-O2", "-dynamiclib" if sys.platform == "darwin" else "-shared", "-fPIC",
                        "-I"+str(ROOT/"src"), "-I"+str(ROOT/"include"), str(source), str(sdk),
                        "-Wl,-rpath,"+str(sdk.parent), "-lm", "-o", str(library)], check=True, capture_output=True)
        cls.helper = C.CDLL(str(library))
        for name in ("picked_sample", "translucent_sample", "project_grab"):
            fn = getattr(cls.helper, name)
            fn.argtypes = [C.c_void_p, C.POINTER(C.c_double)]
            fn.restype = C.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_real_original_surface_depth_and_pixel_remain_anchored(self):
        for name in ("pearl-cascade", "copper-causeway", "tidal-glass", "silt"):
            for projection in (0, 1):
                for configured in (False, True):
                    with self.subTest(scene=name, projection=projection, configured=configured), NativeScene(2030, **self.scene_kwargs) as scene:
                        scene.command({"op":"batch","commands":[
                            {"op":"resize","width":120,"height":40},
                            {"op":"environment","presentation":"canvas","stars":0,"style":"solid"},
                            {"op":"floor","enabled":False,"visible":False},
                            {"op":"prompt","active":False},
                            {"op":"scene-art","scene":name,"timeMs":425,"controls":{"projection":projection}},
                            {"op":"camera","profile":"original","navigation":"orbit"}]})
                        if configured: scene.command({"op":"camera-controls","rig":"orbit","mode":"orbit","anchor":None})
                        scene.render()
                        sampled = (C.c_double*4)()
                        self.assertEqual(self.helper.picked_sample(scene._context, sampled), 1, "real off-center source geometry required")
                        x, y, depth, encoded = sampled
                        scene.command({"op":"pointer","phase":"down","button":1,"x":x,"y":y})
                        self.assertIsNotNone(scene.info()["camera"]["grabbed"])
                        projected = (C.c_double*3)()
                        self.assertEqual(self.helper.project_grab(scene._context, projected), 1)
                        print(json.dumps({"scene":name,"projection":projection,"configured":configured,"pointer":[x,y],"sourceDepth":depth,"encodedDepth":encoded,"grabProjection":list(projected)}),flush=True)
                        self.assertAlmostEqual(projected[2], depth, delta=.3, msg="grab must lie at actual source sample depth")
                        self.assertAlmostEqual(projected[0], x, delta=.15)
                        self.assertAlmostEqual(projected[1], y, delta=.15)
                        for dx, dy in ((5.5,-2.25),(-3.25,1.75)):
                            scene.command({"op":"pointer","phase":"move","button":1,"x":x+dx,"y":y+dy})
                            scene.render()
                            self.assertEqual(self.helper.project_grab(scene._context, projected), 1)
                            self.assertAlmostEqual(projected[0], x, delta=.15, msg="grabbed world point moved horizontally")
                            self.assertAlmostEqual(projected[1], y, delta=.15, msg="grabbed world point moved vertically")
                        scene.command({"op":"pointer","phase":"cancel","x":x,"y":y})
                        self.assertIsNone(scene.info()["camera"]["grabbed"])

    def test_actual_wasm_pointer_replay_matches_native(self):
        self.assertNotIn("NOCTURNE_REVIEW_LIBRARY", os.environ, "public replay requires the normal native/WASM pair; isolated-library checks use the native witness methods")
        commands=[]
        for name in ("pearl-cascade", "copper-causeway", "tidal-glass", "silt"):
            for projection in (0, 1):
                setup=[{"op":"reset","seed":2030},{"op":"resize","width":120,"height":40},
                       {"op":"environment","presentation":"canvas","stars":0,"style":"solid"},
                       {"op":"floor","enabled":False,"visible":False},{"op":"prompt","active":False},
                       {"op":"scene-art","scene":name,"timeMs":425,"controls":{"projection":projection}},
                       {"op":"camera","profile":"original","navigation":"orbit"},
                       {"op":"camera-controls","rig":"orbit","mode":"orbit","anchor":None}]
                with NativeScene(2030, **self.scene_kwargs) as scene:
                    for command in setup: scene.command(command)
                    scene.render();sampled=(C.c_double*6)()
                    witness=self.helper.translucent_sample if name=="tidal-glass" else self.helper.picked_sample
                    self.assertEqual(witness(scene._context,sampled),1)
                    x,y=sampled[:2]
                commands.extend(setup)
                commands.extend([{"op":"pointer","phase":"down","button":1,"x":x,"y":y},
                                 {"op":"pointer","phase":"move","button":1,"x":x+5.5,"y":y-2.25},
                                 {"op":"pointer","phase":"move","button":1,"x":x-3.25,"y":y+1.75},
                                 {"op":"pointer","phase":"cancel","x":x,"y":y}])
        node=shutil.which("node");self.assertIsNotNone(node)
        payload="".join(json.dumps(c,separators=(",",":"))+"\n" for c in commands)
        records=[]
        for argv in ([sys.executable,str(ROOT/"scripts/replay.py")],[node,str(ROOT/"scripts/replay.mjs")]):
            result=subprocess.run(argv,cwd=ROOT,input=payload,text=True,capture_output=True,
                                  timeout=120,env=os.environ.copy())
            self.assertEqual(result.returncode,0,result.stderr)
            rows=[json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(rows),len(commands));records.append(rows)
        self.assertTrue(records[0]==records[1],"source picks, camera state, snapshot and frame differ across native/WASM")

    def test_visible_translucent_water_is_pickable_without_changing_occlusion(self):
        for projection in (0, 1):
            with self.subTest(projection=projection), NativeScene(2030, **self.scene_kwargs) as scene:
                for command in [
                    {"op":"resize","width":120,"height":40},
                    {"op":"environment","presentation":"canvas","stars":0,"style":"solid"},
                    {"op":"floor","enabled":False,"visible":False},
                    {"op":"prompt","active":False},
                    {"op":"scene-art","scene":"tidal-glass","timeMs":425,"controls":{"projection":projection}},
                    {"op":"camera","profile":"original","navigation":"orbit"}]:
                    scene.command(command)
                scene.render();sampled=(C.c_double*6)()
                self.assertEqual(self.helper.translucent_sample(scene._context,sampled),1)
                x,y,depth,encoded,opaque,alpha=sampled
                self.assertLess(opaque,encoded);self.assertGreater(alpha,0);self.assertLess(alpha,950)
                scene.command({"op":"pointer","phase":"down","button":1,"x":x,"y":y})
                projected=(C.c_double*3)();self.assertEqual(self.helper.project_grab(scene._context,projected),1)
                print(json.dumps({"surface":"translucent-water","projection":projection,"pointer":[x,y],"depth":depth,"alpha":alpha,"opaqueEncoded":opaque,"grabProjection":list(projected)}),flush=True)
                self.assertAlmostEqual(projected[2],depth,delta=.3)
                for dx,dy in ((0,0),(5.5,-2.25),(-3.25,1.75)):
                    if dx or dy:scene.command({"op":"pointer","phase":"move","button":1,"x":x+dx,"y":y+dy})
                    self.assertEqual(self.helper.project_grab(scene._context,projected),1)
                    self.assertAlmostEqual(projected[0],x,delta=.15)
                    self.assertAlmostEqual(projected[1],y,delta=.15)

if __name__ == "__main__":
    unittest.main()
