#include "../src/internal.h"
#include "../src/scenic_native.h"
#include "../src/scenic_source_raster.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static NrContext context;
static State stateBefore;

static int command(State *s, const char *json) {
    if (!nrParse(&context.json, json, (int)strlen(json))) return -1;
    return nrSceneArtCommand(&context, s, &context.json);
}

static int expectRejectedUnchanged(State *s, const char *json, int code) {
    memcpy(&stateBefore, s, sizeof(*s));
    int result = command(s, json);
    if (result >= 0 || memcmp(&stateBefore, s, sizeof(*s))) {
        fprintf(stderr, "negative command did not reject atomically: %s\n", json);
        return code;
    }
    return 0;
}

static int closeTo(double actual, double expected) {
    return fabs(actual - expected) < 1e-12;
}

static int qCameraValue(double value, int32_t *out) {
    return nrSceneArtQFromNatural(value, -100000, 100000, 256, 0, out);
}

static void ignoreCoverage(void *user,int32_t x,int32_t y,int32_t depth,
                           uint32_t rgb,int32_t alpha,int32_t threshold) {
    (void)x;(void)y;(void)depth;(void)rgb;(void)alpha;(void)threshold;
    (*(uint32_t *)user)++;
}

static int effectiveCanonicalCameraLimits(State *s) {
    int32_t authoredWorld[NR_WORLD_FIELD_COUNT];
    int32_t authoredDetail[NR_WORLD_DETAIL_FIELD_COUNT];
    Camera saved=s->camera;
    memcpy(authoredWorld,s->sceneArt.world,sizeof(authoredWorld));
    memcpy(authoredDetail,s->sceneArt.detail,sizeof(authoredDetail));
    s->camera.position=(Vec3){32760,-32760,32760};
    s->camera.yaw=36000;s->camera.pitch=89.9;s->camera.roll=-36000;
    s->camera.fov=10;s->camera.span=.1;s->camera.orthographic=1;

    NrScenicArtConfig view;
    if(!nrSceneArtEffective(s,(int)s->width,(int)s->height,&view))return 0;
    if(nrScenicArtValidate(&view)||!nrScenicArtValidateView(&view))return 0;
    if(view.world[NR_WORLD_CAMERA_X]!=8386560||view.world[NR_WORLD_CAMERA_Y]!=-8386560||
       view.world[NR_WORLD_CAMERA_Z]!=-8386560||view.world[NR_WORLD_YAW]!=9216000||
       view.world[NR_WORLD_PITCH]!=23014||view.world[NR_WORLD_ROLL]!=-9216000||
       view.world[NR_WORLD_FOV]!=2560||view.world[NR_WORLD_SPAN]!=26||
       view.world[NR_WORLD_PROJECTION]!=1)return 0;

    uint32_t covered=0;NrScenicSourceRaster raster;
    if(!nrScenicSourceRasterInit(&raster,&view,(int32_t)s->width,(int32_t)s->height,
                                 ignoreCoverage,&covered))return 0;
    if(!nrScenicArtDraw(&view,2000,nrScenicSourceRasterSink(&raster)))return 0;

    NrScenicArtConfig invalid=view;
    invalid.world[NR_WORLD_YAW]=9216001;
    if(nrScenicArtValidateView(&invalid)||
       nrScenicSourceRasterInit(&raster,&invalid,(int32_t)s->width,(int32_t)s->height,
                                ignoreCoverage,&covered)||
       nrScenicArtDraw(&invalid,2000,nrScenicSourceRasterSink(&raster)))return 0;

    int ok=nrValidSceneArt(s)&&
        memcmp(authoredWorld,s->sceneArt.world,sizeof(authoredWorld))==0&&
        memcmp(authoredDetail,s->sceneArt.detail,sizeof(authoredDetail))==0;
    s->camera=saved;
    return ok;
}

