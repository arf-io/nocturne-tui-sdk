/** Compile-only negative contracts. Native validation remains authoritative. */
import type {StyleRuleOptions, StateTarget, ValueBinding} from '../../bindings/typescript/contracts.js';
const widgetRule:StyleRuleOptions={id:1,selector:{family:'widget',states:{selected:true}},style:{material:2,alpha:{path:'/load',inputMin:0,inputMax:100,outputMin:.1,outputMax:.9}}};
const floor:StateTarget={family:'floor',id:0};
const binding:ValueBinding={family:'state',id:1,field:'active'};
// @ts-expect-error Text has no native alpha property.
const textAlpha:StyleRuleOptions={id:1,selector:{family:'text'},style:{alpha:.4}};
// @ts-expect-error Materials are discrete identifiers, not interpolated numbers.
const interpolatedMaterial:StyleRuleOptions={id:1,selector:{family:'widget'},style:{material:{path:'/load',inputMin:0,inputMax:1,outputMin:0,outputMax:3}}};
// @ts-expect-error Floor is the singleton zero identity.
const nonzeroFloor:StateTarget={family:'floor',id:4};
// @ts-expect-error Sampling inheritance is widget-only.
const floorInherit:StyleRuleOptions={id:1,selector:{family:'floor'},style:{sampling:'inherit'}};
// @ts-expect-error Role selectors use native booleans, not truthy strings.
const badState:StyleRuleOptions={id:1,selector:{family:'widget',states:{hover:'yes'}},style:{material:2}};
void [widgetRule,floor,binding,textAlpha,interpolatedMaterial,nonzeroFloor,floorInherit,badState];
const cameraProjectionBinding:ValueBinding={family:'camera',field:'fov'};
const donutGeometryBinding:ValueBinding={family:'widget',id:1,field:'innerRadius'};
// @ts-expect-error Camera fields cannot be used as widget property names.
const wrongBindingFamily:ValueBinding={family:'widget',id:1,field:'fov'};
// @ts-expect-error Unknown property names must fail before native execution.
const unknownBinding:ValueBinding={family:'camera',field:'any-arbitrary-field'};
void [cameraProjectionBinding,donutGeometryBinding,wrongBindingFamily,unknownBinding];
import type {NumericExpression} from '../../bindings/typescript/contracts.js';
const numericFormula:NumericExpression={clamp:{value:{add:[{multiply:[2,{intentField:'value'}]},{path:'/offset'}]},min:0,max:100}};
// @ts-expect-error String event fields are not numeric expression leaves.
const textPayloadFormula:NumericExpression={intentField:'event'};
// @ts-expect-error Divide requires exactly two numeric operands.
const wrongArityFormula:NumericExpression={divide:[1,2,3]};
// @ts-expect-error Array operators require at least two operands.
const unaryAddition:NumericExpression={add:[1]};
void [numericFormula,textPayloadFormula,wrongArityFormula,unaryAddition];
// @ts-expect-error One expression node cannot select two operators.
const mixedFormula:NumericExpression={add:[1,2],abs:3};
void mixedFormula;
import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const characterRuleCommand:NativeCommand={op:'character-rule',rule:{id:'prompt',selector:{role:'user-text',indices:[0,1]},foreground:2,states:{selected:{foregroundEffects:[{type:'invert'}]}}}};
// @ts-expect-error State patches cannot change the rule selector.
const invalidCharacterPatch:NativeCommand={op:'character-rule',rule:{id:'bad',states:{active:{selector:{role:'all'}}}}};
// @ts-expect-error Historical rule IDs are strings, unlike property style IDs.
const invalidCharacterId:NativeCommand={op:'remove-character-rule',id:1};
void [characterRuleCommand,invalidCharacterPatch,invalidCharacterId];
const valueRemoval:NativeCommand={op:'remove-value',path:'/control'};
const triggerRemoval:NativeCommand={op:'remove-trigger',id:1};
// @ts-expect-error Value removal uses its absolute path rather than a trigger ID.
const wrongValueRemoval:NativeCommand={op:'remove-value',id:1};
void [valueRemoval,triggerRemoval,wrongValueRemoval];

