#ifndef NR_INTERNAL_H
#define NR_INTERNAL_H
#include "nocturne_native.h"
#include "prompt_source.h"
#include "source_material_sampler.h"
#include "scenic_art.h"
#include "scenic_source_raster.h"
#include "window_source_presentation.h"
#include "stage_native.h"
#include "window_texture.h"
#include "window_content.h"
#include "window_application.h"
#include "window_atelier.h"
#include <string.h>
#define NR_LAYOUT_MAX 2147483647
#define NR_LAYOUT_MIN (-2147483647-1)
#define NR_MAGIC 0x3456524eu
#define NR_STATE_SCHEMA 0x20261098u
#define NR_STATE_SCHEMA_PROMPT_SOURCE_REGION 0x20261098u
#define NR_STATE_SCHEMA_OCCLUSION_CONTROLS 0x20261097u
#define NR_STATE_SCHEMA_PROMPT_APPEARANCE 0x20261096u
#define NR_STATE_SCHEMA_SCENE_ART_CLOCK 0x20261095u
#define NR_STATE_SCHEMA_CAMERA_CONTROLS 0x20261094u
#define NR_STATE_SCHEMA_SOURCE_MODAL 0x20261093u
#define NR_STATE_SCHEMA_OBSERVATORY_OVERLAY 0x20261092u
#define NR_STATE_SCHEMA_SOURCE_STAGE_SCENE 0x20261091u
#define NR_STATE_SCHEMA_SOURCE_MODEL 0x20261090u
#define NR_STATE_SCHEMA_FIRST_PROMPT 0x20261089u
#define NR_STATE_SCHEMA_CAMERA_ANCHOR 0x20261088u
#define NR_STATE_SCHEMA_CORONA_PAINT 0x20261084u
#define NR_STATE_SCHEMA_OBSERVATORY_PAINT 0x20261083u
#define NR_STATE_SCHEMA_WORLD_PAINT 0x20261081u
#define NR_STATE_SCHEMA_THERMAL_PAINT 0x20261079u
#define NR_STATE_SCHEMA_SURFACE_PAINT 0x20261086u
#define NR_STATE_SCHEMA_STUDIO_PAINT 0x20261078u
#define NR_STATE_SCHEMA_HISTORY100 0x20261075u
#define NR_STATE_SCHEMA_KINETIC_PAINT 0x20261076u
#define NR_STATE_SCHEMA_DYNAMIC_PROMPT 0x20261073u
#define NR_STATE_SCHEMA_ATELIER_APP_PARTICLES 0x20261082u
#define NR_STATE_SCHEMA_ATELIER_WINDOWS 0x20261080u
#define NR_STATE_SCHEMA_CAMERA_ORIGINAL 0x20261074u
#define NR_STATE_SCHEMA_WINDOW_POOLS 0x20261072u
#define NR_STATE_SCHEMA_WINDOW_APPLICATION 0x20261069u
#define NR_STATE_SCHEMA_PROMPT_CAPACITY 0x20261070u
#define NR_STATE_SCHEMA_WINDOW_TEXTURE 0x20261068u
#define NR_STATE_SCHEMA_OBSERVATORY 0x20261058u
#define NR_STATE_SCHEMA_KINETIC 0x20261059u
#define NR_STATE_SCHEMA_ATELIER 0x20261060u
#define NR_STATE_SCHEMA_THERMAL_PROFILES 0x20261061u
#define NR_STATE_SCHEMA_WORLD_PROFILES 0x20261062u
#define NR_STATE_SCHEMA_STUDIO_NOVA 0x20261063u
#define NR_STATE_SCHEMA_TEXT_ALPHABET 0x20261064u
#define NR_STATE_SCHEMA_TEXT_UINT32_SEED 0x20261065u
#define NR_STATE_SCHEMA_WINDOW_SOURCE 0x20261066u
#define NR_STATE_SCHEMA_TEXT_PHASE_MODEL 0x20261067u
#define NR_STATE_SCHEMA_PROMPT_FRAMED 0x20261067u
#define NR_STATE_SCHEMA_MATERIAL_PATTERN 0x20261067u
#define NR_STATE_SCHEMA_SCENE_ART 0x20261067u
#define NR_STATE_SCHEMA_CANVAS_PRESENTATION 0x20261067u
#define NR_STATE_SCHEMA_WINDOW_PRESENTATION 0x20261067u
#define NR_STATE_SCHEMA_SOURCE_STAGE 0x20261067u
#define NR_STATE_SCHEMA_CORONA 0x20261057u
#define NR_STATE_SCHEMA_WIDE_UNBOUND_VALUES 0x20261056u
#define NR_STATE_SCHEMA_RESOURCE_ANIMATION 0x20261055u
#define NR_STATE_SCHEMA_NOVA_OPTICS 0x20261054u
#define NR_STATE_SCHEMA_BURST_CONTROLS 0x20261053u
#define NR_STATE_SCHEMA_ELECTRICAL_ARCS 0x20261052u
#define NR_STATE_SCHEMA_BIDI_PROMPT 0x20261051u
#define NR_PROMPT_BIDI(s) (((s)->promptPresentation.layout&3)==2)
#define NR_PROMPT_DIRECTION(s) ((unsigned)(s)->promptPresentation.layout>>2)
#define NR_STATE_SCHEMA_PROMPT_PRESENTATION 0x20261050u
#define NR_STATE_SCHEMA_SOURCE_OPTICS 0x20261049u
#define NR_FIELD_SOURCE_PAINT(q) (((q)->rings&32u)!=0)
#define NR_FIELD_RINGS(q) ((q)->rings&31u)
#define NR_FIELD_OPTICS(q) ((q)->rings>>8)
#define NR_STATE_SCHEMA_SOFT_FRONTS 0x20261048u
#define NR_STATE_SCHEMA_COLOR_FIELDS 0x20261047u
#define NR_STATE_SCHEMA_MESH_SUBDIVISION 0x20261046u
#define NR_STATE_SCHEMA_AGGREGATE_REEMIT 0x20261045u
#define NR_STATE_SCHEMA_MATERIAL_HEAT 0x20261044u
#define NR_STATE_SCHEMA_LATENT_HEAT 0x20261043u
#define NR_STATE_SCHEMA_HYDRAULIC_HEAT 0x20261042u
#define NR_STATE_SCHEMA_SURFACE_POSE 0x20261041u
#define NR_STATE_SCHEMA_ANGULAR_HISTORY 0x20261040u
#define NR_STATE_SCHEMA_ANGULAR_FLUID 0x20261039u
#define NR_STATE_SCHEMA_FLUID_HISTORY 0x20261038u
#define NR_STATE_SCHEMA_SURFACE_FLUID 0x20261037u
#define NR_STATE_SCHEMA_FLOAT_HULLS 0x20261036u
#define NR_STATE_SCHEMA_TEXT_IDENTITIES 0x20261035u
#define NR_STATE_SCHEMA_FLOW_SETTINGS 0x20261035u
#define NR_STATE_SCHEMA_THERMAL_SETTINGS 0x20261035u
#define NR_STATE_SCHEMA_WATER_SETTINGS 0x20261035u
#define NR_STATE_SCHEMA_FLOW_THICKNESS 0x20261034u
#define NR_STATE_SCHEMA_FOAM_TRANSPORT 0x20261033u
#define NR_STATE_SCHEMA_GENERAL_API 0x20261032u
#define NR_STATE_SCHEMA_CELL_ART 0x20261031u
#define NR_STATE_SCHEMA_THERMAL_LINK 0x20261030u
#define NR_STATE_SCHEMA_THERMAL_TRANSFER 0x20261029u
#define NR_STATE_SCHEMA_THERMAL 0x20261028u
#define NR_STATE_SCHEMA_WATER_REEMIT 0x20261027u
#define NR_STATE_SCHEMA_WATER_LINK 0x20261026u
#define NR_STATE_SCHEMA_WATER_TRANSFER 0x20261025u
#define NR_STATE_SCHEMA_SURFACE_WATER 0x20261024u
#define NR_STATE_SCHEMA_SPRAY_PARTICLES 0x20261023u
#define NR_STATE_SCHEMA_FLOW_SPRAY 0x20261022u
#define NR_STATE_SCHEMA_FLOW_SINK 0x20261021u
#define NR_STATE_SCHEMA_FLOW_SURFACE 0x20261020u
#define NR_STATE_SCHEMA_FLOW 0x20261019u
#define NR_STATE_SCHEMA_REPEAT_EDIT 0x20261018u
#define NR_STATE_SCHEMA_EDITOR_REDO 0x20261017u
#define NR_STATE_SCHEMA_NAMED_REGISTERS 0x20261016u
#define NR_STATE_SCHEMA_VIM_REGISTER 0x20261015u
#define NR_STATE_SCHEMA_VIM_OPERATOR 0x20261014u
#define NR_STATE_SCHEMA_VIM_COUNT 0x20261013u
#define NR_STATE_SCHEMA_PATH_ACTORS 0x20261012u
#define NR_STATE_SCHEMA_FOAM 0x20261011u
#define NR_STATE_SCHEMA_FLOAT_BODIES 0x20261010u
#define NR_STATE_SCHEMA_SURFACE_WAVES 0x20261009u
#define NR_STATE_SCHEMA_PARTICLE_MOTION 0x20261008u
#define NR_STATE_SCHEMA_BIRTH_FRAME 0x20261007u
#define NR_STATE_SCHEMA_GEOMETRY 0x20261006u
#define NR_STATE_SCHEMA_PRE_GEOMETRY 0x20261005u
#define NR_STATE_SCHEMA_LOCAL_ACTION 0x20261004u
#define NR_STATE_SCHEMA_LOCAL_SELECTOR 0x20261003u
#define NR_STATE_SCHEMA_CONTRACTS7 0x20261003u
#define NR_STATE_SCHEMA_OLDEST 0x20261002u
#define NR_TRIGGER_SOURCE_INTENT_VALUE (-2)
#define NR_PENDING 32
#define NR_PENDING_BYTES 4096
#define NR_PI 3.14159265358979323846
#define NR_TEXTS 24
#define NR_FIELDS 192
#define NR_MATERIALS 16
#define NR_WIDGETS 40
#define NR_AREAS 16
#define NR_MESSAGES 48
#define NR_NOTIFICATION_ACTIONS 4
#define NR_ACTION_LABEL 64
#define NR_INTENTS 64
#define NR_INDICATORS 24
#define NR_EDGES 256
#define NR_STEPS 32
#define NR_DEPOSITS 512
#define NR_TILES 256
#define NR_VALUES 64
#define NR_TRIGGERS 32
#define NR_CONDITIONS 31
#define NR_CONDITION_DEPTH 8
#define NR_REGISTERED_STATES 64
#define NR_STYLE_RULES 32
#define NR_STYLE_PROPERTIES 7
#define NR_STYLE_STATES 5
#define NR_STYLE_FAMILIES 11
#define NR_MESH 256
#define NR_SURFACES 16
#define NR_BVH_NODES 127
#define NR_COLLISION_CONTACTS 4
#define NR_COLLIDERS_EXPLICIT 0x80000000u
#define NR_COLLIDER_BITS 0x0001ffffu
#define NR_JSON_TOKENS 16384
#define NR_LAYERS 6
#define NR_INFO_SIZE 1048576u
#define NR_Q 65536.0
#define NR_GLYPH_BLOCK 0x2580u
#define NR_ID_NODE 0x10000000u
#define NR_ID_WINDOW 0x20000000u
#define NR_ID_WIDGET 0x30000000u
#define NR_ID_PROMPT 0x40000000u
#define NR_ID_DOCK 0x50000000u
#define NR_ID_CLOSE 0x60000000u
#define NR_ID_MIN 0x61000000u
#define NR_ID_MAX 0x62000000u
#define NR_ID_WINDOW_RETURN 0x64000000u
#define NR_ID_SOURCE_STAGE 0x65000000u
#define NR_ID_NOTIFICATION_ACTION 0x63000000u
typedef struct {uint32_t enabled,reserved;int32_t values[112];} FirstPromptSource;
/* Where and how an enabled prompt source paints: the first instance of a bounded surface layer.
 * All-zero bytes are the full viewport at alpha 1 with no frame, so every older snapshot restores unchanged.
 * placement 1 holds a cell rectangle; placement 2 follows the active prompt's frame and placement 3 a
 * widget's rectangle, both resolved from current state every frame. z (0 above) and order (0) are
 * reserved for the surface-layers design and are always zero. */
