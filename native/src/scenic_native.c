/* Native command/effective-view seam for the original scenic sampler.
 * Root owns State layout, command routing, capability metadata and the
 * shared-compositor hook. */
#include "scenic_native.h"

#include <string.h>

_Static_assert(sizeof(SceneArt) == 136, "scene art snapshot record layout");
_Static_assert(sizeof(SceneArtClock) == 16, "scene art clock record layout");
_Static_assert(offsetof(SceneArtClock,timeMs) == 8, "scene art clock value offset");
_Static_assert(offsetof(SceneArt, world) == 8, "scene art world vector offset");
_Static_assert(offsetof(SceneArt, detail) == 104, "scene art detail vector offset");

typedef struct {
    const char *name;
    int index;
    double min;
    double max;
    int scale;
    int integral;
} ScenicControl;

static const ScenicControl WORLD_CONTROLS[] = {
    {"cameraX", NR_WORLD_CAMERA_X, -100000, 100000, 256, 0},
    {"cameraY", NR_WORLD_CAMERA_Y, -100000, 100000, 256, 0},
    {"cameraZ", NR_WORLD_CAMERA_Z, -100000, 100000, 256, 0},
    {"yaw", NR_WORLD_YAW, -360, 360, 256, 0},
    {"pitch", NR_WORLD_PITCH, -89, 89, 256, 0},
    {"roll", NR_WORLD_ROLL, -360, 360, 256, 0},
    {"fov", NR_WORLD_FOV, 15, 140, 256, 0},
    {"projection", NR_WORLD_PROJECTION, 0, 1, 1, 1},
    {"span", NR_WORLD_SPAN, 16, 1000, 256, 0},
    {"flow", NR_WORLD_FLOW, 0, 8, 1000, 0},
    {"travel", NR_WORLD_TRAVEL, -8000000, 8000000, 256, 0},
    {"seed", NR_WORLD_SEED, 0, 2147483647, 1, 1},
    {"redshift", NR_WORLD_REDSHIFT, 0, 1, 1000, 0},
    {"discTilt", NR_WORLD_DISC_TILT, -85, 85, 256, 0},
    {"detail", NR_WORLD_DETAIL, 0, 2, 1, 1},
    {"waterAlpha", NR_WORLD_WATER_ALPHA, 0, 1, 1000, 0},
    {"background", NR_WORLD_BACKGROUND, 0, 16777215, 1, 1},
    {"ink", NR_WORLD_INK, 0, 16777215, 1, 1},
    {"accent", NR_WORLD_ACCENT, 0, 16777215, 1, 1},
    {"secondary", NR_WORLD_SECONDARY, 0, 16777215, 1, 1},
    {"sampling", NR_WORLD_SAMPLING, 0, 1, 1, 1},
};

static const ScenicControl DETAIL_CONTROLS[] = {
    {"waveHeight", NR_WORLD_DETAIL_WAVE_HEIGHT, 0, 8, 256, 0},
    {"wavelength", NR_WORLD_DETAIL_WAVELENGTH, 8, 120, 256, 0},
    {"windAngle", NR_WORLD_DETAIL_WIND_ANGLE, -360, 360, 256, 0},
    {"crossSwell", NR_WORLD_DETAIL_CROSS_SWELL, 0, 1, 1000, 0},
    {"choppiness", NR_WORLD_DETAIL_CHOPPINESS, 0, 1, 1000, 0},
    {"foam", NR_WORLD_DETAIL_FOAM, 0, 1, 1000, 0},
    {"waveSpeed", NR_WORLD_DETAIL_WAVE_SPEED, 0, 4, 1000, 0},
    {"joinRiver", NR_WORLD_DETAIL_JOIN_RIVER, 0, 1, 1, 1},
};

static const int32_t WORLD_DEFAULT[NR_WORLD_FIELD_COUNT] = {
    120, 40, NR_SCENIC_PEARL_CASCADE, -17408, 12288, -24576, 8960, -5632,
    0, 15872, 1, 37120, 1000, 0, 2030, 700, 3072, 1, 940, 1053726, 0, 0, 0, 1
};
static const int32_t DETAIL_DEFAULT[NR_WORLD_DETAIL_FIELD_COUNT] = {
    358, 8704, 5632, 480, 430, 620, 1000, 1
};