const panelPosition: NativeCommand = {op:"define",path:"/panel/x",value:8,binding:{family:"window",id:1,field:"position.x"}};
const areaFade: NativeCommand = {op:"define",path:"/area/fade",value:500,binding:{family:"area",id:1,field:"fadeMs"}};
// @ts-expect-error Window and area fields remain distinct.
const wrongPanelField: NativeCommand = {op:"define",path:"/bad",binding:{family:"area",id:1,field:"yaw"}};

const retainedFormula: NativeCommand = {op:"trigger",id:1,source:"/go",target:"/out",expression:{multiply:[{path:"/step"},2]}};
// @ts-expect-error Retained formulas cannot also select a constant operand.
const mixedTriggerFormula: NativeCommand = {op:"trigger",id:1,source:"/go",target:"/out",expression:1,value:1};
// @ts-expect-error Retained formulas cannot also select the legacy event operand.
const mixedEventFormula: NativeCommand = {op:"trigger",id:1,source:"/go",target:"/out",expression:1,valueFrom:"intentValue"};

const dimensionalCalculation: NativeCommand = {op:'set',path:'/duration',expression:{convert:{value:{path:'/seconds'},from:'seconds',to:'milliseconds'}}};
const mappedCalculation: NativeCommand = {op:'trigger',id:2,source:'/go',target:'/progress',expression:{remap:{value:{path:'/done'},inMin:0,inMax:100,outMin:0,outMax:1}}};
// @ts-expect-error Unit names are explicit; display cells have no implicit physical scale.
const invalidUnits: NativeCommand = {op:'set',path:'/out',expression:{convert:{value:1,from:'pixels',to:'meters'}}};
// @ts-expect-error A remap requires both output endpoints.
const incompleteRemap: NativeCommand = {op:'set',path:'/out',expression:{remap:{value:1,inMin:0,inMax:2,outMin:0}}};
// @ts-expect-error Operators are mutually exclusive.
const mixedTransforms: NativeCommand = {op:'set',path:'/out',expression:{floor:1,ceil:1}};
void [dimensionalCalculation,mappedCalculation,invalidUnits,incompleteRemap,mixedTransforms];
const emitterVector:NativeCommand={op:'define',path:'/weather/gravity',value:-4,binding:{family:'emitter',id:1,field:'gravity.y'}};
const birthMotion:NativeCommand={op:'define',path:'/weather/spin',value:30,binding:{family:'emitter',id:1,field:'angularVelocity.z'}};
const textTreatment:NativeCommand={op:'define',path:'/title/scatter',value:4,binding:{family:'text',id:1,field:'scatter'}};
const floorRetention:NativeCommand={op:'define',path:'/ground/retention',value:4000,binding:{family:'floor',field:'retentionMs'}};
// @ts-expect-error Floor controls cannot address emitter birth motion.
const wrongResourceField:NativeCommand={op:'define',path:'/bad',binding:{family:'floor',field:'angularVelocity.z'}};
// @ts-expect-error Vector components use x/y/z.
const wrongEmitterAxis:NativeCommand={op:'define',path:'/bad',binding:{family:'emitter',id:1,field:'gravity.w'}};
void [emitterVector,birthMotion,textTreatment,floorRetention,wrongResourceField,wrongEmitterAxis];
const nodeCardWidth:NativeCommand={op:'define',path:'/card/columns',value:40,binding:{family:'node',id:1,field:'maxColumns'}};
const waitSpeed:NativeCommand={op:'define',path:'/waiting/speed',value:120,binding:{family:'indicator',id:1,field:'stepMs'}};
// @ts-expect-error Wait indicators cannot use graph card metadata fields.
const wrongIndicatorField:NativeCommand={op:'define',path:'/bad',binding:{family:'indicator',id:1,field:'showDetail'}};
void [nodeCardWidth,waitSpeed,wrongIndicatorField];
const promptRows:NativeCommand={op:'define',path:'/prompt/rows',value:8,binding:{family:'prompt',field:'maxRows'}};
const backgroundStyle:NativeCommand={op:'define',path:'/background/style',value:2,binding:{family:'environment',field:'style'}};
const fieldWidth:NativeCommand={op:'define',path:'/field/band',value:1000,binding:{family:'field',id:1,field:'width'}};
// @ts-expect-error The prompt and environment have singleton ID zero.
const wrongPromptID:NativeCommand={op:'define',path:'/bad',binding:{family:'prompt',id:1,field:'maxRows'}};
void [promptRows,backgroundStyle,fieldWidth,wrongPromptID];
const plotReveal:NativeCommand={op:'define',path:'/plot/reveal',value:1200,binding:{family:'widget',id:1,field:'revealMs'}};
const panelShape:NativeCommand={op:'define',path:'/panel/shape',value:2,binding:{family:'window',id:1,field:'shape'}};
const areaParent:NativeCommand={op:'define',path:'/area/parent',value:2,binding:{family:'area',id:1,field:'parent'}};
// @ts-expect-error Widget presentation has no area parent field.
const wrongWidgetParent:NativeCommand={op:'define',path:'/bad',binding:{family:'widget',id:1,field:'parent'}};
void [plotReveal,panelShape,areaParent,wrongWidgetParent];
const replaceBinding:NativeCommand={op:'bind',path:'/control',binding:{family:'widget',id:2,field:'value'}};
const detachBinding:NativeCommand={op:'bind',path:'/control',binding:null};
// @ts-expect-error Binding replacement requires an explicit target or null.
const missingReplacement:NativeCommand={op:'bind',path:'/control'};
void [replaceBinding,detachBinding,missingReplacement];
const hueRate:NativeCommand={op:'define',path:'/palette/rate',value:20,binding:{family:'material',id:2,field:'channels.h.rate'}};
const alphaBoundary:NativeCommand={op:'define',path:'/palette/boundary',value:2,binding:{family:'material',id:2,field:'alpha.boundary'}};
// @ts-expect-error Track members are declared explicitly.
const invalidTrackMember:NativeCommand={op:'define',path:'/bad',binding:{family:'material',id:2,field:'alpha.frequency'}};
void [hueRate,alphaBoundary,invalidTrackMember];
const hostEvent:NativeCommand={op:'emit-intent',event:'/host/task',value:7,payload:{task:{id:'noc-1',ready:true},items:[1,null,'source']}};
// @ts-expect-error A host callback cannot be serialized as a retained payload.
const callbackPayload:NativeCommand={op:'emit-intent',event:'/host/task',payload:()=>true};
void [hostEvent,callbackPayload];