static int effectiveTracksRealFlight(State *s) {
    static const uint64_t sampleTimes[] = {0, 2000000, 4000000};
    int32_t authoredWorld[NR_WORLD_FIELD_COUNT], authoredDetail[NR_WORLD_DETAIL_FIELD_COUNT];
    memcpy(authoredWorld, s->sceneArt.world, sizeof(authoredWorld));
    memcpy(authoredDetail, s->sceneArt.detail, sizeof(authoredDetail));
    Camera canonical = s->camera;
    memset(&s->flight, 0, sizeof(s->flight));
    s->flight.count = 1;
    s->flight.startUs = 0;
    s->flight.origin = canonical;
    s->flight.steps[0].kind = 1;
    s->flight.steps[0].durationUs = sampleTimes[2];
    s->flight.steps[0].speed = 7;
    s->flight.steps[0].yaw = 60;

    Camera midpoint = canonical;
    for (size_t i = 0; i < sizeof(sampleTimes)/sizeof(sampleTimes[0]); i++) {
        s->timeUs = sampleTimes[i];
        Camera sampled = nrCameraAt(s);
        NrScenicArtConfig effective;
        if (!nrSceneArtEffective(s, (int)s->width, (int)s->height, &effective)) return 0;
        int32_t expected[8];
        if (!qCameraValue(sampled.position.x, &expected[0]) ||
            !qCameraValue(sampled.position.y, &expected[1]) ||
            !qCameraValue(-sampled.position.z, &expected[2]) ||
            !qCameraValue(sampled.yaw, &expected[3]) ||
            !qCameraValue(sampled.pitch, &expected[4]) ||
            !qCameraValue(sampled.roll, &expected[5]) ||
            !qCameraValue(sampled.fov, &expected[6]) ||
            !qCameraValue(sampled.span, &expected[7])) return 0;
        const int indices[8] = {NR_WORLD_CAMERA_X, NR_WORLD_CAMERA_Y,
            NR_WORLD_CAMERA_Z, NR_WORLD_YAW, NR_WORLD_PITCH, NR_WORLD_ROLL,
            NR_WORLD_FOV, NR_WORLD_SPAN};
        for (int k = 0; k < 8; k++)
            if (effective.world[indices[k]] != expected[k]) return 0;
        if (effective.world[NR_WORLD_PROJECTION] != sampled.orthographic ||
            effective.world[NR_WORLD_WIDTH] != (int32_t)s->width ||
            effective.world[NR_WORLD_HEIGHT] != (int32_t)s->height) return 0;
        if (i == 1) midpoint = sampled;
    }
    if (closeTo(midpoint.position.x, canonical.position.x) &&
        closeTo(midpoint.position.z, canonical.position.z)) return 0;
    if (memcmp(authoredWorld, s->sceneArt.world, sizeof(authoredWorld)) ||
        memcmp(authoredDetail, s->sceneArt.detail, sizeof(authoredDetail)) ||
        memcmp(&canonical, &s->camera, sizeof(canonical))) return 0;
    memset(&s->flight, 0, sizeof(s->flight));
    s->timeUs = 0;
    return 1;
}