/* alphaForeground applies to the source's glyphs, alphaBackground to its paper (and to the scene ink it covers). */
typedef struct {uint32_t placement,widget;int32_t x,y,width,height;uint32_t frame,z;int32_t order;uint32_t alphaConfigured;double alphaForeground,alphaBackground;} PromptSourceLayer;
#define NR_PROMPT_SOURCE_VIEWPORT 0u
#define NR_PROMPT_SOURCE_CELLS 1u
#define NR_PROMPT_SOURCE_PROMPT 2u
#define NR_PROMPT_SOURCE_WIDGET 3u
#define NR_PROMPT_SOURCE_ALPHA_FG(s) ((s)->promptSourceLayer.alphaConfigured?(s)->promptSourceLayer.alphaForeground:1.0)
#define NR_PROMPT_SOURCE_ALPHA_BG(s) ((s)->promptSourceLayer.alphaConfigured?(s)->promptSourceLayer.alphaBackground:1.0)
typedef struct {int key,motion,count,unit,selected,append;} RepeatEdit;
typedef struct {uint32_t id;int used,count,epochs;struct {char name[32];uint64_t delayUs,tailUs;} stages[8];struct {uint64_t atUs;double rate;} changes[128];} Flow;
typedef struct {
    double x,y,z;
}
Vec3;
typedef struct {
    int32_t x,y,z;
}
QVec3;
typedef struct {
    int type,start,end,next,count;
    double number;
}
JToken;
typedef struct {
    const char *text;
    int length,count,pos,depth;
    JToken tokens[NR_JSON_TOKENS];
    char error[128];
}
Json;
enum {
    J_OBJECT=1,J_ARRAY,J_STRING,J_NUMBER,J_TRUE,J_FALSE,J_NULL
};
typedef struct {
    double initial,rate,min,max,step;
    uint64_t periodUs;
    int boundary,easing;
    uint32_t seed;
}
Track;
typedef struct {
    int used,space,scope,blend,gradientCount,colorCount;
    Track channel[4],alpha,index;
    double hueStep,spacing;
    double stops[16][4];
    uint32_t colors[64];
}
Material;
typedef struct {uint32_t used,reserved;NrSourceMaterialSampler sampler;} MaterialPattern;
typedef struct {uint32_t used,hasWorldDetail;int32_t world[24],detail[8];} SceneArt;
typedef struct {uint32_t enabled,reserved;double timeMs;} SceneArtClock;
typedef struct {uint32_t id,generation;double capacity,temperature,contactFraction,conductance;} HeatReservoir;
typedef struct {Vec3 position;int32_t parent;uint32_t reserved;} ElectricalPoint;
typedef struct {uint32_t used,reserved;double glitterHz,glitterDepth,coreAlpha,residualAlpha;uint64_t residualUs;} BurstControls;
typedef struct {uint32_t used,generation;double speed,width,intensity;uint64_t durationUs,startUs;} CoronaControls;
typedef struct {uint32_t used,generation,seed,reserved;double speed,intensity;uint64_t durationUs,startUs;} ObservatoryControls;
typedef struct {
    uint32_t used,generation,seed,eventId,count,branches,arcSegments,glyphCount;
    double lifeMs,launchSpeed,gravity,drag,wind,flickerHz,trailMs,arcJitter,coreMs,shockwave,explosionForce,brightness,emberSpread,arcReach;
    uint64_t startUs;
    uint32_t glyphs[64];
} KineticControls;
typedef struct {uint32_t pointCount,segmentCount;double core,radius,shockwave;double points[160][6],segments[512][7];} KineticSample;
typedef struct {
    uint32_t used,generation,seed,eventId,count,branches,reducedMotion,reserved;
    double lifeMs,speed,gravity,rise,drag,turbulence,glitterHz,trailMs,jaggedness,coreMs,coreRadius,ejecta,shockwave,intensity;
    uint64_t startUs;
} AtelierControls;
typedef struct {uint32_t pointCount,segmentCount,glowCount,reserved;double points[513][5],segments[524][6],glows[2][6];} AtelierSample;
typedef struct {uint32_t used,generation,seed,reserved;double lifeMs;uint64_t startUs;} ThermalSourceControls;
typedef struct {uint32_t pointCount,segmentCount;double points[88][6],segments[400][8];} ThermalSourceSample;
typedef struct {uint32_t used,generation,seed,count;double scale,lifeMs,gravity;uint64_t startUs;} WorldSourceControls;
typedef struct {uint32_t pointCount,segmentCount;double points[1200][6],segments[1200][8];} WorldSourceSample;
typedef struct {uint32_t used,generation,seed,novaDurationMs,rippleSpeed,rippleWidth,rippleOpacity,rippleRings,cellAspect,strength,waveScale,glyphCount,paletteCount,starPaletteCount;uint32_t glyphs[16],palette[32],starPalette[32];uint64_t startUs;} StudioNovaControls;
typedef struct {uint32_t envelope,glyph,glyphIndex,coreColor;} StudioNovaSample;
typedef struct {
    uint32_t enabled,reserved;
    NrPromptSourceOptions options;
    uint32_t vimState,minimizedRestoreMode,normalMode,reserved2;
    uint32_t commandCount,command[256];
    uint32_t searchCount,search[256];
    uint32_t messageCount,message[512];
    uint32_t checkpointValid,checkpointCount,checkpointCaret,checkpointMode,checkpointNormalMode,checkpointVimState;
    NrPromptSourceOptions checkpointOptions;
    uint32_t checkpointText[65536];
} PromptFramed;
typedef struct {uint32_t profile,seed,count,index;} NovaOptics;
typedef struct {
    uint32_t id,seed,material,count;
    uint64_t startUs,delayUs,holdUs,fadeUs,periodUs;
    double speed,jitter,alpha,flicker;
    ElectricalPoint points[32];
} ElectricalArc;
typedef struct {
    Vec3 position;
    double yaw,pitch,roll,nearPlane,farPlane,fov,span;
    int orthographic;
}
Camera;
typedef struct {
    int kind,coordinated;
    uint64_t durationUs;
    double speed,yaw,pitch,roll,bank,radius;
    Vec3 target;
}
Motion;
typedef struct {
    uint64_t startUs;
    int count;
    Camera origin;
    Motion steps[NR_STEPS];
    Vec3 look;
}
Flight;
typedef struct {uint64_t durationUs;uint32_t kind,coordinated;double speed,degrees,bank;} OriginalFlightStep;
typedef struct {
    uint32_t enabled,navigation,flightKind,stepCount;
    Vec3 target;
    double moveSpeed,turnSpeed,sensitivity;
    uint64_t startUs;
    Camera origin;
    Vec3 direction,orbitTarget,radial,tangent;
    double speed,periodSeconds,radialRate,bank,radius;
    uint32_t orbitMode,grabActive,grabSource,grabWidth,grabHeight,grabReserved;
    Vec3 grabbed;
    OriginalFlightStep steps[64];
} OriginalCamera;
typedef struct {
    uint32_t id,seed,generation;
    int used,effect,shape,schedule,count,born,material,deposit,collision,topology,endStyle,stopping;
    uint64_t startUs,runningUs,lifeMinUs,lifeMaxUs,stopUs,tailUs;
    Vec3 position,extent,velocity,spread,gravity,wind,windVariation,tumble,shapeWeights;
    double drag,lift,flutterHz,flutterAmount,sizeMin,sizeMax,alpha,heat,radius,windScale,windPeriod;
    uint32_t trailUs,birthFadeUs,deathFadeUs,coreUs;
    int cycles;
    uint64_t gapUs;
    double rate,nearDistance,farDistance,farFade,veinContrast,curl,backTint;
    int twoSided,sampling;
    double surfaceAlpha;
}
Emitter;
typedef struct {
    uint32_t id,emitterId,seed,bornStep,lifeSteps;
    int emitterSlot,state,effect,material;
    QVec3 position,previous,velocity;
    double size,angle,heat;
    uint64_t settledUs;
    int leafShape;
}
Particle;
typedef struct {
    int used,effect,material;
    uint32_t id,seed;
    Vec3 position;
    double size,angle,alpha;
    uint64_t atUs;
    uint32_t emitterId,emitterGeneration;
    int leafShape;
    double veinContrast,curl,backTint,surfaceAlpha;
    int sampling;
}
Deposit;
typedef struct {
    int used,x,z;
    uint32_t count,color,emitterId;
    uint64_t atUs;
}
DepositTile;
typedef struct {
    uint32_t generation,seed,lifeSteps,emitted;
    int effect,material,leafShape,motionAuthored;
    double size,angle,heatCapacity,heatFraction,heatConductance;
    Vec3 orientation,angularVelocity;
    uint32_t used,padding;
} AggregateProvenance;
typedef struct {
    int enabled,visible,maxIndividual,maxTiles,overflow,sampling;
    double height,restitution,friction,settleSpeed,reentrain,cellSize,alpha;
    uint64_t retentionUs,fadeUs;
    double wetness,evaporation;
}
Floor;
typedef struct {
    uint32_t id,seed;
    int used,effect,material;
    uint64_t atUs,lifeUs;
    double x,y,width,speed,strength;
}
Field;
typedef struct {
    int used,continuous,falloff,materialAuthored,surface;
    uint32_t rings;
    double frequency,phase,interference,vx,vy,x,y,width,height;
} FieldControls;
typedef struct {
    uint32_t glyphs[NR_MAX_TEXT];
    int count,caret,anchor,mode,active,minRows,maxRows,border,padding,vimMode;
    double alpha;
    uint32_t undo[16][NR_MAX_TEXT];
    int undoCount[16],undoCaret[16],undoHead,undoSize;
    int modal;
    uint64_t revision;
}
LegacyPrompt;
typedef struct {
    uint32_t glyphs[NR_MAX_PROMPT];
    int count,caret,anchor,mode,active,minRows,maxRows,border,padding,vimMode;
    double alpha;
    uint32_t undo[16][NR_MAX_PROMPT];
    int undoCount[16],undoCaret[16],undoHead,undoSize;
    int modal;
    uint64_t revision;
}
PromptFixed70;
typedef struct {
    union {uint32_t *glyphs;uint64_t glyphPointerAlignment;};
    int count,caret,anchor,mode,active,minRows,maxRows,border,padding,vimMode;
    double alpha;
    uint32_t *undo[100];
    int undoCount[100],undoCaret[100],undoHead,undoSize;
    int modal;uint64_t revision;
} Prompt;
/* Scene-wide treatment of braille-family particles hidden behind the nearest one in a cell.
 * All-zero bytes are the default (tint 1, hidden dots), so every older snapshot restores unchanged. */
typedef struct {
 uint32_t tintConfigured; /* 0: occlusionTint is the default 1 and tint holds 0; 1: tint holds the authored value. */
 uint32_t occludedDots; /* 0 hidden, 1 merge. */
 double tint; /* 0..1 when configured. */
} OcclusionControls;
#define NR_OCCLUSION_TINT(s) ((s)->occlusionControls.tintConfigured?(s)->occlusionControls.tint:1.0)
typedef struct {uint32_t *glyphs;int count,linewise;} PromptRegister;
typedef struct {PromptRegister slots[26];int pending,selected,append,padding;uint64_t revision;} PromptRegisters;
typedef struct {uint32_t id,count,generation,padding;uint32_t *source,*identities;} PromptIdentity;
typedef struct {
 uint32_t cursorConfigured,cursorShape,cursorGlyph,cursorColor,cursorColor2,colorMode,weatherConfigured,weatherStyle;
 double blinkMs,duty,colorPeriodMs,weatherIntensity,weatherLifeMs,weatherSpeed;
 uint32_t pastePolicy,eventCount;uint64_t eventSerial;
 NrSourceWeatherEvent events[64];
} PromptAppearance;