const numericPayloadLeaf:NumericExpression={intentPath:'/task/done'};
const payloadRatio:NativeCommand={op:'set',path:'/progress',intentId:1,expression:{divide:[{intentPath:'/task/done'},{intentPath:'/task/total'}]}};
// @ts-expect-error Payload paths are strings.
const badPayloadPath:NumericExpression={intentPath:3};
// @ts-expect-error Numeric leaf alternatives are mutually exclusive.
const mixedPayloadLeaf:NumericExpression={intentPath:'/task/done',intentField:'value'};
void [numericPayloadLeaf,payloadRatio,badPayloadPath,mixedPayloadLeaf];

const typedReady:NativeCommand={op:'define',path:'/ready',value:true,binding:{family:'widget',id:1,field:'enabled'}};
const typedTitle:NativeCommand={op:'define',path:'/title',value:'NOC 日本',binding:{family:'window',id:1,field:'title'}};
const typedTask:NativeCommand={op:'define',path:'/task',type:'json',value:{id:'noc-1',ready:true}};
const copyTask:NativeCommand={op:'set',path:'/task',expression:{literal:{id:'noc-2',items:[1,null,false]}}};
// @ts-expect-error Boolean values cannot bind numeric alpha properties.
const booleanAlpha:NativeCommand={op:'define',path:'/bad',value:true,binding:{family:'widget',id:1,field:'alpha'}};
// @ts-expect-error String values cannot bind numeric material identities.
const stringMaterial:NativeCommand={op:'define',path:'/bad',value:'3',binding:{family:'text',id:1,field:'material'}};
// @ts-expect-error Structured data has no scalar component binding.
const objectText:NativeCommand={op:'define',path:'/bad',value:{text:'value'},binding:{family:'widget',id:1,field:'text'}};
// @ts-expect-error Explicit Boolean type requires a Boolean value.
const mismatchedType:NativeCommand={op:'define',path:'/bad',type:'boolean',value:1};
void [typedReady,typedTitle,typedTask,copyTask,booleanAlpha,stringMaterial,objectText,mismatchedType];