static int scenicReject(NrContext *c, const char *message) {
    if (c) {
        size_t i = 0;
        while (message[i] && i + 1 < sizeof(c->error)) {
            c->error[i] = message[i];
            i++;
        }
        c->error[i] = 0;
    }
    return -1;
}

static int scenicViewportRepresentable(uint32_t width, uint32_t height) {
    /* Mirrors nrValidViewport's public representation limits without pulling
       the full state module into this focused unit target. */
    return width && height && width <= 2147483647u/2 && height <= 2147483647u/4 &&
           (uint64_t)width * height <= UINT32_MAX;
}

static int sceneId(const Json *j, int token, int *out) {
    if (token < 0) return 0;
    static const char *names[] = {
        "pearl-cascade", "copper-causeway", "red-shift", "tidal-glass", "silt"
    };
    for (int i = 0; i < NR_SCENIC_SILT + 1; i++) {
        if (nrEqual(j, token, names[i])) {
            *out = i;
            return 1;
        }
    }
    return 0;
}

/* ECMAScript Math.round(x): ties move toward positive infinity. */
int nrSceneArtQFromNatural(double natural, double min, double max, int scale,
                           int integral, int32_t *out) {
    if (!out || scale <= 0 || natural != natural || natural < min || natural > max ||
        natural < -1e100 || natural > 1e100) return 0;
    if (integral && natural != nrFloor(natural)) return 0;
    double scaled = natural * scale;
    if (scaled != scaled || scaled < (double)INT32_MIN || scaled > (double)INT32_MAX) return 0;
    double rounded = nrFloor(scaled + .5);
    if (rounded < (double)INT32_MIN || rounded > (double)INT32_MAX) return 0;
    *out = (int32_t)rounded;
    return 1;
}

static int qValue(double natural, const ScenicControl *field, int32_t *out) {
    return nrSceneArtQFromNatural(natural, field->min, field->max,
                                  field->scale, field->integral, out);
}

static int applyControls(const Json *j, int object, const ScenicControl *fields,
                         size_t count, int32_t *values, double *natural) {
    if (object < 0) return 1;
    for (size_t i = 0; i < count; i++) {
        int token = nrField(j, object, fields[i].name);
        if (token < 0) continue;
        double value;
        int32_t q;
        if (!nrNumber(j, token, &value) || !qValue(value, &fields[i], &q)) return 0;
        values[fields[i].index] = q;
        if (natural) natural[fields[i].index] = value;
    }
    return 1;
}

static int readViewport(const Json *j, int *width, int *height) {
    int wToken = nrField(j, 0, "width"), hToken = nrField(j, 0, "height");
    double value;
    if (wToken >= 0) {
        if (!nrNumber(j, wToken, &value) || value < 1 || value > 2147483647.0/2 || value != nrFloor(value)) return 0;
        *width = (int)value;
    }
    if (hToken >= 0) {
        if (!nrNumber(j, hToken, &value) || value < 1 || value > 2147483647.0/4 || value != nrFloor(value)) return 0;
        *height = (int)value;
    }
    return 1;
}

static int applyCameraControls(const Json *j, int object, const Camera *base,
                               const ScenicControl *fields, size_t count,
                               const int32_t *world, Camera *out) {
    *out = *base;
    if (object < 0) return 1;
    for (size_t i = 0; i < count; i++) {
        int token = nrField(j, object, fields[i].name);
        if (token < 0) continue;
        double n;
        if (!nrNumber(j, token, &n)) return 0;
        switch (fields[i].index) {
            case NR_WORLD_CAMERA_X: out->position.x = n; break;
            case NR_WORLD_CAMERA_Y: out->position.y = n; break;
            /* RC2 looks down +Z; RC4's canonical camera basis looks down -Z. */
            case NR_WORLD_CAMERA_Z: out->position.z = -n; break;
            case NR_WORLD_YAW: out->yaw = n; break;
            case NR_WORLD_PITCH: out->pitch = n; break;
            case NR_WORLD_ROLL: out->roll = n; break;
            case NR_WORLD_FOV: out->fov = n; break;
            case NR_WORLD_PROJECTION: out->orthographic = world[NR_WORLD_PROJECTION] != 0; break;
            case NR_WORLD_SPAN: out->span = n; break;
            default: break;
        }
    }
    return 1;
}