typedef struct {
    Prompt document;PromptRegister register0;PromptRegisters registers;PromptIdentity identity;
    uint32_t *checkpoint,*scratch;uint32_t capacity,scratchWords;uint64_t historyCapacity;NrContext *owner;
} PromptRuntime;
typedef struct {uint32_t action,enabled,invert,reserved;double sensitivity;} CameraAxisControl;
typedef struct {
    uint32_t configured,rig,mode,inputTarget;
    CameraAxisControl axes[3];
    Vec3 headPosition,headRotation,cranePivot,craneBoom,followPoint,followOffset,followReference;
    uint32_t followKind,followId,anchorEnabled,followTrack;
    Vec3 anchor;
} CameraControls;
_Static_assert(sizeof(CameraControls)==296,"Camera controls wire footer");
typedef struct { double x,y,alpha,hue;uint32_t glyph; } TextPose;
typedef struct { double dx,dy,da,dh;uint32_t glyph,identity; } TextOrigin;
typedef struct {
    int used,id,effect,phase,local,x,y,width,material,seed,easing,batchSize,count,alphabetCount;
    uint64_t startUs,durationUs,staggerUs,jitterUs;
    double distance,scatter,variation,wind,overshoot,cycles,scrambleHz,hueSpread;
    uint32_t text[NR_MAX_TEXT],alphabet[128];
    uint64_t delayUs,totalUs;
    int reverseOrder,randomOrder,trailLength,retargeted;
    uint16_t rank[NR_MAX_TEXT],column[NR_MAX_TEXT],row[NR_MAX_TEXT];
    TextOrigin origin[NR_MAX_TEXT];
}
TextRun;
typedef struct {
    int used,id,effect,shape,material,group,titleCount,textCount,target,maximized;
    uint64_t atUs,durationUs;
    double fromVisibility,alpha,width,height;
    Vec3 position;
    double yaw,pitch,roll;
    uint32_t title[160],text[NR_MAX_TEXT];
    int reader,scrollRow,minColumns,maxColumns;
    double anchorX,anchorY,overshoot,scatter,bend;
    int folds,meshColumns,meshRows,polygonCount;
    uint32_t seed;
    double polygon[32][2];
    int padding,border,chromeSize;
    double fadeStartRatio,fadeEndRatio;
}
Window;
typedef struct {
    int used,id,kind,x,y,width,height,padding,border,material,backgroundMaterial,enabled,selected,active,count,dataCount,mode;
    uint32_t text[NR_MAX_TEXT];
    double alpha,value,min,max,data[128];
    uint64_t changedUs,pulseUs;
    int sampling;
    double cellAspect,innerRadius,startAngle,sweepAngle;
    uint64_t revealUs,revealAtUs;
}
Widget;
typedef struct {
    int used,id,parent,x,y,width,height,padding,margin,border,hideEmpty,material;
    double alpha,speedX,speedY;
    uint64_t fadeUs,gapUs,availableUs;
    int layout;
}
Area;
typedef struct {
    int id,labelCount,dismiss;
    uint32_t label[NR_ACTION_LABEL];
    char event[128];
    double value;
} NotificationAction;
typedef struct {
    int used,messageId,actionId;
    uint64_t id,messageSequence,atUs;
    char event[128];
    double value;
} Intent;
typedef struct {
    int used,id,area,mode,priority,count;
    uint32_t text[NR_MAX_TEXT];
    uint64_t startUs,durationUs,readyUs,sequence;
    int state,x,y;
    char key[64];
    int coalesce,important,acknowledged,actionCount;
    uint32_t occurrences,replacements,actionMask;
    NotificationAction actions[NR_NOTIFICATION_ACTIONS];
}
Message;
typedef struct {
    int used,id,area,x,y,count,material,cursor;
    uint32_t glyphs[128];
    uint64_t stepUs;
}
Indicator;
typedef struct {
    int used,id,pinned,labelCount,detailCount;
    uint32_t label[256],detail[512];
    char kind[48],status[128],sha[129];
    Vec3 position,from,to;
    uint32_t color;
    uint64_t atUs,durationUs;
    int minColumns,maxColumns,padding,shaPrefix,showKind,showStatus,showSha,showDetail;
}
Node;
typedef struct {
    int from,to,kind;
}
Edge;
typedef struct {
    int used,readonly,bindingFamily,bindingId;
    char path[128],field[32];
    double value;
}
Value;
typedef struct {
    int kind,source,comparison,children,end,lastTruth;
    double low,high,hysteresis;
} Condition;
typedef struct {
    int used,id,source,target,comparison,action,lastTruth,pending;
    double threshold,hysteresis,value;
    uint64_t debounceUs,cooldownUs,pendingUs,lastFireUs;
    Condition conditions[NR_CONDITIONS];
    int conditionCount,edge,hasFired,pendingTruth;
    uint32_t fireCount;
    char eventPath[128];
    uint64_t lastIntent,pendingIntent;
}
Trigger;
typedef struct {int kind,ref,childCount;uint8_t children[16];double value;} NumericFormulaNode;
typedef struct {int count,usesIntent;NumericFormulaNode nodes[31];char intentPaths[31][128];} NumericFormula;
typedef struct {uint32_t length,count;char json[4096];JToken tokens[128];} IntentPayload;
typedef struct {int kind,padding;IntentPayload data;} TypedValue;
typedef struct {NumericFormula tree;IntentPayload source;} DataFormula;
typedef struct {
    int roleCount,stateCount,idCount,indexCount,glyphCount,hasIds,hasIndices,hasRect,inkOnly;
    int x,y,width,height;
    char roles[64][129],states[64][129],path[128],prefix[128];
    uint32_t ids[4096],indices[4096],glyphs[4096];
} CharacterSelector;
typedef struct {int type,where;double value;} CharacterEffect;
typedef struct {int count,padding;CharacterEffect entries[32];} CharacterEffects;
int nrCompileCharacterEffects(const Json*,int,CharacterEffects*);
int nrApplyCharacterEffects(const CharacterEffects*,int,const double*,double*);
void nrRotateColorHue(const double*,double,double*);
/* Sampled paint kernel; effects and retained authoring belong to the evaluator. */
typedef struct {
    uint32_t foreground,background,foregroundAlpha,backgroundAlpha;
    uint32_t foregroundBlend,backgroundBlend,operation,seed,space;
    int hasForeground,hasBackground,protectLocalInk;
} CharacterPaint;
typedef struct {
    int enabled,foregroundMaterial,backgroundMaterial,padding;
    double foregroundOpacity,backgroundOpacity;
    CharacterPaint paint;
    CharacterEffects foregroundEffects,backgroundEffects;
} CharacterStyle;
typedef struct {
    char id[129];
    double priority;
    CharacterSelector selector;
    CharacterStyle style;
    int stateCount,padding;
    struct {char name[129];CharacterStyle style;} states[32];
} CharacterRule;
typedef struct {int used,length;char json[4096];} CharacterRuleSource;
typedef struct {
    char id[129],role[129],state[129],path[128];
    int hasRect,hasCells,cellCount,indexCount,x,y,width,height;
    uint32_t cells[4096],indices[4096];
} CharacterRegion;
int nrCompileCharacterRegion(const Json*,int,CharacterRegion*);
int nrCharacterRuleCompare(const CharacterRule*,const CharacterRule*);
int nrApplyCharacterRuleCell(const NrContext*,const CharacterRule*,int,int,NrCell*);
int nrCharacterPaintCell(const NrCell*,const CharacterPaint*,int,NrCell*);
int nrCharacterPaintEffectsCell(const NrCell*,const CharacterPaint*,const CharacterEffects*,const CharacterEffects*,int,int,NrCell*);
int nrCompositeInSpace(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t*);
uint32_t nrMixColorSpace(const double*,const double*,double,uint32_t);
uint32_t nrLabColor(double,double,double);
int nrCompileCharacterSelector(const Json*,int,CharacterSelector*);
int nrCharacterSelectorMatches(const CharacterSelector*,const char*,const char*,const char*,uint32_t,uint32_t,uint32_t,int,int);
typedef struct {
    int used,id,family,targetId,active;
    char path[128],role[48];
} RegisteredState;
typedef struct {
    int family,targetId,prefix;
    char path[128],role[48];
    unsigned stateMask,stateValue;
} StateSelector;
typedef struct {
    int mapped,source;
    double inputMin,inputMax,outputMin,outputMax;
} StyleValue;
typedef struct {
    int used,id,enabled,priority;
    StateSelector selector;
    unsigned propertyMask;
    StyleValue properties[NR_STYLE_PROPERTIES];
    Trigger guard;
} StyleRule;
typedef struct {
    unsigned mask;
    double value[NR_STYLE_PROPERTIES];
} Appearance;
typedef struct {
    Vec3 a,b,c;
    uint32_t color;
    double alpha;
}
Triangle;
typedef struct {
    int used,id,length;
    uint64_t atUs,sequence;
    char command[NR_PENDING_BYTES];
} PendingCommand;
/* Appended state preserves every pre-geometry field offset. Surface IDs are
 * 1..16; zero is the existing floor, never an imported-mesh collision default. */