const typedAction:NativeCommand={op:'trigger',id:1,target:'/title',event:'/host/task',whenExpression:{equal:[{intentPath:'/task/status'},{literal:'ready'}]},expression:{concat:[{literal:'Task: '},{intentPath:'/task/title'}]}};
const typedConditional:NativeCommand={op:'set',path:'/title',expression:{if:{condition:{path:'/ready'},then:{literal:'Ready'},else:{literal:'Waiting'}}}};
// @ts-expect-error Choose a scalar source or a typed guard expression.
const mixedTypedGuard:NativeCommand={op:'trigger',id:1,source:'/go',target:'/title',whenExpression:true,expression:{literal:'Ready'}};
// @ts-expect-error One typed expression node cannot select two operators.
const mixedTypedOperators:NativeCommand={op:'set',path:'/ready',expression:{and:[true,false],or:[true,false]}};
// @ts-expect-error Equality has exactly two operands.
const wrongEqualityArity:NativeCommand={op:'set',path:'/ready',expression:{equal:[true,false,true]}};
void [typedAction,typedConditional,mixedTypedGuard,mixedTypedOperators,wrongEqualityArity];

const typedAppearanceGuard:NativeCommand={op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:{equal:[{path:'/status'},'ready']},style:{alpha:.8}};
const conditionalNumericResult:NativeCommand={op:'set',path:'/duration',expression:{if:{condition:{path:'/ready'},then:{convert:{value:2,from:'seconds',to:'milliseconds'}},else:0}}};
// @ts-expect-error Appearance rules choose numeric conditions or a typed expression.
const mixedAppearanceGuard:NativeCommand={op:'style-rule',id:1,selector:{family:'widget'},when:{path:'/load',comparison:'above',value:0},whenExpression:true,style:{alpha:.8}};
void [typedAppearanceGuard,conditionalNumericResult,mixedAppearanceGuard];

const structuredTaskResult:NativeCommand={op:'set',path:'/task',intentId:1,expression:{object:{task:{intentPath:'/task'},ready:{equal:[{intentPath:'/status'},'ready']},items:{array:[true,null,{path:'/title'}]}}}};
// @ts-expect-error Container expression alternatives are mutually exclusive.
const mixedContainers:NativeCommand={op:'set',path:'/task',expression:{array:[],object:{}}};
// @ts-expect-error Array construction needs an array of expressions.
const wrongArrayShape:NativeCommand={op:'set',path:'/task',expression:{array:{task:true}}};
void [structuredTaskResult,mixedContainers,wrongArrayShape];

const retainedTaskTitle:NativeCommand={op:'set',path:'/title',expression:{path:'/task',pointer:'/title'}};
const retainedTaskRatio:NativeCommand={op:'set',path:'/progress',expression:{divide:[{path:'/task',pointer:'/done'},{path:'/task',pointer:'/total'}]}};
// @ts-expect-error JSON pointers are strings.
const invalidValuePointer:NativeCommand={op:'set',path:'/title',expression:{path:'/task',pointer:1}};
void [retainedTaskTitle,retainedTaskRatio,invalidValuePointer];