static int hasCameraControls(const Json *j, int object) {
    if (object < 0) return 0;
    static const char *const names[] = {
        "cameraX", "cameraY", "cameraZ", "yaw", "pitch", "roll",
        "fov", "projection", "span"
    };
    for (size_t i = 0; i < sizeof(names)/sizeof(names[0]); i++)
        if (nrField(j, object, names[i]) >= 0) return 1;
    return 0;
}

static int defaultCamera(Camera *out, const Camera *current) {
    *out = *current;
    out->position.x = -68;
    out->position.y = 48;
    out->position.z = 96;
    out->yaw = 35;
    out->pitch = -22;
    out->roll = 0;
    out->fov = 62;
    out->span = 145;
    out->orthographic = 1;
    return 1;
}

static void clearResizeInteraction(State *s) {
    nrPointerRelease(s);
    s->hoverHit = 0;
    s->pressedHit = 0;
}

static int sceneArtCommand(NrContext *c, State *s, const Json *j,int model) {
    if (!c || !s || !j) return scenicReject(c, "Invalid scene-art command context");
    if (s->schema < NR_STATE_SCHEMA_SCENE_ART) return scenicReject(c, "Scene art requires the scene-art state schema");
    int op = nrField(j, 0, "op");
    if (nrEqual(j, op, model?"remove-model-view":"remove-scene-art")) {
        if (!nrAllowed(j, 0, "op")) return scenicReject(c, "Invalid remove-scene-art fields");
        memset(model?&s->sourceModel.view:&s->sceneArt, 0, sizeof(s->sceneArt));
        if(!model)memset(&s->sceneArtClock,0,sizeof(s->sceneArtClock));
        return 0;
    }
    if (!nrEqual(j, op, model?"model-view":"scene-art")) return scenicReject(c, "Scene art operation required");
    if (!nrAllowed(j, 0, model?"op width height controls":"op scene width height controls detail timeMs"))
        return scenicReject(c, "Unknown scene-art command field");

    SceneArtClock clock=s->sceneArtClock;
    int timeToken=nrField(j,0,"timeMs");
    if(timeToken>=0){
        if(model||s->schema<NR_STATE_SCHEMA_SCENE_ART_CLOCK)return scenicReject(c,"Scene-art clock requires schema95");
        if(j->tokens[timeToken].type==J_NULL)memset(&clock,0,sizeof(clock));
        else{
            double value;
            if(!nrNumber(j,timeToken,&value)||!(value>=0&&value<=9007199254740991.0)||value!=nrFloor(value))
                return scenicReject(c,"Scene-art timeMs must be a nonnegative safe integer or null");
            clock=(SceneArtClock){1,0,value};
        }
    }
    SceneArt candidate = model?s->sourceModel.view:s->sceneArt;
    Camera camera = s->camera;
    int width = (int)s->width, height = (int)s->height;
    int firstActivation = !candidate.used;
    if (candidate.used && !(model?nrValidSourceModel(s):nrValidSceneArt(s))) return scenicReject(c, "Invalid retained scene-art configuration");
    if (firstActivation) {
        memcpy(candidate.world, WORLD_DEFAULT, sizeof(WORLD_DEFAULT));
        memcpy(candidate.detail, DETAIL_DEFAULT, sizeof(DETAIL_DEFAULT));
        candidate.hasWorldDetail = 1;
        defaultCamera(&camera, &s->camera);
    }
    int selected;
    int sceneToken = nrField(j, 0, "scene");
    if (sceneToken >= 0) {
        if (!sceneId(j, sceneToken, &selected)) return scenicReject(c, "Unknown scene-art scene");
        candidate.world[NR_WORLD_SCENE] = selected;
    } else if (firstActivation&&!model) {
        return scenicReject(c, "First scene-art activation requires a scene");
    }

    if (!readViewport(j, &width, &height) || !scenicViewportRepresentable((uint32_t)width, (uint32_t)height))
        return scenicReject(c, "Invalid scene-art viewport");
    /* Preserve explicit author-requested source dimensions in the authored
       24-value vector. Later generic resize operations affect only the
       effective presentation view. */
    if (nrField(j, 0, "width") >= 0) candidate.world[NR_WORLD_WIDTH] = width;
    if (nrField(j, 0, "height") >= 0) candidate.world[NR_WORLD_HEIGHT] = height;

    int controls = nrField(j, 0, "controls");
    int detail = nrField(j, 0, "detail");
    if (controls >= 0 && j->tokens[controls].type != J_OBJECT)
        return scenicReject(c, "Scene-art controls must be an object");
    if (detail >= 0 && j->tokens[detail].type != J_OBJECT)
        return scenicReject(c, "Scene-art detail must be an object");
    if (controls >= 0 && !nrAllowed(j, controls,
        "cameraX cameraY cameraZ yaw pitch roll fov projection span flow travel seed redshift discTilt detail waterAlpha background ink accent secondary sampling"))
        return scenicReject(c, "Unknown scene-art control");
    if (detail >= 0 && !nrAllowed(j, detail,
        "waveHeight wavelength windAngle crossSwell choppiness foam waveSpeed joinRiver"))
        return scenicReject(c, "Unknown scene-art detail control");
    int cameraControlsProvided = hasCameraControls(j, controls);
    /* A partial camera edit has the same baseline semantics as `camera`:
       sample the active flight pose, change only authored camera fields, then
       retain that pose as the new canonical camera and cancel the old flight.
       First activation instead starts from source defaults and always resets
       any prior flight. Non-camera patches leave both canonical camera and
       flight untouched. */
    if (!firstActivation && cameraControlsProvided) camera = nrCameraAt(s);

    double natural[NR_WORLD_FIELD_COUNT] = {0};
    for (size_t i = 0; i < sizeof(WORLD_CONTROLS)/sizeof(WORLD_CONTROLS[0]); i++) {
        int token = controls < 0 ? -1 : nrField(j, controls, WORLD_CONTROLS[i].name);
        if (token < 0) continue;
        double value;
        int32_t q;
        if (!nrNumber(j, token, &value) || !qValue(value, &WORLD_CONTROLS[i], &q))
            return scenicReject(c, "Scene-art control is outside its source range");
        candidate.world[WORLD_CONTROLS[i].index] = q;
        natural[WORLD_CONTROLS[i].index] = value;
    }
    if (!applyControls(j, detail, DETAIL_CONTROLS,
                       sizeof(DETAIL_CONTROLS)/sizeof(DETAIL_CONTROLS[0]),
                       candidate.detail, NULL))
        return scenicReject(c, "Scene-art detail is outside its source range");

    Camera changedCamera;
    if (!applyCameraControls(j, controls, &camera, WORLD_CONTROLS,
                             sizeof(WORLD_CONTROLS)/sizeof(WORLD_CONTROLS[0]),
                             candidate.world, &changedCamera))
        return scenicReject(c, "Invalid scene-art camera control");

    candidate.used = 1;
    NrScenicArtConfig config;
    memcpy(config.world, candidate.world, sizeof(config.world));
    memcpy(config.detail, candidate.detail, sizeof(config.detail));
    config.hasWorldDetail = (uint8_t)candidate.hasWorldDetail;
    if (!nrScenicArtValidate(&config)) return scenicReject(c, "Invalid scene-art source vector");

    if(model&&s->sceneArt.used&&candidate.world[NR_WORLD_SAMPLING]!=s->sceneArt.world[NR_WORLD_SAMPLING])return scenicReject(c,"Model and source scene sampling must agree");
    if(!model&&s->sourceModel.view.used&&candidate.world[NR_WORLD_SAMPLING]!=s->sourceModel.view.world[NR_WORLD_SAMPLING])return scenicReject(c,"Model and source scene sampling must agree");
    if(model)s->sourceModel.view=candidate;else{s->sceneArt=candidate;s->sceneArtClock=clock;}
    s->camera = changedCamera;
    if (firstActivation || cameraControlsProvided) memset(&s->flight, 0, sizeof(s->flight));
    if (width != (int)s->width || height != (int)s->height) {
        s->width = (uint32_t)width;
        s->height = (uint32_t)height;
        clearResizeInteraction(s);
    }
    return 0;
}

