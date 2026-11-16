import type {NativeCommand,EmitterOptions} from '../../bindings/typescript/contracts.js';
const flat:EmitterOptions={id:1,birthOrientation:[0,0,90]};
const nested:NativeCommand={op:'weather-author',schema:'nocturne.weather-authoring/v1',id:1,
 effect:'weather/autumn-drift',birth:{shape:'line',orientation:[0,0,90],extent:[4,0,0]},
 emission:{count:240,runningTimeMs:20000},collision:{enabled:false,deposit:false}};
// @ts-expect-error Euler orientation has exactly three numeric axes.
const invalid:EmitterOptions={id:1,birthOrientation:[0,90]};
// @ts-expect-error A force cannot be authored as a birth-frame orientation.
const wrongGroup:NativeCommand={op:'weather-author',schema:'nocturne.weather-authoring/v1',id:1,effect:'weather/autumn-drift',forces:{orientation:[0,0,90]}};
void [flat,nested,invalid,wrongGroup];

const uniformBirth: NativeCommand = {op:'weather-author',schema:'nocturne.weather-authoring/v1',id:2,effect:'weather/autumn-drift',birth:{shape:'sphere',distribution:'uniform'}};
void uniformBirth;
// @ts-expect-error distribution is a closed native choice
const badDistribution: NativeCommand = {op:'emitter',id:3,distribution:'gaussian'};
void badDistribution;

const model:NativeCommand={op:'model-import',schema:'nocturne.model/v1',units:'meters',coordinates:'right-handed-y-up',vertices:[[0,0,0],[1,0,0],[0,1,0]],materials:[{color:0xffffff}],triangles:[{indices:[0,1,2],material:0}]};
void model;
// @ts-expect-error imported geometry has three indices per triangle
const invalidModel:NativeCommand={op:'model-import',schema:'nocturne.model/v1',units:'meters',coordinates:'right-handed-y-up',vertices:[],materials:[],triangles:[{indices:[0,1],material:0}]};
void invalidModel;

const authoredMotion:NativeCommand={op:'weather-author',schema:'nocturne.weather-authoring/v1',id:7,effect:'weather/autumn-drift',birth:{initialOrientation:[10,20,30],angularVelocity:[30,-60,90]}};
void authoredMotion;

const retainedResume:NativeCommand={op:'resume',id:1};
const retainedCancel:NativeCommand={op:'cancel',id:1,style:'dissolve',tailMs:500};
void [retainedResume,retainedCancel];
// @ts-expect-error cancellation requires a non-drain ending
const invalidCancel:NativeCommand={op:'cancel',id:1,style:'drain'};
// @ts-expect-error resume cannot author a new particle count
const invalidResume:NativeCommand={op:'resume',id:1,count:4};
void [invalidCancel,invalidResume];

const graphemeKey:NativeCommand={op:'key',key:'Backspace',unit:'grapheme'};
void graphemeKey;
// @ts-expect-error editor units are closed native choices
const badUnit:NativeCommand={op:'key',key:'Backspace',unit:'word'};
void badUnit;