const meshAppearance:NativeCommand={op:'mesh-style',alpha:.4,color:0xabcdef,sampling:'braille'};
const triangleAppearance:NativeCommand={op:'mesh-style',triangleIndex:0,alpha:.4};
const triangleColorBinding:NativeCommand={op:'define',path:'/triangle/color',value:0xabcdef,binding:{family:'triangle',id:0,field:'color'}};
const waveAmplitudeBinding:NativeCommand={op:'define',path:'/ocean/amplitude',value:2,binding:{family:'surface-wave',id:1,field:'waves.0.amplitude'}};
const foamEnabledBinding:NativeCommand={op:'define',path:'/ocean/foam',value:true,binding:{family:'surface-foam',id:1,field:'enabled'}};
// @ts-expect-error Sampling belongs to the complete mesh, not one triangle.
const triangleSampling:NativeCommand={op:'mesh-style',triangleIndex:0,sampling:'braille'};
// @ts-expect-error Wave coefficient members are closed names.
const invalidWaveMember:NativeCommand={op:'define',path:'/ocean/wave',value:2,binding:{family:'surface-wave',id:1,field:'waves.0.unknown'}};
// @ts-expect-error Foam density is a derived observation.
const derivedFoamBinding:NativeCommand={op:'define',path:'/ocean/density',value:2,binding:{family:'surface-foam',id:1,field:'density'}};

const scheduledBatch:NativeCommand={op:'schedule',id:1,atUs:500000,command:{op:'batch',commands:[{op:'set',path:'/load',value:2}]}};
// @ts-expect-error Scheduled batches cannot contain nested transactions.
const nestedScheduledBatch:NativeCommand={op:'schedule',id:1,atUs:500000,command:{op:'batch',commands:[{op:'batch',commands:[]}]}};

const plotDataBinding:NativeCommand={op:'define',path:'/series',type:'json',value:[1,2,3],binding:{family:'widget',id:1,field:'data'}};
// @ts-expect-error Bound plot data contains numbers, not coerced booleans.
const booleanPlotData:NativeCommand={op:'define',path:'/series',type:'json',value:[true],binding:{family:'widget',id:1,field:'data'}};

const individualPlotEntry:NativeCommand={op:'define',path:'/entry',value:5,binding:{family:'widget',id:1,field:'data.127'}};

const payloadThresholdGuard:NativeCommand={op:'trigger',id:1,target:'/out',event:'/host/metric',whenExpression:{greaterOrEqual:[{intentPath:'/metric'},3]},value:7};
// @ts-expect-error Ordered predicates require exactly two operands.
const badOrderingArity:NativeCommand={op:'set',path:'/truth',expression:{lessThan:[1,2,3]}};
// @ts-expect-error Different expression operators cannot coexist in one node.
const mixedOrderingNode:NativeCommand={op:'set',path:'/truth',expression:{lessThan:[1,2],equal:[1,2]}};

const emitterCollisionBoolean:NativeCommand={op:'define',path:'/collision',value:false,binding:{family:'emitter',id:1,field:'collision'}};
// @ts-expect-error Binding family is required; there is no implicit material target.
const missingBindingFamily:NativeCommand={op:'define',path:'/alpha',value:.5,binding:{id:0,field:'alpha'}};
const reducedMotionPreference:NativeCommand={op:'define',path:'/motion',value:true,binding:{family:'accessibility',field:'reducedMotion'}};
// @ts-expect-error Accessibility preferences are a singleton with ID zero.
const invalidPreferenceId:NativeCommand={op:'define',path:'/motion',value:true,binding:{family:'accessibility',id:1,field:'reducedMotion'}};
const emitterDepositBoolean:NativeCommand={op:'define',path:'/deposit',type:'boolean',value:true,binding:{family:'emitter',id:1,field:'deposit'}};
// @ts-expect-error Collision binding is not a string-valued control.
const emitterCollisionString:NativeCommand={op:'define',path:'/collision',value:'false',binding:{family:'emitter',id:1,field:'collision'}};
