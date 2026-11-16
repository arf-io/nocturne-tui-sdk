#include "scenic_native.h"
#include "scenic_source_raster.h"

static void ignoreCoverage(void *user,int32_t x,int32_t y,int32_t depth,
                           uint32_t rgb,int32_t alpha,int32_t threshold) {
    (void)user;(void)x;(void)y;(void)depth;(void)rgb;(void)alpha;(void)threshold;
}

int scene_native_freestanding_probe(void) {
    int32_t q = 0;
    if (!nrSceneArtQFromNatural(-68.001953125, -100000, 100000, 256, 0, &q) || q != -17408) return 1;
    if (!nrSceneArtQFromNatural(-67.998046875, -100000, 100000, 256, 0, &q) || q != -17407) return 2;
    if (!nrSceneArtQFromNatural(.8125, 0, 1, 1000, 0, &q) || q != 813) return 3;
    if (nrSceneArtQFromNatural(.5, 0, 1, 1, 1, &q)) return 4;
    if (nrSceneArtSamplingMode(0) != 1 || nrSceneArtSamplingMode(1) != 2 ||
        nrSceneArtSamplingMode(2) != -1) return 5;
    Vec3 v = nrSceneArtQ8ToVec3(INT32_MIN, -1, INT32_MAX);
    if (v.x != (double)INT32_MIN/256.0 || v.y != -1.0/256.0 ||
        v.z != (double)INT32_MAX/256.0) return 6;
    static const int32_t sourceWorld[NR_WORLD_FIELD_COUNT] = {
        120,40,NR_SCENIC_PEARL_CASCADE,-17408,12288,-24576,8960,-5632,
        0,15872,1,37120,1000,0,2030,700,3072,1,940,1053726,0,0,0,1
    };
    static const int32_t sourceDetail[NR_WORLD_DETAIL_FIELD_COUNT] = {
        358,8704,5632,480,430,620,1000,1
    };
    static State state;NrScenicArtConfig effective;
    state.schema=NR_STATE_SCHEMA_SCENE_ART;state.width=80;state.height=24;
    state.sceneArt.used=1;state.sceneArt.hasWorldDetail=1;
    for(int i=0;i<NR_WORLD_FIELD_COUNT;i++)state.sceneArt.world[i]=sourceWorld[i];
    for(int i=0;i<NR_WORLD_DETAIL_FIELD_COUNT;i++)state.sceneArt.detail[i]=sourceDetail[i];
    state.camera.position=(Vec3){-68,48,96};state.camera.yaw=35;state.camera.pitch=-22;
    state.camera.fov=62;state.camera.span=145;state.camera.orthographic=1;
    if(!nrSceneArtEffective(&state,80,24,&effective)||
       effective.world[NR_WORLD_CAMERA_Z]!=-24576)return 7;
    state.camera.position=(Vec3){32760,-32760,32760};
    state.camera.yaw=36000;state.camera.pitch=89.9;state.camera.roll=-36000;
    state.camera.fov=10;state.camera.span=.1;state.camera.orthographic=1;
    if(!nrSceneArtEffective(&state,80,24,&effective)||
       nrScenicArtValidate(&effective)||!nrScenicArtValidateView(&effective)||
       effective.world[NR_WORLD_CAMERA_X]!=8386560||
       effective.world[NR_WORLD_CAMERA_Y]!=-8386560||
       effective.world[NR_WORLD_CAMERA_Z]!=-8386560||
       effective.world[NR_WORLD_YAW]!=9216000||
       effective.world[NR_WORLD_PITCH]!=23014||
       effective.world[NR_WORLD_ROLL]!=-9216000||
       effective.world[NR_WORLD_FOV]!=2560||
       effective.world[NR_WORLD_SPAN]!=26)return 8;
    NrScenicSourceRaster raster;
    if(!nrScenicSourceRasterInit(&raster,&effective,80,24,ignoreCoverage,0))return 9;
    effective.world[NR_WORLD_YAW]=9216001;
    if(nrScenicArtValidateView(&effective)||
       nrScenicSourceRasterInit(&raster,&effective,80,24,ignoreCoverage,0))return 10;
    return 0;
}