typedef struct {
    int used,collisionEnabled,renderVisible,maxIndividual,maxTiles,overflow;
    double restitution,friction,settleSpeed,reentrain;
    uint64_t retentionUs,fadeUs;
    double wetnessGain,evaporation,heatGain,cooling,thermalEvaporation;
    double wetnessDarkening,heatTintStrength;
    uint32_t heatColor;
    double wetness,heat;
    uint64_t impacts,rejectedDeposits;
} Surface;
typedef struct {
    Vec3 minimum,maximum;
    int left,right,first,count;
} CollisionNode;
typedef struct {
    int triangleCount,nodeCount;
    int order[NR_MESH];
    CollisionNode nodes[NR_BVH_NODES];
} GeometryIndex;
typedef struct {
    int used,surfaceId,triangleIndex;
    Vec3 normal;
} SurfaceContact;
typedef struct {
    int surfaceId,triangleIndex;
    uint32_t meshGeneration;
    Vec3 normal,a,b,c;
} SurfaceTile;
typedef struct {
    Surface surfaces[NR_SURFACES];
    uint32_t emitterColliders[NR_MAX_EMITTERS];
    int triangleSurfaces[NR_MESH];
    GeometryIndex index;
    SurfaceContact particleContacts[NR_MAX_PARTICLES],depositContacts[NR_DEPOSITS];
    SurfaceTile tileSurfaces[NR_TILES];
    uint32_t meshGeneration;
    uint64_t contactBudgetExhausted,collisionQueries,triangleTests;
} GeometryState;
typedef struct {
    int surfaceId,triangleIndex;
    double fraction;
    Vec3 position,normal,surfaceVelocity;
} GeometryHit;
typedef struct {
    uint32_t id,surfaceId;int used,visible;
    Vec3 position,velocity,normal;
    double mass,radius,density,gravity,drag,immersion,buoyantForce;
    uint32_t color,padding;
} FloatBody;
#define NR_FLOAT_BODIES 64
typedef struct {
    uint32_t used,vertexCount,faceCount,padding;
    Vec3 vertices[128];uint32_t faces[256][3];
    double orientation[4]; /* XYZW unit quaternion, local to world */
    Vec3 angularVelocity,inertia,centerOfMass;
    double volume;
} FloatHull;
typedef struct {
    uint32_t used,padding;double mass;
    Vec3 velocity,initialMomentum,bodyImpulse,offset;
    double dissipatedEnergy,initialEnergy;
} SurfaceFluid;
typedef struct {
    double mass,energy;Vec3 momentum,initialMomentum,bodyImpulse;
    double initialEnergy,dissipatedEnergy;uint64_t exports;
} SurfaceFluidHistory;
/* Retained angular record: lifecycle follows its owning finite-water record. */
typedef struct {
    uint32_t used,padding;
    double inertia;
    Vec3 omega,initialMomentum,bodyImpulse;
    double dissipatedEnergy,initialEnergy;
} SurfaceFluidAngular;
_Static_assert(sizeof(SurfaceFluidAngular)==104,"Angular fluid record layout");
typedef struct {
    double inertia,energy;
    Vec3 momentum,initialMomentum,bodyImpulse;
    double initialEnergy,dissipatedEnergy;
    uint64_t exports;
} SurfaceFluidAngularHistory;
_Static_assert(sizeof(SurfaceFluidAngularHistory)==112,"Angular history layout");
int nrAngularFluidHistoryValid(const SurfaceFluidAngularHistory*);
int nrAngularFluidArchive(SurfaceFluidAngularHistory*,const SurfaceFluidAngular*);
int nrSurfacePoseAdvance(const double*,Vec3,double,double*);
int nrFluidPointDragExchange(double,double,double,double,double,Vec3,Vec3,Vec3,Vec3,double*);
double nrDragResponseFraction(double);
int nrLineBreakProperties(const uint32_t*,uint32_t,uint32_t*,uint32_t);
int nrSurfacePoseMotion(const double*,Vec3,Vec3,Vec3,Vec3,Vec3,double*);
int nrSurfacePoseInverse(const double*,Vec3,Vec3,Vec3,Vec3,Vec3,Vec3,double*);
int nrSurfacePoseBounds(const double*,Vec3,Vec3,Vec3,Vec3,const double*,uint32_t,double,double*);
typedef struct {uint32_t used,padding;double orientation[4];Vec3 pivot;} SurfaceFluidPose;
_Static_assert(sizeof(SurfaceFluidPose)==64,"Surface fluid pose layout");
int nrAngularFluidRecordValid(const SurfaceFluidAngular*);
int nrAngularFluidRecordInit(SurfaceFluidAngular*,double,Vec3);
int nrAngularFluidRecordExchange(SurfaceFluidAngular*,Vec3,Vec3,Vec3,double,const double*,Vec3*);
typedef struct {uint32_t id,count,generation,padding;uint32_t source[NR_MAX_TEXT],identities[NR_MAX_TEXT];} TextIdentityRun;
typedef struct {int used,padding;double width,speed,maxDepth;Vec3 direction;} FlowThickness;
typedef struct {uint32_t role,weight[3];} FlowThicknessTriangle;
typedef struct {int used,enabled;double sourceRate,threshold,decay,impactGain;uint32_t color,padding;} FoamSettings;
typedef struct {double density,generated,decayed,saturated;} FoamCell;
typedef struct {FoamSettings settings[NR_SURFACES];FoamCell cells[NR_MESH];uint32_t meshGeneration,padding;} FoamState;
typedef struct {int dimensions,mode,iterations,sweeps,lr;uint32_t seed;double nodeGap,layerGap,depthGap,repulsion,spring,linkLength,damping,timeStep,collision;} SourceGraphOptions;
typedef struct {uint32_t enabled,seed,density,reserved;double radius,exposure,trailMs,textLightness,textChroma;} SourceSky;
typedef struct {uint32_t enabled,kind,flatNavigation,reserved;double fallMs,hueStep,textHueSpeed;} OriginalObservatoryOverlay;
/* Original eight modal layers; only text storage grows with authored content. */
typedef struct {uint32_t offset,count;} SourceModalString;
typedef struct {char id[68];uint32_t kind,dismissible,selected,reserved,reserved2;double atMs;SourceModalString title,body,context,query;} SourceModalEntry;
typedef struct {uint32_t depth,scalars;uint64_t revision;SourceModalString workspace,context,query;uint32_t selected,reserved;SourceModalEntry entries[8];uint32_t ownedCount,activeCount,boxId,association;uint32_t ownedIds[NR_SOURCE_STAGE_COMPONENT_CAPACITY],activeIds[NR_SOURCE_STAGE_COMPONENT_CAPACITY];} SourceModalState;