int nrSceneArtCommand(NrContext*c,State*s,const Json*j){return sceneArtCommand(c,s,j,0);}
int nrModelViewCommand(NrContext*c,State*s,const Json*j){return sceneArtCommand(c,s,j,1);}

int nrValidSceneArt(const State *s) {
    if (!s || s->sceneArt.used > 1 || s->sceneArt.hasWorldDetail > 1) return 0;
    const SceneArtClock*clock=&s->sceneArtClock;
    if(clock->enabled>1||clock->reserved)return 0;
    if(!clock->enabled){static const SceneArtClock empty={0};if(memcmp(clock,&empty,sizeof(empty)))return 0;}
    else if(s->schema<NR_STATE_SCHEMA_SCENE_ART_CLOCK||!s->sceneArt.used||
            !(clock->timeMs>=0&&clock->timeMs<=9007199254740991.0)||clock->timeMs!=nrFloor(clock->timeMs))return 0;
    if (!s->sceneArt.used) {
        static const SceneArt empty = {0};
        return memcmp(&s->sceneArt, &empty, sizeof(empty)) == 0;
    }
    NrScenicArtConfig config;
    memcpy(config.world, s->sceneArt.world, sizeof(config.world));
    memcpy(config.detail, s->sceneArt.detail, sizeof(config.detail));
    config.hasWorldDetail = (uint8_t)s->sceneArt.hasWorldDetail;
    return nrScenicArtValidate(&config);
}