int main(void) {
    Vec3 fixed = nrSceneArtQ8ToVec3(-1, 12345, INT32_MAX);
    if (fixed.x != -1.0/256.0 || fixed.y != 12345.0/256.0 ||
        fixed.z != (double)INT32_MAX/256.0) return 30;
    int32_t rounded;
    if (!nrSceneArtQFromNatural(-68.001953125, -100000, 100000, 256, 0, &rounded) || rounded != -17408) return 32;
    if (!nrSceneArtQFromNatural(-67.998046875, -100000, 100000, 256, 0, &rounded) || rounded != -17407) return 33;
    if (!nrSceneArtQFromNatural(.8125, 0, 1, 1000, 0, &rounded) || rounded != 813) return 34;
    if (nrSceneArtQFromNatural(.5, 0, 1, 1, 1, &rounded)) return 35;
    if (nrSceneArtSamplingMode(0) != 1 || nrSceneArtSamplingMode(1) != 2 || nrSceneArtSamplingMode(2) != -1) return 36;

    State *s = &context.trial;
    memset(s, 0, sizeof(*s));
    s->schema = NR_STATE_SCHEMA_SCENE_ART;
    s->width = 80;
    s->height = 24;
    s->camera.position = (Vec3){0, 0, 0};
    s->camera.nearPlane = .25;
    s->camera.farPlane = 9000;
    s->camera.fov = 74;
    s->camera.span = 180;
    s->camera.orthographic = 0;

    if (command(s, "{\"op\":\"scene-art\",\"scene\":\"tidal-glass\"}") < 0) return 1;
    if (!nrValidSceneArt(s) || !s->sceneArt.used || !s->sceneArt.hasWorldDetail) return 2;
    const int32_t defaults[24] = {
        120, 40, NR_SCENIC_TIDAL_GLASS, -17408, 12288, -24576, 8960, -5632,
        0, 15872, 1, 37120, 1000, 0, 2030, 700, 3072, 1, 940, 1053726, 0, 0, 0, 1
    };
    const int32_t detail[8] = {358, 8704, 5632, 480, 430, 620, 1000, 1};
    if (memcmp(s->sceneArt.world, defaults, sizeof(defaults)) ||
        memcmp(s->sceneArt.detail, detail, sizeof(detail))) return 3;
    if (s->width != 80 || s->height != 24) return 4;
    if (!closeTo(s->camera.position.x, -68) || !closeTo(s->camera.position.y, 48) ||
        !closeTo(s->camera.position.z, 96) || !closeTo(s->camera.yaw, 35) ||
        !closeTo(s->camera.pitch, -22) || !closeTo(s->camera.roll, 0) ||
        !closeTo(s->camera.fov, 62) || !closeTo(s->camera.span, 145) ||
        s->camera.orthographic != 1 || s->camera.nearPlane != .25 || s->camera.farPlane != 9000) return 5;

    /* JavaScript Math.round ties toward +infinity, including negative Q ties. */
    if (command(s, "{\"op\":\"scene-art\",\"controls\":{\"flow\":1.2345,\"cameraX\":-68.001953125,\"cameraZ\":-110,\"waterAlpha\":0.8125},\"detail\":{\"crossSwell\":0.1235}}") < 0) return 6;
    if (s->sceneArt.world[NR_WORLD_FLOW] != 1235 ||
        s->sceneArt.world[NR_WORLD_CAMERA_X] != -17408 ||
        s->sceneArt.world[NR_WORLD_CAMERA_Z] != -28160 ||
        s->sceneArt.world[NR_WORLD_WATER_ALPHA] != 813 ||
        s->sceneArt.detail[NR_WORLD_DETAIL_CROSS_SWELL] != 124) return 7;
    if (!closeTo(s->camera.position.x, -68.001953125) || !closeTo(s->camera.position.z, 110)) return 8;
    if (s->sceneArt.world[NR_WORLD_SEED] != 2030 || s->sceneArt.detail[NR_WORLD_DETAIL_FOAM] != 620) return 9;

    const char *sceneNames[5] = {
        "pearl-cascade", "copper-causeway", "red-shift", "tidal-glass", "silt"
    };
    for (int scene = 0; scene < 5; scene++) {
        char update[96];
        snprintf(update, sizeof(update), "{\"op\":\"scene-art\",\"scene\":\"%s\"}", sceneNames[scene]);
        if (command(s, update) < 0 || s->sceneArt.world[NR_WORLD_SCENE] != scene) return 91 + scene;
    }

    /* Explicit viewport updates canonical resize; large legal native viewports
       are not clamped to the old rc2 120x40 defaults or descriptor maxima. */
    if (command(s, "{\"op\":\"scene-art\",\"width\":900,\"height\":300}") < 0) return 10;
    if (s->width != 900 || s->height != 300) return 11;
    if (s->sceneArt.world[NR_WORLD_WIDTH] != 900 || s->sceneArt.world[NR_WORLD_HEIGHT] != 300) return 111;
    NrScenicArtConfig effective;
    if (!nrSceneArtEffective(s, s->width, s->height, &effective)) return 12;
    if (effective.world[NR_WORLD_WIDTH] != 900 || effective.world[NR_WORLD_HEIGHT] != 300) return 13;
    if (s->sceneArt.world[NR_WORLD_WIDTH] != 900 || s->sceneArt.world[NR_WORLD_HEIGHT] != 300) return 131;
    if (effective.world[NR_WORLD_CAMERA_X] != -17408 || effective.world[NR_WORLD_FLOW] != 1235) return 14;

    /* Later canonical camera/resize changes are authoritative, while authored
       values remain separately retained for metadata and snapshot round trip. */
    s->camera.position.x = 12.5;
    s->camera.position.z = 42;
    s->camera.yaw = -17.25;
    s->width = 101;
    s->height = 37;
    int32_t authoredX = s->sceneArt.world[NR_WORLD_CAMERA_X];
    if (!nrSceneArtEffective(s, s->width, s->height, &effective)) return 15;
    if (effective.world[NR_WORLD_CAMERA_X] != 3200 || effective.world[NR_WORLD_CAMERA_Z] != -10752 ||
        effective.world[NR_WORLD_YAW] != -4416) return 16;
    if (s->sceneArt.world[NR_WORLD_CAMERA_X] != authoredX || s->width != 101 || s->height != 37) return 17;
    /* Effective scene projection follows nrCameraAt throughout a real flight,
       while canonical camera and authored source controls remain retained. */
    if (!effectiveTracksRealFlight(s)) return 171;
    if (!effectiveCanonicalCameraLimits(s)) return 172;

    if (expectRejectedUnchanged(s, "{\"op\":\"scene-art\",\"scene\":\"unknown\"}", 20)) return 20;
    if (expectRejectedUnchanged(s, "{\"op\":\"scene-art\",\"controls\":{\"notAControl\":1}}", 21)) return 21;
    if (expectRejectedUnchanged(s, "{\"op\":\"scene-art\",\"detail\":{\"joinRiver\":0.5}}", 22)) return 22;
    if (expectRejectedUnchanged(s, "{\"op\":\"scene-art\",\"controls\":{\"flow\":8.001}}", 23)) return 23;
    if (expectRejectedUnchanged(s, "{\"op\":\"scene-art\",\"width\":0}", 24)) return 24;
    if (expectRejectedUnchanged(s, "{\"op\":\"scene-art\",\"scene\":\"pearl-cascade\",\"controls\":{\"scene\":3}}", 25)) return 25;
    if (expectRejectedUnchanged(s, "{\"op\":\"scene-art\",\"controls\":{\"cameraPitch\":90}}", 26)) return 26;
    Camera beforeRemoveCamera = s->camera;
    uint32_t beforeRemoveWidth = s->width, beforeRemoveHeight = s->height;
    if (command(s, "{\"op\":\"remove-scene-art\"}") < 0 || s->sceneArt.used || s->sceneArt.hasWorldDetail) return 28;
    if (memcmp(&beforeRemoveCamera, &s->camera, sizeof(Camera)) ||
        s->width != beforeRemoveWidth || s->height != beforeRemoveHeight) return 29;
    if (expectRejectedUnchanged(s, "{\"op\":\"scene-art\",\"controls\":{\"flow\":2}}", 31)) return 31;
    uint32_t currentSchema = s->schema;
    s->schema = NR_STATE_SCHEMA_WINDOW_SOURCE;
    if (expectRejectedUnchanged(s, "{\"op\":\"scene-art\",\"scene\":\"pearl-cascade\"}", 27)) return 27;
    s->schema = currentSchema;

    puts("scene-art native contract: source defaults, JS Q rounding, canonical view, and atomic rejection");
    return 0;
}