typedef struct {uint32_t enabled,reserved;SourceGraphOptions options;uint32_t nodeIds[NR_MAX_NODES];double widths[NR_MAX_NODES],heights[NR_MAX_NODES],edgeWeights[NR_EDGES];} SourceGraphLayout;
typedef struct {
    uint32_t magic,schema,seed,width,height,paused,step,nextParticle,nextField;
    uint64_t timeUs,targetUs;
    Camera camera;
    Flight flight;
    Emitter emitters[NR_MAX_EMITTERS];
    Particle particles[NR_MAX_PARTICLES];
    Deposit deposits[NR_DEPOSITS];
    DepositTile tiles[NR_TILES];
    Floor floor;
    Field fields[NR_FIELDS];
    Material materials[NR_MATERIALS];
    LegacyPrompt prompt;
    TextRun text[NR_TEXTS];
    Window legacyWindows[12];
    Widget widgets[NR_WIDGETS];
    Area areas[NR_AREAS];
    Message messages[NR_MESSAGES];
    Intent intents[NR_INTENTS];
    uint64_t nextIntent;
    uint32_t nextMessageId;
    Indicator indicators[NR_INDICATORS];
    Node nodes[NR_MAX_NODES];
    Edge edges[NR_EDGES];
    int edgeCount,selection,dimensions,layoutMode,cycleCount,selectionScroll;
    Value values[NR_VALUES];
    Trigger triggers[NR_TRIGGERS];
    RegisteredState registeredStates[NR_REGISTERED_STATES];
    StyleRule styleRules[NR_STYLE_RULES];
    uint32_t hoverHit,pressedHit;
    Triangle mesh[NR_MESH];
    int meshCount,meshSampling;
    uint32_t background;
    int stars,sampling,style;
    double starFar;
    uint64_t births,rejectedBirths,expired,aggregateCount,depositsRejected,fieldOverflow;
    int pointerActive,pointerKind,pointerId,pointerAlt;
    double pointerX,pointerY;
    int selectedWindow;
    int reducedMotion,screenReader,dockPage;
    uint64_t nextTransaction,nextMessage;
    uint32_t nextEmitterGeneration,nextGlyphIdentity;
    PendingCommand pending[NR_PENDING];
    GeometryState geometry;
    /* Euler XYZ birth-frame degrees; appended to preserve schema-06 offsets. */
    Vec3 birthOrientations[NR_MAX_EMITTERS];
    struct { Vec3 orientation,angularVelocity; int authored,padding; } emitterMotions[NR_MAX_EMITTERS],particleMotions[NR_MAX_PARTICLES];
    struct { uint32_t count,padding; double waves[32][5]; } surfaceWaves[NR_SURFACES];
    FloatBody floatBodies[NR_FLOAT_BODIES];
    FoamState foam;
    struct { uint32_t id,targetId,generation; int used,family,closed,mode,count; uint64_t startUs; double speed,distance; double points[129][3]; } pathActors[16];
    struct {int count,padding;uint64_t revision;} vimCount;
    struct {int key,count;uint64_t revision;} vimOperator;
    struct {uint32_t glyphs[NR_MAX_TEXT];int count,linewise;} vimRegister;
    struct {struct {uint32_t glyphs[NR_MAX_TEXT];int count,linewise;} slots[26];int pending,selected,append,padding;uint64_t revision;} namedRegisters;
    struct {int count,padding;} editorRedo;
    RepeatEdit repeatEdit;
    Flow flows[8];
    struct {uint32_t flowId;int stage;double referenceFlux;} flowSurfaces[NR_SURFACES];
    struct {uint32_t flowId,padding;double fraction;uint64_t evaporationUs,startUs;double initialReceived,initialStored,capacity;} flowSinks[NR_SURFACES];
    struct {uint32_t flowId,generation;double fraction,particleVolume,initialDelivered,emittedVolume;uint64_t startUs;int ordinal,padding;} flowSprays[NR_MAX_EMITTERS];
    struct {uint32_t particleId,emitterSlot;double volume;} sprayParticles[NR_MAX_PARTICLES];
    struct {double expired,impacted,exported,legacyUnresolved;} sprayTerminals[NR_MAX_EMITTERS];
    struct {struct {int used,padding;double capacity;uint64_t evaporationUs;double historicalReceived,historicalEvaporated,historicalExported;} settings[NR_SURFACES];struct {uint32_t surfaceId,padding;uint64_t atUs;double received,stored;} cells[NR_MESH];} surfaceWater;
    struct {double incoming,outgoing;} waterTransfers[NR_MESH],waterHistoricalTransfers[NR_SURFACES];
    struct {uint32_t id,generation;int used,from,to,padding;double rate;uint64_t startUs;} waterLinks[64];
    double sprayReentrained[NR_MAX_EMITTERS];
    struct {int used,padding;uint64_t atUs;double capacity,temperature,ambient,conductance,power,initialEnergy,appliedEnergy,environmentEnergy;} thermalCells[NR_MESH];
    struct {double initial,applied,environment,exported;} thermalHistory;
    struct {double incoming,outgoing;} thermalTransfers[NR_MESH],thermalHistoricalTransfers;
    struct {uint32_t id,generation;int used,from,to,padding;double conductance;uint64_t startUs;} thermalLinks[64];
    struct {int id,used,width,height,x,y,layer,padding;double alpha;uint32_t cells[2048][3];} cellArt[4];
    NumericFormula triggerFormulas[NR_TRIGGERS];
    IntentPayload intentPayloads[NR_INTENTS];
    TypedValue typedValues[NR_VALUES];
    DataFormula triggerDataFormulas[NR_TRIGGERS],triggerGuardFormulas[NR_TRIGGERS],styleGuardFormulas[NR_STYLE_RULES];
    CharacterRuleSource characterRules[128];
    CharacterRuleSource characterRegions[1024];
    struct {double x,z;} foamVelocity[NR_SURFACES];
    struct {double incoming,outgoing;} foamTransfers[NR_MESH];
    FlowThickness flowThickness[NR_SURFACES];
    FlowThicknessTriangle flowThicknessTriangles[NR_MESH];
    uint32_t nextClusterIdentity,nextTextRunGeneration;
    TextIdentityRun legacyTextIdentities[25];
    FloatHull floatHulls[NR_FLOAT_BODIES];
    SurfaceFluid surfaceFluids[NR_SURFACES];
    SurfaceFluidHistory fluidHistory[NR_SURFACES];
    SurfaceFluidAngular angularFluids[NR_SURFACES];
    SurfaceFluidAngularHistory angularHistory[NR_SURFACES];
    SurfaceFluidPose surfacePoses[NR_SURFACES];
    double waterLinkHeatCapacity[64];
    struct {double coefficient,evaporatedEnergy;} latentHeat[NR_MESH];
    double historicalLatentEnergy;
    HeatReservoir materialHeat[NR_MATERIALS],particleHeat[NR_MAX_PARTICLES],depositHeat[NR_DEPOSITS],aggregateHeat[NR_TILES];
    struct {double initial,imported,transferred,exported;} materialHeatLedger;
    AggregateProvenance aggregateProvenance[NR_TILES];
    uint64_t aggregateReemittedCount;
    FieldControls fieldControls[NR_FIELDS];
    struct {int layout,ambiguous;} promptPresentation;
    ElectricalArc electricalArcs[16];
    BurstControls burstControls[NR_MAX_EMITTERS];
    NovaOptics novaOptics[NR_MAX_PARTICLES];
    CoronaControls coronaControls[NR_MAX_EMITTERS];
    ObservatoryControls observatoryControls[NR_MAX_EMITTERS];
    KineticControls kineticControls[NR_MAX_EMITTERS];
    AtelierControls atelierControls[NR_MAX_EMITTERS];
    ThermalSourceControls thermalSourceControls[NR_MAX_EMITTERS];
    WorldSourceControls worldSourceControls[NR_MAX_EMITTERS];
    StudioNovaControls studioNovaControls[NR_MAX_EMITTERS];
    uint32_t textAlphabetTail[NR_TEXTS][128];
    uint32_t legacyWindowSourceGeometry[12];
    uint32_t textPhaseModel[NR_TEXTS];
    PromptFramed promptFramed;
    MaterialPattern materialPatterns[NR_MATERIALS];
    SceneArt sceneArt;
    uint32_t canvasPresentation,canvasReserved;
    struct WindowSourcePresentationStateStorage {
        uint32_t enabled,reserved;
        NrWindowSourcePresentationOptions options;
    } legacyWindowPresentation[12];
    int32_t legacyWindowSourceOrder[12];
    SourceStageState sourceStage;
    LegacyWindowTextures legacyWindowTextures;
    WindowContent legacyWindowContent[12];
    PromptFixed70 promptFixed70;
    struct {uint32_t glyphs[NR_MAX_PROMPT];int count,linewise;} promptRegisterFixed70;
    struct {struct {uint32_t glyphs[NR_MAX_PROMPT];int count,linewise;} slots[26];int pending,selected,append,padding;uint64_t revision;} promptRegistersFixed70;
    struct {uint32_t id,count,generation,padding;uint32_t source[NR_MAX_PROMPT],identities[NR_MAX_PROMPT];} promptIdentityFixed70;
    WindowApplication windowApplication;
    /* Current32window contract pools. All older snapshot offsets stay fixed. */
    Window windows[NR_MAX_WINDOWS];
    TextIdentityRun textIdentities[1+2*NR_MAX_WINDOWS];
    uint32_t windowSourceGeometry[NR_MAX_WINDOWS];
    struct WindowSourcePresentationStateStorage windowPresentation[NR_MAX_WINDOWS];
    int32_t windowSourceOrder[NR_MAX_WINDOWS];
    WindowTextures windowTextures;
    WindowContent windowContent[NR_MAX_WINDOWS];
    uint32_t kineticPaint[NR_MAX_EMITTERS]; /*0material,1original source palette.*/
    OriginalCamera originalCamera;
    SourceAtelierWindow atelierWindows[NR_MAX_WINDOWS];
    AtelierControls atelierApplicationParticles;
    SourceGraphLayout sourceGraphLayout; /* Epoch88 fixed appendix. */
    SourceSky sourceSky; /* Epoch88 original WorldStarfield controls. */
    FirstPromptSource firstPromptSource; /* Epoch89 original prompt surface. */
    struct {uint32_t count,reserved;SceneArt view;} sourceModel; /* Epoch90. */
    SourceStageScene sourceStageScene; /* Epoch91 original Stage scene. */
    OriginalObservatoryOverlay observatoryOverlay; /* Epoch92 source typography/graph/workspace. */
    SourceModalState sourceModal; /* Epoch93 original control stack. */
    CameraControls cameraControls; /* Epoch94 physical rigs and independent input axes. */
    SceneArtClock sceneArtClock; /* Epoch95 independent original scenic sample clock. */
    PromptAppearance promptAppearance;
    OcclusionControls occlusionControls; /* Epoch97 occlusion tint and occluded dots. */
    PromptSourceLayer promptSourceLayer; /* Epoch98 bounded prompt source layer. */
    PromptRuntime dynamicPrompt; /* Runtime views begin here: never serialized. */
    NrModelTriangle *modelRecords;
    uint32_t *modalScalars; /* Separate owned arena view. */
}
State;
#define promptDocument dynamicPrompt.document
#define promptRegister dynamicPrompt.register0
#define promptRegisters dynamicPrompt.registers
#define promptIdentity dynamicPrompt.identity
#define NR_PROMPT_DATA_ARRAYS 31u
#define NR_PROMPT_WIRE_ARRAYS 131u
#define NR_PROMPT_HISTORY 100
#define NR_PROMPT_SCRATCH_ARRAYS 104u
#define NR_PROMPT_ARENA_ARRAYS (3u*(NR_PROMPT_DATA_ARRAYS+NR_PROMPT_SCRATCH_ARRAYS)+2u+4u*16u)
#define NR_INLINE_PROMPT_CAPACITY 4095u
void nrPromptBindInitial(NrContext*);
void nrPromptRuntimeClear(State*);
void nrPromptCoordinates(const State*,int (*)[2]);
void nrPromptCopy(Prompt*,const Prompt*);
int nrPromptHistorySet(State*,int,const uint32_t*,int,int);
void nrStateCopy(State*,const State*);
int nrPromptRequire(State*,uint64_t);
int nrPromptDecodeCommand(State*,const Json*,int,uint32_t**);
uint32_t nrPromptPayloadSize(const State*);
uint32_t nrPromptWireSize(void);
int nrPromptSavePayload(const State*,uint8_t*,uint32_t);
int nrPromptPayloadShape(const uint8_t*,uint32_t,uint32_t);
int nrPromptLoadPayload(State*,const uint8_t*,uint32_t,uint32_t);
uint32_t nrPromptLegacyRequired(const State*,uint32_t);
int nrPromptPromote70(State*);
int nrPromptAllowed(const State*,uint64_t);
typedef struct WindowSourcePresentationStateStorage WindowSourcePresentationState;
int nrWindowPresentationPatch(const Json*,const WindowSourcePresentationState*,double,WindowSourcePresentationState*,double*);
int nrWindowPresentationDrawTheatreToolbar(NrContext*,int,const NrWindowSourcePresentationOptions*,double,uint32_t);
int nrValidWindowPresentation(const State*);
int nrWindowApplicationCommand(NrContext*,State*,const Json*);
int nrWindowApplicationInput(State*,uint64_t priorScalarCount,uint64_t insertedScalarCount);
int nrWindowApplicationDraft(State*,uint64_t priorUtf16Units,uint64_t nextUtf16Units,uint64_t nextScalarCount,int64_t firstDifference);
double nrAtelierWindowTween(const State*s,int slot,int value);
int nrAtelierWindowPatch(NrContext*,State*,const Json*,int);
int nrValidAtelierWindows(const State*);
int nrAtelierWindowAction(State*,int,int);
int nrDrawAtelierWindow(NrContext*,int);
void nrAtelierApplicationChrome(NrContext*);
int nrAtelierApplicationParticlePatch(NrContext*,State*,const Json*,int);
int nrValidAtelierApplicationParticles(const State*);
void nrAtelierApplicationParticles(NrContext*);
void nrAtelierApplicationStars(NrContext*,const NrWindowPaletteSourcePrepared*);
int nrValidWindowApplication(const State*);
void nrWindowApplicationBackground(NrContext*);
uint64_t nrWindowApplicationTimeUs(const State*);
int nrWindowSourceProject(const State*,const Camera*,Vec3,double*,double*,double*);
void nrWindowApplicationChrome(NrContext*);
int nrWindowTextureCommand(NrContext*,State*,const Json*);
int nrValidWindowTextures(const State*);
int nrWindowContentCommand(NrContext*,State*,const Json*);
int nrValidWindowContent(const State*);
int nrWindowContentAction(State*,int,int);
double nrWindowContentVisibility(const State*,int);
double nrWindowContentMaximized(const State*,int);
const uint32_t *nrWindowDocument(const State*,const Window*,int*);
int nrWindowContentTexture(NrContext*,int,uint32_t,uint32_t,const uint32_t**);
double nrWindowOpacity(const State*,int);
int nrSourceStageCommand(NrContext*,State*,const Json*);
int nrValidSourceStage(const State*);
void nrSourceStageDraw(NrContext*,const State*);
int nrSourceStageSceneCommand(NrContext*,State*,const Json*);
int nrValidSourceStageScene(const State*);
int nrValidOriginalObservatoryOverlay(const State*);
int nrOriginalObservatoryOverlayCommand(NrContext*,State*,const Json*);
void nrDrawOriginalObservatoryOverlay(NrContext*,const WindowApplication*,const NrWindowPaletteSourcePrepared*,double);
void nrSourceStageBackground(NrContext*,const State*);
void nrSourceStageQuantize(NrContext*,const State*);
void nrSourceStagePalette(const SourceStageScene*,NrSourceMaterialSampler*);
uint64_t nrSourceStageTime(const State*);
void nrSceneViewport(const State*,int*,int*);
typedef struct { int x,y,width,height; } ClipRect;
typedef struct {
    int32_t depth;
    uint32_t rgb;
    uint16_t alpha,blend;
    uint32_t owner;
    uint16_t detail,sampling;
}
Fragment;
typedef struct {
    Vec3 position,right,up,forward;
    double focal,cx,cy;
    int orthographic;
    double nearPlane,farPlane,scale;
    int sourceEnabled;
    NrScenicSourceRaster source;
}
Projection;
int nrDrawWindowTexture(NrContext*,const Projection*,int);
/* Inline scratch is an allocation optimization, never a viewport limit. */
#define NR_INLINE_CELLS 24000u
#define NR_RENDER_BYTES_PER_CELL (sizeof(NrCell)+8u*NR_LAYERS*sizeof(Fragment)+8u+8u*sizeof(uint32_t)+1u+8u*sizeof(uint32_t)+2u*sizeof(uint32_t)+8u*sizeof(int32_t)+sizeof(double)+8u*sizeof(uint32_t)+8u*sizeof(int32_t))
#define NR_INLINE_RENDER_BYTES ((NR_INLINE_CELLS*NR_RENDER_BYTES_PER_CELL+95u)&~7u)
/* Command path (native/docs/TRANSACTIONS.md; TDD-STATE-COPY-ELIMINATION-20261102.md section 5.6). nrInit seeds every
 * context's commandPathLimit from NR_COMMAND_FASTPATH: bit NR_PATH_DIRECT allows direct (plan/commit) transactions,
 * bit NR_PATH_SEGMENTS is reserved, and a value outside 0..3 is treated as 0. This line is the rollback lever and the
 * only default: 0 restores the copy transaction for every command. build.py's NOCTURNE_COMMAND_FASTPATH overrides it
 * for build.py's own outputs only. */
#ifndef NR_COMMAND_FASTPATH
#define NR_COMMAND_FASTPATH 1
#endif
#define NR_PATH_DIRECT 1u
#define NR_PATH_SEGMENTS 2u
/* Direct transactions (native/docs/TRANSACTIONS.md). nrDirectApply plans an op against the live State and, inside
 * its plan's domain, commits it in place; outside the domain it returns NR_DIRECT_DECLINED and writes nothing, and
 * nrCommand runs the copy transaction exactly as before. It runs only while the context is settled. */
#define NR_DIRECT_DECLINED 0x7ffe
#define NR_UNDO_BYTES 65536u
#define NR_UNDO_RANGES 64
typedef struct {unsigned char *at;uint32_t offset,length;} NrUndoRange;
/* The bounded record journal of a direct commit: the old bytes of each declared record, restored if a scoped
 * validator rejects the result. Never serialized; empty between commands. */
typedef struct {uint32_t count,used,journaled,padding;NrUndoRange ranges[NR_UNDO_RANGES];unsigned char bytes[NR_UNDO_BYTES];} NrUndo;
/* Deterministic work counters, in every build: State bytes in the copy primitive, bytes in the memcmp gates, full
 * validations at the nrValidState call sites (never inside a validator), and render, schedule and pending probe
 * syncs. They live in the context, never in State, and are never serialized. */
typedef struct { uint64_t direct, fallback, hotBytes, coldBytes, runtimeBytes, comparedBytes,
                 fullValidations, probeSyncs, auditFaults; } NrCommandCounters;      /* 72 B */