static int q8(double value, int32_t *out) {
    if (value != value || value < -100000 || value > 100000) return 0;
    double q = nrFloor(value * 256.0 + .5);
    if (q < INT32_MIN || q > INT32_MAX) return 0;
    *out = (int32_t)q;
    return 1;
}

static int sceneArtEffective(const State *s,const SceneArt*view,int width,int height,NrScenicArtConfig*out) {
    if (!s || !view || !out || !view->used ||
        width < 1 || height < 1 || !scenicViewportRepresentable((uint32_t)width, (uint32_t)height)) return 0;
    memcpy(out->world, view->world, sizeof(out->world));
    memcpy(out->detail, view->detail, sizeof(out->detail));
    out->hasWorldDetail = (uint8_t)view->hasWorldDetail;
    out->world[NR_WORLD_WIDTH] = width;
    out->world[NR_WORLD_HEIGHT] = height;
    Camera camera = nrCameraAt(s);
    if (!q8(camera.position.x, &out->world[NR_WORLD_CAMERA_X]) ||
        !q8(camera.position.y, &out->world[NR_WORLD_CAMERA_Y]) ||
        !q8(-camera.position.z, &out->world[NR_WORLD_CAMERA_Z]) ||
        !q8(camera.yaw, &out->world[NR_WORLD_YAW]) ||
        !q8(camera.pitch, &out->world[NR_WORLD_PITCH]) ||
        !q8(camera.roll, &out->world[NR_WORLD_ROLL]) ||
        !q8(camera.fov, &out->world[NR_WORLD_FOV]) ||
        !q8(camera.span, &out->world[NR_WORLD_SPAN])) return 0;
    out->world[NR_WORLD_PROJECTION] = camera.orthographic ? 1 : 0;
    return nrScenicArtValidateView(out);
}

int nrSceneArtEffective(const State*s,int w,int h,NrScenicArtConfig*out){return s&&nrValidSceneArt(s)&&sceneArtEffective(s,&s->sceneArt,w,h,out);}
int nrSourceModelEffective(const State*s,int w,int h,NrScenicArtConfig*out){return s&&nrValidSourceModel(s)&&sceneArtEffective(s,&s->sourceModel.view,w,h,out);}

Vec3 nrSceneArtQ8ToVec3(int32_t xQ8, int32_t yQ8, int32_t zQ8) {
    return (Vec3){xQ8 / 256.0, yQ8 / 256.0, zQ8 / 256.0};
}

int nrSceneArtSamplingMode(int sourceSampling) {
    if (sourceSampling == 0) return 1;
    if (sourceSampling == 1) return 2;
    return -1;
}