struct NrContext {
    uint32_t valid,capacity;
    State state,trial,probe;
    Prompt promptResetBackup;uint32_t *promptCheckpointBackup;
    uint32_t *documentLayout,*documentClip;
    void *modalMemory;uint64_t modalMemoryBytes,modalRequiredBytes;
    uint32_t modalCapacity,modalRequestedCapacity;
    void *modelMemory;uint64_t modelMemoryBytes,modelRequiredBytes;
    uint32_t modelCapacity,modelRequestedCapacity;
    void *promptMemory;uint64_t promptMemoryBytes,promptRequiredBytes;
    uint32_t promptMemoryCapacity,promptRequestedCapacity;
    uint64_t promptHistoryWords,promptRequestedHistoryWords;
    uint32_t inlinePromptMemory[(NR_INLINE_PROMPT_CAPACITY+1u)*NR_PROMPT_ARENA_ARRAYS];
    Json json,subjson,repeatJson,projectedJson,scheduledJson;
    TypedValue typedBefore[NR_VALUES];
    IntentPayload dataScratch[31];
    DataFormula dataFormulaScratch;
    Json characterJson;
    CharacterRule characterRuleScratch,characterRuleCache[128];
    int characterRuleCount;
    int characterRuleOrder[128];
    CharacterRegion characterRegionScratch,characterRegionCache[1024];
    int characterRegionCount;
    int characterFrameValid;
    int executingPendingId;
    int checkingPending;
    TextRun probeTextBackup;
    uint32_t probeTextAlphabetTailBackup[128];
    uint32_t probeTextPhaseModelBackup;
    Node probeNodeBackup;
    Emitter probeEmitterBackup;
    BurstControls probeEmitterBurstBackup;
    CoronaControls probeEmitterCoronaBackup;
    ObservatoryControls probeEmitterObservatoryBackup;
    KineticControls probeEmitterKineticBackup;
    uint32_t probeEmitterKineticPaintBackup;
    AtelierControls probeEmitterAtelierBackup;
    ThermalSourceControls probeEmitterThermalSourceBackup;
    WorldSourceControls probeEmitterWorldSourceBackup;
    StudioNovaControls probeEmitterStudioNovaBackup;
    Vec3 probeEmitterBirthBackup;
    unsigned char probeEmitterMotionBackup[sizeof(((State*)0)->emitterMotions[0])];
    uint32_t probeEmitterColliderBackup;
    unsigned char probeEmitterSprayBackup[sizeof(((State*)0)->flowSprays[0])];
    char projectedText[NR_MAX_COMMAND+32];
    NrCell *cells;
    Fragment (*fragments)[NR_LAYERS];
    uint8_t *fragmentCounts;
    uint32_t *legacyFragmentOverflow; /* Three-slot minus six-slot overflow, per sample. */
    uint32_t *backgroundPixels;
    /* Source-order scene depth in the common sample grid; colors live in
     * backgroundPixels. All presentation scratch, never snapshot authority. */
    int32_t *sourceDepth;
    int32_t *sourcePickDepth; /* Visible source samples, independent of occlusion alpha. */
    double *windowDepth; /* Cell texture depth, presentation scratch only. */
    NrWindowPaletteSourceConfig windowPaletteConfig[NR_MAX_WINDOWS];
    NrWindowPaletteSourcePrepared windowPalette[NR_MAX_WINDOWS];
    uint32_t windowPaletteValid[NR_MAX_WINDOWS];
    uint32_t windowContentCells[7200][4];
    int sourceActive,sourceWidth,sourceHeight,sourceSampling,sourceOrthographic;
    uint32_t sourceBackground;
    /* Presentation-only scratch, excluded from snapshots. One complete widget at a time. */
    uint8_t *plotMask;
    uint32_t (*plotColor)[8];
    /* Local source scalar index of the visible glyph; UINT32_MAX means no
     * authored source index. This is presentation scratch, never scene state. */
    uint32_t *characterIndices;
    /* Registered-family/target pair, independent of interactive hit IDs. */
    uint32_t *characterOwners;
    uint32_t characterOwner;
    uint64_t renderMemoryBytes;
    uint64_t inlineRenderMemory[NR_INLINE_RENDER_BYTES/8u];
    char info[NR_INFO_SIZE],error[256];
    uint32_t fragmentOverflow,contentNeedsReader,clippedPrimitives;
    int screenWidth,screenHeight,promptTop,paintBlend;
    int deferValues,valuesDirty;
    int rendering; /* Select probe as read-only presentation scratch, never authority. */
    /* Raster ownership is scratch only; it never enters simulation snapshots. */
    uint32_t paintOwner;
    int paintDetail,paintSampling;
    int paintMaterialId; /* 0 disables spatial pattern sampling; otherwise material+1. */
    ClipRect clip;
    /* Command-path bookkeeping (section 5.6). Set by nrInit; changed only at the named call sites (I16). */
    NrCommandCounters counters;
    uint32_t commandPathLimit;
    /* 1 only while c->state is the result of an accepted copy transaction (or of direct commits after one): valid,
     * and a fixed point of the post-command pipeline (sync, styles tick, mirror). Cleared by every other writer. */
    uint32_t settled;
    NrUndo undo;
    Widget widgetPlan; /* planWidget's record (commands.c): scratch, never authority */
    Node nodePlan; /* planNode's record: scratch, never authority */
#ifdef NR_BENCH_HOOKS
    double benchBodyMs; /* bench builds only: wall time inside direct plans and commits (TRANSACTIONS.md) */
#endif
};
int nrExternalOutput(const NrContext*,const void*,size_t);
/* command_path.c */
uint32_t nrCommandPathInitialLimit(void);
void nrCountStateCopy(NrContext*,uint64_t runtimeBytes);
int nrCountedValidState(NrContext*,const State*);
int nrCopyTransaction(NrContext*,State*);
int nrShadowDirect(NrContext*);
void nrShadowFrame(NrContext*);
int nrDirectApply(NrContext*,const Json*);
int nrValidWidget(const State*,const Widget*);
int nrValidNode(const State*,const Node*);
int nrSyncPromptIdentity(State*);
int nrValidGlyphs(const uint32_t*,int,int);
int nrValidPointerCamera(const State*);
void nrPromptMirrorDocument(State*);
void nrPromptMirrorCaret(State*);
int nrUndoSave(NrContext*,const void*,size_t);
void nrUndoRestore(NrContext*);
int nrStateDiffers(const NrContext*,const State*,const State*,char*,size_t);
int nrModelRequire(State*,uint32_t);
int nrValidSourceModel(const State*);
int nrValidSourceModal(const State*);
int nrSourceModalCommand(NrContext*,State*,const Json*);
int nrModalLoadPayload(State*,const uint8_t*,uint32_t);
void nrModalCopyState(State*,const State*);
int nrModalBlocking(const State*);
int nrModalPointerOwns(const State*,double,double);
void nrModalForgetComponent(State*,uint32_t);
int nrModalOwnsComponent(const State*,uint32_t);
int nrModalActiveComponent(const State*,uint32_t);
int nrModalAssociationReady(const State*);
int nrModalDismiss(State*);
void nrSourceStageDrawModal(NrContext*,const State*);
const char *nrModalKind(uint32_t);

int nrModelLoadPayload(State*,const uint8_t*,uint32_t);
void nrModelCopyState(State*,const State*);
int nrModelViewCommand(NrContext*,State*,const Json*);
int nrSourceModelEffective(const State*,int,int,NrScenicArtConfig*);
int nrSourceModelDraw(NrContext*,const State*,int,int);
int nrResolveArea(const State*,uint32_t,int64_t*);
int nrPromptHardBreak(uint32_t);
int nrPromptLogical(const State*,uint32_t*);
void nrPromptGraphemeCoordinates(const State*,int [NR_MAX_TEXT+1][2]);
int nrPromptGraphemeHit(const State*,int,int);
int nrPromptVisualRows(const State*,uint32_t*);
int nrPromptVisualMap(const State*,double*);
int nrPromptSpanVisible(const State*,int,int,int);
void nrFieldControlsInit(FieldControls*);
int nrFieldLive(const State*,int);
void nrFieldCenter(const State*,int,double*,double*);
int nrValidOriginalField(const State*,int);
void nrDrawOriginalFields(NrContext*);
void nrFieldCurve(const State*,int,double,uint32_t*,double*);
void nrFieldCurveAt(const State*,int,double,int32_t,int32_t,uint32_t*,double*);
void nrSourceFieldCurve(const State*,int,double,uint32_t*,double*);
int nrSourceFieldHit(const State*,int,double,double);
int nrFieldContains(const State*,int,double,double);
int nrValidFieldControls(const State*);
int nrValidViewport(uint32_t width,uint32_t height);
/* Styles: bounded command compilation, pure resolution, explicit state tick. */
int nrStyleCommand(NrContext*,State*,const Json*);
int nrValidStyles(const State*);
int nrStylesTick(NrContext*,State*);
void nrPrepareAppearance(NrContext*);
static inline const State *nrView(const NrContext*c) {return c->rendering?&c->probe:&c->state;}
int nrAuthoredAppearance(const State*,const RegisteredState*,Appearance*);
unsigned nrEffectiveAppearance(const State*,const RegisteredState*,Appearance*);
unsigned nrRegisteredFlags(const State*,const RegisteredState*);
const RegisteredState*nrCharacterRegisteredOwner(const State*,uint32_t);
const RegisteredState*nrCharacterSemanticOwner(const State*,uint32_t);
int nrCompileCharacterRule(const State*,const Json*,int,CharacterRule*);
int nrCharacterRuleCommand(NrContext*,State*,const Json*);
int nrCharacterRegionCommand(NrContext*,State*,const Json*);
int nrValidateCharacterRegions(NrContext*,const State*);
void nrCacheCharacterRegions(NrContext*);
int nrValidateCharacterRules(NrContext*,const State*);
void nrCacheCharacterRules(NrContext*);
void nrDrawCharacterRules(NrContext*);
void nrDrawCharacterRegions(NrContext*);
void nrCharacterCellOwner(const NrContext*,size_t,const char**,const char**,const char**);
uint32_t nrCharacterFragmentOwner(const State*,uint32_t);
int nrCharacterCellMatches(const NrContext*,const CharacterSelector*,int,int);
const char *nrStyleFamilyName(int);
const char *nrStylePropertyName(int);
const char *nrStyleStateName(int);
double nrClamp(double v,double lo,double hi);
double nrAbs(double v);
double nrFloor(double v);
double nrSin(double degrees);
double nrCos(double degrees);
double nrSqrt(double v);
double nrEase(double p,int easing);
double nrTrack(const Track*,uint64_t us,double index);
uint32_t nrHash(uint32_t value);
double nrRandom(uint32_t seed,uint32_t id,uint32_t purpose);
Vec3 nrV(double,double,double);
Vec3 nrAdd(Vec3,Vec3);
Vec3 nrSub(Vec3,Vec3);
Vec3 nrScale(Vec3,double);
double nrDot(Vec3,Vec3);
Vec3 nrCross(Vec3,Vec3);
Vec3 nrNormal(Vec3);
QVec3 nrQuantize(Vec3);
Vec3 nrUnquantize(QVec3);
uint32_t nrRgb(double,double,double);
uint32_t nrMix(uint32_t,uint32_t,double);
void nrBasis(const Camera*,Vec3*,Vec3*,Vec3*);
int nrParse(Json*,const char*,int);
int nrField(const Json*,int,const char*);
int nrAllowed(const Json*,int,const char*);
int nrDecode(const Json*,int,uint32_t*,int);
int nrStringSpan(const char*,int,int,char*,int);
int nrGraphemeBefore(const uint32_t*,int,int);
int nrGraphemeAfter(const uint32_t*,int,int);
int nrGraphemeFloor(const uint32_t*,int,int);
int nrString(const Json*,int,char*,int);
int nrEqual(const Json*,int,const char*);
int nrNumber(const Json*,int,double*);
int nrDecimalNumber(const char*,int,double*);
int nrJsonNumber(double,char*,int);
int nrBoolean(const Json*,int,int*);
uint32_t nrCrc(const void*,uint32_t);
void nrDefaults(State*,uint32_t);
int nrValidState(const State*);
int nrApply(NrContext*,State*,const Json*);
int nrSyncTextIdentities(State*);
int nrProbeTextIdentities(NrContext*,State*);
int nrValidTextIdentities(const State*);
int nrTransaction(NrContext*,State*,const Json*);
int nrApplyScheduled(NrContext*,State*);
int nrCheckPending(NrContext*,const State*);
uint32_t nrStepAt(uint64_t us);
int nrSimulate(State*);
Camera nrCameraAt(const State*);
Camera nrCameraCarrierAt(const State*);
Camera nrCameraCarrierAtTime(const State*,uint64_t);
int nrCameraPathOwned(const State*);
int nrCameraControlsCommand(NrContext*,State*,const Json*);
int nrValidCameraControls(const State*);
Camera nrCameraControlsCompose(const State*,Camera,uint64_t);
void nrCameraControlInput(State*,double,double,double,int);
Camera nrOriginalCameraAt(const State*);
int nrOriginalCameraCommand(NrContext*,State*,const Json*);
int nrValidOriginalCamera(const State*);
void nrOriginalCameraStop(State*);
void nrPointerRelease(State*);
void nrCameraManualPose(State*,const Camera*,const Camera*);
void nrOriginalCameraGrab(NrContext*,State*,double,double);
void nrOriginalCameraDrag(State*,double,double,int);
double nrWindowVisibility(const Window*,uint64_t);
Vec3 nrNodeAt(const Node*,uint64_t);
int nrSelectNode(State*,int,uint64_t);
int nrGraphSourceLayout(NrContext*,State*,const Json*);
int nrValidSourceGraphLayout(const State*);
int nrSourceSkyCommand(NrContext*,State*,const Json*);
int nrValidSourceSky(const State*);
void nrDrawSourceSky(NrContext*);
Camera nrCameraAtTime(const State*,uint64_t);
Camera nrOriginalCameraAtTime(const State*,uint64_t);
void nrGraphLayout(State*,int,int,double,int);
int nrEffectId(const char*);
int nrEffectFamily(int);
int nrEffectAlgorithm(int);
int nrEffectProfile(int);
const char *nrEffectName(int);
void nrInitMaterial(Material*,int);
uint32_t nrPaint(const State*,int,uint64_t,double,double*);
uint32_t nrPaintAt(const State*,int,uint64_t,int32_t,int32_t,double,double*);
int nrMaterialPatternCommand(NrContext*,State*,const Json*,int);
int nrValidMaterialPatterns(const State*);
int nrSceneArtCommand(NrContext*,State*,const Json*);
int nrValidSceneArt(const State*);
int nrSceneArtEffective(const State*,int,int,NrScenicArtConfig*);
void nrRenderAll(NrContext*);
void nrResolveLayerCell(NrContext*,unsigned,unsigned,NrCell*);
void nrResolveSamples(NrCell*,const uint32_t*,const uint32_t*,unsigned,int);
/* Hybrid (3) dictates one class per object from its family, 2 braille or 1 half
 * (docs/MIXED-LAYERS.md, Hybrid dictation); it never mixes an object between them.
 * Paint sites apply it to the effective policy in render scratch; state keeps 3. */
static inline int nrDictatedSampling(int policy,int family) {return policy==3?family:policy;}
int nrDrawPlot(NrContext*,const Widget*,int,int,int,int,uint32_t,double,uint32_t,double);
int nrNodeWidth(const Node*);
int nrNodeHeight(const Node*,int);
int nrWindowReaderPageRows(const State*);
int nrWindowReaderMaxScroll(const State*,const Window*);
void nrDrawUI(NrContext*,const Projection*);
void nrDrawSceneGeometry(NrContext*,const Projection*);
int nrEndStyleSupported(int,int);
int nrParticlePose(const State*,int,Vec3*,Vec3*);
void nrDrawWeather(NrContext*,const Projection*);
void nrProjection(const State*,int,int,Projection*);
int nrProject(const Projection*,Vec3,double*,double*,double*);
void nrPoint(NrContext*,const Projection*,Vec3,uint32_t,double,double);
void nrLine(NrContext*,const Projection*,Vec3,Vec3,uint32_t,double);
void nrTriangle(NrContext*,const Projection*,Triangle);
void nrPixel(NrContext*,int,int,double,uint32_t,double);
void nrUseMaterial(NrContext*,int);
void nrCellBackground(NrContext*,int,int,uint32_t,double);
ClipRect nrClip(NrContext*,int,int,int,int);
int nrInClip(const NrContext*,int,int);
void nrGlyph(NrContext*,int,int,uint32_t,uint32_t,double,uint32_t);
void nrIndexedGlyph(NrContext*,int,int,uint32_t,uint32_t,double,uint32_t,uint32_t);
void nrText(NrContext*,int,int,const uint32_t*,int,int,uint32_t,double,uint32_t);
void nrBox(NrContext*,int,int,int,int,int,uint32_t,double,uint32_t);
int nrPromptRows(const State*);
int nrPromptFramedCommand(NrContext*,State*,const Json*);
int nrPromptFramedValid(const State*);
int nrPromptFramedInput(const State*,NrPromptSourceInput*);
int nrPromptFramedLayout(const State*,NrPromptSourceInput*,NrPromptSourceLayout*);
void nrPromptFramedPaint(NrContext*,const State*);
int nrPromptFramedHit(const State*,int,int);
int nrPromptFramedActivate(NrContext*,State*,int);
int nrPromptFramedKey(NrContext*,State*,const Json*,int,int,int,int);
void nrPromptFramedCoordinate(const State*,int,int*,int*);
int nrPromptColumns(const State*);
void nrPromptCoordinate(const State*,int,int*,int*);
int nrPromptHit(const State*,int,int);
int nrPromptVertical(const State*,int,int);
int nrDocumentGraphemeLayout(const uint32_t*,uint32_t,uint32_t,uint32_t,uint32_t*,uint32_t);
int nrPromptStoragePromote(State*);
void nrPromptStorageMirror(State*);
int nrPromptStorageValid(const State*);
int nrInputOwner(const State*); /* 0 prompt, 1 modal, 2 reader */
int nrInput(State*,const uint32_t*,int,int);
int nrValuesTick(NrContext*,State*);
int nrCompileTriggerFormula(const State*,const Json*,int,NumericFormula*);
int nrEvalTriggerFormula(const NumericFormula*,const double*,const Intent*,const IntentPayload*,double*);
int nrValidTriggerFormulas(const State*);
int nrEvaluateValues(NrContext*,State*);
int nrParseConditions(const State*,const Json*,int,Trigger*);
int nrConditionTruth(Trigger*,const double*,const Intent*);
int nrValidConditions(const State*,const Trigger*);
void nrStatusTick(State*);
int nrNotificationCommand(NrContext*,State*,const Json*);
int nrHostEventCommand(NrContext*,State*,const Json*);
int nrIntentPayloadStorageValid(const State*);
int nrValidateIntentPayloads(NrContext*,const State*);
int nrPayloadPathValid(const char*);
int nrPayloadNumber(const IntentPayload*,const char*,double*);
int nrPayloadResolve(const IntentPayload*,const char*,int*);
int nrPayloadFromJson(const Json*,int,IntentPayload*);
int nrPayloadSlice(const IntentPayload*,int,IntentPayload*);
int nrTypedSet(State*,int,const Json*,int);
int nrTypedAssign(State*,int,const IntentPayload*);
int nrFormulaUnitRef(const Json*,int,int);
int nrNumericOperation(int,int,const double*,int,double*);
int nrCompileDataFormula(const State*,const Json*,int,DataFormula*);
int nrEvalDataNumber(NrContext*,const State*,const DataFormula*,const double*,const TypedValue*,const Intent*,double*);
int nrDataNumericExpression(NrContext*,const State*,const Json*,int,int,double*);
int nrEvalDataFormula(NrContext*,const State*,const DataFormula*,const double*,const TypedValue*,const Intent*,IntentPayload*);
int nrValidateDataFormulas(NrContext*,const State*);
int nrTypedExpression(NrContext*,State*,int,const Json*,int,int);
int nrTypedApply(State*,const Value*,const TypedValue*);
int nrTypedBindingValid(const Value*,int);
int nrTypedStorageValid(const State*);
int nrWidgetDataPayloadValid(const IntentPayload*);
int nrDecodeSpan(const char*,int,int,uint32_t*,int);
int nrNotificationActivate(NrContext*,State*,int,int);
int nrEventPath(const char*);
int nrPendingExpressionShape(NrContext*,const State*,const Json*,int,int);
int nrNumericExpression(const State*,const Json*,int,int,double*);
int nrValueInUse(NrContext*,const State*,int);
void nrProbeReleaseValueConsumers(NrContext*,State*,const char*);
int nrBindValue(State*,const Value*,double);
int nrBindMaterialValue(State*,const Value*,double);
int nrBindEmitterValue(State*,const Value*,double);
int nrBindTextValue(State*,const Value*,double);
int nrBindFloorValue(State*,const Value*,double);
int nrBindNodeValue(State*,const Value*,double);
int nrBindIndicatorValue(State*,const Value*,double);
int nrBindSceneValue(State*,const Value*,double);
int nrValueNumberValid(const Value*,double);
int nrFindNode(const State*,int);
int nrFindWindow(const State*,int);
int nrFindEmitter(const State*,int);
int nrFoamCommand(NrContext*,State*,const Json*);
int nrValidFoam(const State*);
int nrPathTravelCommand(NrContext*,State*,const Json*);
int nrPathActorsTick(State*);
int nrFlowCommand(NrContext*,State*,const Json*);
int nrFlowSetRate(State*,uint32_t,double);
int nrBindSurfaceValue(State*,const Value*,double);
int nrBindWaveValue(State*,const Value*,double);
int nrEmitterNumberValid(NrContext*,State*,const Value*,double);
int nrFloatBodyNumberValid(const Value*,double);
int nrWaveBindingNumberValid(const Value*,double);
int nrDormantBindingNumberValid(const Value*,double);
int nrBindFloatBodyValue(State*,const Value*,double);
int nrBindFoamValue(State*,const Value*,double);
int nrBindCellArtValue(State*,const Value*,double);
int nrResourceBindingShapeValid(const Value*);
int nrLegacyBindingShapeValid(const Value*);
int nrBindMeshAppearance(State*,const Value*,double);
int nrMeshStyleCommand(NrContext*,State*,const Json*);
int nrValidFlows(const State*);
int nrFlowVolumes(const State*,int,double*);
int nrFlowVolumesAt(const State*,int,uint64_t,double*);
double nrFlowStageFluxAt(const State*,int,int,uint64_t);
int nrFlowSurfaceCommand(NrContext*,State*,const Json*);
int nrFlowThicknessCommand(NrContext*,State*,const Json*);
int nrFlowThicknessSettingsShape(const Json*);
int nrBindFlowThicknessValue(State*,const Value*,double);
int nrValidFlowThickness(const State*);
int nrFlowThicknessGeometryEditAllowed(const State*,const Json*);
int nrFlowThicknessTriangleAt(const State*,int,uint64_t,Triangle*);
int nrSurfaceTriangleAtTime(const State*,int,double,Triangle*,Vec3*);
int nrRotatingSurfaceHit(const State*,int,Vec3,Vec3,double,double,double,GeometryHit*);
Vec3 nrFlowThicknessVelocity(const State*,int,Vec3);
int nrFlowThicknessHit(const State*,int,Vec3,Vec3,double,double,double,GeometryHit*);
int nrFinishFlowThicknessMesh(NrContext*,State*,int,int);
void nrFlowSurfaceAlpha(const State*,double*);
int nrFlowSinkCommand(NrContext*,State*,const Json*);
int nrValidFlowSinks(const State*);
void nrFlowSinkVolumes(const State*,int,double*);
int nrFlowSprayCommand(NrContext*,State*,const Json*);
int nrValidFlowSprays(const State*);
void nrFlowSprayVolumes(const State*,int,double*);
int nrFlowSprayDue(const State*,int);
void nrFlowSpraySpawn(State*,int,int);
void nrFlowSprayRelease(State*,int,int);
int nrValidSprayParticles(const State*);
void nrFlowSprayLifecycle(const State*,int,double*);
void nrFlowSprayPromote(State*);
int nrSurfaceWaterCommand(NrContext*,State*,const Json*);
int nrSurfaceWaterTransferCommand(NrContext*,State*,const Json*);
int nrSurfaceWaterLinkCommand(NrContext*,State*,const Json*);
int nrSurfaceWaterTransport(State*);
int nrValidWaterLinks(const State*);
int nrSurfaceWaterReemitCommand(NrContext*,State*,const Json*);
int nrThermalCommand(NrContext*,State*,const Json*);
int nrThermalSettingsShape(const Json*);
int nrSurfaceWaterAddShape(const Json*);
int nrSurfaceWaterAddCommand(NrContext*,State*,const Json*);
int nrSurfaceWaterSettingsShape(const Json*);
int nrSurfaceWaterSettingsCommand(NrContext*,State*,const Json*);
int nrBindWaterValue(State*,const Value*,double);
int nrBindThermalValue(State*,const Value*,double);
int nrElectricalArcCommand(NrContext*,State*,const Json*);
int nrBurstBindingField(const char*);
int nrBindBurstValue(State*,const Value*,double);
int nrBindElectricalValue(State*,const Value*,double);
int nrBurstStyleCommand(NrContext*,State*,const Json*);
int nrValidBurstControls(const State*);
int nrCoronaStyleCommand(NrContext*,State*,const Json*);
int nrObservatoryStyleCommand(NrContext*,State*,const Json*);
int nrKineticStyleCommand(NrContext*,State*,const Json*);
int nrAtelierStyleCommand(NrContext*,State*,const Json*);
int nrThermalSourceCommand(NrContext*,State*,const Json*);
int nrWorldSourceCommand(NrContext*,State*,const Json*);
int nrStudioNovaCommand(NrContext*,State*,const Json*);
int nrValidStudioNovaControls(const State*);
int nrStudioNovaProfile(const State*,int);
int nrStudioNovaSample(const State*,int,StudioNovaSample*);
int nrStudioNovaCenter(const State*,int,double[3]);
void nrDrawStudioNova(NrContext*,const Projection*);
uint32_t nrStudioNovaRing(const StudioNovaControls*,uint64_t,int64_t,int64_t);
uint32_t nrStudioNovaRingColor(const StudioNovaControls*,int64_t,int64_t);
int nrWorldSourceProfile(const State*,int);
int nrValidWorldSourceControls(const State*);
int nrWorldSourceSample(const State*,int,WorldSourceSample*);
void nrWorldOriginalProjection(const State*,const Projection*,Projection*);
void nrStudioOriginalRippleTileCell(const StudioNovaControls*,uint64_t,int,int,NrCell*);
int nrThermalSourceProfile(const State*,int);
int nrValidThermalSourceControls(const State*);
int nrThermalSourceSample(const State*,int,ThermalSourceSample*);
int nrThermalSourceProjectSegment(const Projection*,Vec3,const double*,double[6]);
int nrThermalOriginalProjectSegment(const Projection*,Vec3,const double*,double[6]);
void nrDrawThermalSource(NrContext*,const Projection*);
void nrDrawWorldSource(NrContext*,const Projection*);
uint32_t nrSourcePrimitiveColor(uint32_t,double);
void nrSourceScreenSegment(NrContext*,const double*,uint32_t,double,int,uint32_t);
int nrValidAtelierControls(const State*);
int nrAtelierProfile(const State*,int);
int nrAtelierSampleAt(const AtelierControls*,int,double,AtelierSample*);
int nrAtelierSample(const State*,int,AtelierSample*);
int nrAtelierCenter(const State*,int,double[3]);
void nrDrawAtelier(NrContext*,const Projection*);
int nrValidKineticControls(const State*);
int nrKineticProfile(const State*,int);
int nrKineticSample(const State*,int,KineticSample*);
int nrKineticCenter(const State*,int,double[3]);
void nrDrawKinetic(NrContext*,const Projection*);
int nrValidObservatoryControls(const State*);
int nrObservatoryProfile(const State*,int);
int nrObservatorySample(const State*,int,int,double[5]);
int nrObservatoryCenter(const State*,int,double[3]);
void nrDrawObservatory(NrContext*,const Projection*);
int nrValidCoronaControls(const State*);
int nrCoronaAppearance(const State*,int,double,double[5]);
int nrCoronaCenter(const State*,int,double[3]);
void nrDrawCorona(NrContext*,const Projection*);
BurstControls nrBurstControls(const State*,int);
int nrBurstAppearance(const State*,int,double[4]);
int nrValidNovaOptics(const State*);
int nrNovaAppearance(const State*,int,double[4]);
uint32_t nrColorWithHue(uint32_t,double);
int nrValidElectricalArcs(const State*);
int nrElectricalSegments(const State*,const ElectricalArc*,double[31][7],double*,int*,uint64_t*);
void nrDrawElectricalArcs(NrContext*,const Projection*);
int nrMaterialHeatCommand(NrContext*,State*,const Json*);
int nrAggregateReemitCommand(NrContext*,State*,const Json*);
int nrAggregateCompatible(const State*,int,int);
void nrAggregateCapture(State*,int,int);
int nrValidAggregateProvenance(const State*);
int nrValidMaterialHeat(const State*);
void nrHeatSpawn(State*,int);
void nrHeatRelease(State*,int,int);
void nrHeatDeposit(State*,int,int,int);
void nrHeatReentrain(State*,int,int);
void nrHeatMeshChanged(State*,int);
int nrHeatContact(State*,int,const GeometryHit*);
int nrHeatTick(State*);
double nrHeatLiveEnergy(const State*);
double nrLatentEnergy(const State*,int);
void nrSettleWaterHeat(State*,int);
int nrLatentHeatCommand(NrContext*,State*,const Json*);
int nrTransferThermalEnergy(NrContext*,State*,int,int,double);
int nrThermalTransferCommand(NrContext*,State*,const Json*);
int nrThermalLinkCommand(NrContext*,State*,const Json*);
int nrThermalTransport(State*);
int nrValidThermalLinks(const State*);
int nrValidThermal(const State*);
void nrThermalCell(const State*,int,double*);
void nrThermalMeshChanged(State*,int,int);
uint32_t nrThermalPaint(const State*,int,uint32_t);
int nrValidSurfaceWater(const State*);
void nrSurfaceWaterImpact(State*,int,const GeometryHit*);
void nrSurfaceWaterMeshChanged(State*,int,int);
void nrSurfaceWaterCell(const State*,int,double*);
void nrSurfaceWaterTotals(const State*,int,double*);
int nrPathTargetPosition(const State*,int,Vec3*);
int nrValidPathActors(const State*);
void nrFoamTick(State*);
int nrFoamTransportCommand(NrContext*,State*,const Json*);
int nrValidFoamTransport(const State*);
void nrFoamTransportTick(State*);
void nrFoamMeshChanged(State*);
void nrFoamImpact(State*,const GeometryHit*,const Particle*,Vec3);
int nrFloatBodyCommand(NrContext*,State*,const Json*);
int nrFloatHullCommand(NrContext*,State*,const Json*);
int nrFloatHullShape(const Json*);
int nrSurfaceFluidCommand(NrContext*,State*,const Json*);
int nrSurfaceFluidAngularCommand(NrContext*,State*,const Json*);
int nrSurfaceFluidAngularShape(const Json*);
int nrSurfaceFluidShape(const Json*);
int nrValidSurfaceFluids(const State*);
int nrSurfaceFluidsTick(State*);
int nrSurfaceFluidExchange(State*,FloatBody*,Vec3,double);
int nrFloatHullNumberValid(const Value*,double);
int nrBindFloatHullValue(State*,const Value*,double);
int nrValidFloatHulls(const State*);
int nrFloatHullTick(State*,int);
Vec3 nrFloatHullVertex(const FloatBody*,const FloatHull*,uint32_t);
int nrFloatBodiesTick(State*);
int nrValidFloatBodies(const State*);
int nrWaterHeight(const State*,int,double,double,double*);
void nrDrawFloatBodies(NrContext*,const Projection*);
int nrGeometryCommand(NrContext*,State*,const Json*);
int nrConfigureColliders(NrContext*,State*,const Json*,int,int);
uint32_t nrEmitterColliderMask(const State*,int);
int nrBuildGeometry(const State*,GeometryIndex*);
int nrValidGeometry(const State*);
int nrGeometryHitTimed(const State*,uint32_t,Vec3,Vec3,double,double,GeometryHit*,uint32_t*);
int nrWaveTriangleHit(const State*,int,Vec3,Vec3,double,double,double,GeometryHit*);
int nrGeometryHit(const State*,uint32_t,Vec3,Vec3,GeometryHit*,uint32_t*);
void nrSurfaceBasis(Vec3,Vec3*,Vec3*);
void nrSurfaceTick(State*);
void nrSurfaceImpact(State*,int,const Particle*,int);
int nrSurfaceWavesCommand(NrContext*,State*,const Json*);
Vec3 nrSurfaceTriangleVelocity(const State*,int,Vec3);
void nrDisplaceSurfaceTriangle(const State*,int,Triangle*);
int nrValidSurfaceWaves(const State*);
int nrSurfaceTriangle(const State*,int,Triangle*);
int nrEffectProfile(int);
int nrWindowMask(const Window*,double,double);
Vec3 nrWindowSourcePoint(const Window*,double,double,double,double*);
Vec3 nrWindowPoint(const Window*,double,double,double,double*);
void nrDrawWindowsGeometry(NrContext*,const Projection*);
double nrPowPositive(double,double);
uint32_t nrHueShift(uint32_t,double);
TextPose nrTextPose(const TextRun*,const uint32_t*,int,uint64_t,int);
TextPose nrTextPoseWithModel(const TextRun*,const uint32_t*,int,uint64_t,int,int);
int nrTextSupportsPhaseModel(int);
int nrTextTrailPose(const State*,int,int,int,TextPose*);
void nrPrepareText(TextRun*,const uint32_t*,const TextRun*,const uint32_t*,uint64_t,uint32_t*);
void nrPrepareTextWithModels(TextRun*,const uint32_t*,int,const TextRun*,const uint32_t*,int,uint64_t,uint32_t*);
void nrDrawTextTransitions(NrContext*);
#endif

int nrValidFirstPrompt(const State*);
int nrFirstPromptCommand(NrContext*,State*,const Json*);
int nrFirstPromptGeometry(const State*,int*,int*,int*,int*);
int nrFirstPromptHit(const State*,int,int);
void nrFirstPromptCoordinates(const State*,int(*)[2]);
void nrFirstPromptPaint(NrContext*,const State*);
int nrFirstPromptViewport(const State*,int*,int*,int*,int*);
int nrPromptFrameRect(const State*,int*,int*,int*,int*);
int nrValidPromptAppearance(const State*);
int nrPromptAppearanceCommand(NrContext*,State*,const Json*);
int nrPromptAppearanceInput(State*,int,int,int);
void nrPromptAppearanceWeather(NrContext*);
void nrPromptAppearanceApplication(NrContext*,const State*);
void nrPromptAppearanceCursor(NrContext*,const State*,int,int);
