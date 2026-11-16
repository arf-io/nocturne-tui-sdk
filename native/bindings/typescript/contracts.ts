/** ABI-1 authoring contracts. Native validation is authoritative for cross-field
 * constraints, finite numbers, capacities, references and atomic rejection.
 * Coordinates: +X right, +Y up, +Z toward the default viewer. Time: microseconds.
 */
export type Sampling = 'cell'|'half'|'braille'|'hybrid';
export type Vector3 = readonly [number,number,number];
export type Easing = 'linear'|'ease-in'|'ease-out'|'smooth'|'smoother'|'sine'|'step';
export type Boundary = 'clamp'|'loop'|'reverse'|'random'|'smooth-random';
export interface Track {initial?:number;rate?:number;min?:number;max?:number;step?:number;periodMs?:number;boundary?:Boundary;easing?:Easing;seed?:number;}
export type Channel = number|Track;
export type ColorSpace = 'oklch'|'oklab'|'hsl'|'hsb'|'rgb'|'linear-rgb'|'cmyk'|'indexed';
export type Border = 'none'|'rounded'|'square'|'double'|'heavy';
export type CharacterBlend = 'normal'|'multiply'|'screen'|'overlay'|'darken'|'lighten'|'color-dodge'|'color-burn'|'hard-light'|'soft-light'|'difference'|'exclusion'|'hue'|'saturation'|'color'|'luminosity'|'additive'|'subtractive'|'divide'|'linear-burn'|'linear-light'|'vivid-light'|'pin-light'|'hard-mix'|'darker-color'|'lighter-color'|'dissolve'|'none';
export type CharacterOperator = 'source-over'|'clear'|'source'|'destination'|'destination-over'|'source-in'|'destination-in'|'source-out'|'destination-out'|'source-atop'|'destination-atop'|'xor'|'lighter';
export interface CharacterSelector {
 role?:string|readonly string[];state?:string|readonly string[];path?:string;pathPrefix?:string;
 ids?:readonly number[];indices?:readonly number[];glyphs?:string;inkOnly?:boolean;
 rect?:{x:number;y:number;width:number;height:number};
}
export interface CharacterEffect {
 type:'invert'|'alpha'|'grayscale'|'exposure'|'contrast'|'gamma'|'posterize'|'threshold'|'hue';
 value?:number;where?:'all'|'selected'|'unselected';
}
export interface CharacterStyle {
 enabled?:boolean;foreground?:number;background?:number;
 foregroundBlend?:CharacterBlend;backgroundBlend?:CharacterBlend;operator?:CharacterOperator;
 compositeSpace?:'srgb'|'linear-srgb'|'oklab'|'oklch';
 foregroundEffects?:readonly CharacterEffect[];backgroundEffects?:readonly CharacterEffect[];
 foregroundOpacity?:number;backgroundOpacity?:number;protectLocalInk?:boolean;
}
export interface CharacterRule extends CharacterStyle {
 id:string;priority?:number;selector?:CharacterSelector;states?:Readonly<Record<string,CharacterStyle>>;
}
export interface CharacterRegion {
 id:string;path:string;role?:string;state?:string;
 rect?:{x:number;y:number;width:number;height:number};
 cells?:readonly number[];indices?:readonly number[];
}
export type EndStyle = 'drain'|'settle'|'dissolve'|'gust'|'quench'|'disperse';
export type PromptMode = 'marquee'|'grow'|'vim-inline'|'vim-full';
export interface PromptCursorAppearance {shape?:'inherit'|'none'|'block'|'half'|'underline'|'bar'|'braille'|'custom';glyph?:string;color?:string;secondaryColor?:string;blinkMs?:number;duty?:number;colorMode?:'fixed'|'pulse'|'cycle';colorPeriodMs?:number;}
export interface PromptTypingWeather {style?:'off'|'embers'|'sparks'|'nova'|'rain'|'snow'|'ripples';intensity?:number;lifeMs?:number;speed?:number;paste?:'each'|'burst'|'off';}

export type WidgetKind = 'text'|'box'|'rule'|'button'|'item'|'cursor'|'progress'|'bars'|'pie'|'donut'|'scatter'|'line'|'digits'|'edge'|'checkbox'|'radio'|'select'|'scrollbar';
/** Exact original RC2 Stage primitive kinds exposed as independent retained
 * RC4 components. Source dimensions are required; the remaining node controls
 * use their original packNodes defaults when omitted. */
export type SourceStageKind = 'text'|'box'|'rule'|'button'|'item'|'cursor'|'progress'|'bars'|'pie'|'donut'|'scatter'|'line'|'digits'|'edge';
export interface SourceStageComponentOptions {
 id:number;kind:SourceStageKind;width:number;height:number;
 legacyFlags?:number;x?:number;y?:number;state?:number;value?:number;fromValue?:number;
 changedMs?:number;durationMs?:number;fg?:number;bg?:number;fgOpacity?:number;bgOpacity?:number;
 style?:number;text?:string;data?:readonly number[];hueStep?:number;hueSpeed?:number;hueBase?:number;
 revealMs?:number;hueSaturation?:number;hueBrightness?:number;colorAnimation?:number;
 glyph?:number;zoom?:number;materialId?:number;
}
/** Complete authored record readback. `node` preserves the exact original
 * 32-word layout independently of the named text/data views. */
export interface SourceStageComponentInfo {
 id:number;materialId:number;kind:SourceStageKind;legacyFlags:number;node:readonly number[];
 text:string;data:readonly number[];
}
/** Explicit destinations for swept particle-center collisions. An omitted
 * emitter setting retains floor-only behavior; an explicit object defaults
 * floor to false. Surface IDs are existing integers 1..16 without duplicates. */
export interface ColliderSelection {floor?:boolean;surfaces?:readonly number[];}
/** A named static triangle surface. Response uses normalized wetness/heat;
 * rates are per second, retention/fade are milliseconds, and colors are RGB24.
 * Updates preserve response state and deposits. See native/docs/SURFACES.md. */
export interface SurfaceOptions {
 id:number;collisionEnabled?:boolean;renderVisible?:boolean;restitution?:number;friction?:number;
 settleSpeed?:number;reentrainWindSpeed?:number;maxIndividual?:number;maxTiles?:number;
 overflow?:'reject-new'|'merge-to-field';retentionMs?:number;fadeMs?:number;
 wetnessGain?:number;evaporation?:number;heatGain?:number;cooling?:number;thermalEvaporation?:number;
 wetnessDarkening?:number;heatColor?:number;heatTintStrength?:number;
}
/** Wave row: amplitude, X/Z wave numbers, angular frequency, phase. */
export type WaveRow = readonly [number,number,number,number,number];
export interface SurfaceWavesOptions {surfaceId:number;waves:readonly WaveRow[];}
export interface SurfaceFoamOptions {surfaceId:number;enabled?:boolean;sourceRate?:number;curvatureThreshold?:number;decay?:number;impactGain?:number;color?:number;}
export interface FloatBodyOptions {id:number;surfaceId?:number;position?:Vector3;velocity?:Vector3;mass?:number;radius?:number;fluidDensity?:number;gravity?:number;drag?:number;visible?:boolean;color?:number;}
/** World-space triangle, bounded by the shared 256-triangle scene capacity.
 * surfaceId 0/omitted is rendering-only; 1..16 references a named surface. */
/** Inline bounded static geometry, consumed directly by the C semantic compiler. */
export interface ModelImportOptions {
 append?:boolean;schema:'nocturne.model/v1';units:'meters'|'centimeters'|'millimeters';coordinates:'right-handed-y-up';
 vertices:readonly Vector3[];materials:readonly {color:number;alpha?:number}[];
 triangles:readonly {indices:readonly [number,number,number];material:number;surfaceId?:number}[];
 transform?:{position?:Vector3;orientation?:Vector3;scale?:Vector3};sampling?:Sampling;
}
export interface PathTravelOptions {id:number;target:{family:'camera';id:0}|{family:'emitter'|'window'|'node';id:number};points:readonly Vector3[];speed?:number;distance?:number;mode?:'clamp'|'loop'|'reverse';closed?:boolean;}
/** Original RC2 scenic compositions exposed as a retained RC4 scene layer.
 * Values use the natural units and field names of the source authoring UI;
 * native validation performs range, finiteness and cross-field checks. */
export type SceneArtName = 'pearl-cascade'|'tidal-glass'|'copper-causeway'|'silt'|'red-shift';
export interface SceneArtControls {
 cameraX?:number;cameraY?:number;cameraZ?:number;yaw?:number;pitch?:number;roll?:number;
 fov?:number;projection?:0|1;span?:number;flow?:number;travel?:number;seed?:number;
 redshift?:number;discTilt?:number;detail?:0|1|2;waterAlpha?:number;background?:number;
 ink?:number;accent?:number;secondary?:number;sampling?:0|1;
}
export interface SceneArtDetailControls {
 waveHeight?:number;wavelength?:number;windAngle?:number;crossSwell?:number;
 choppiness?:number;foam?:number;waveSpeed?:number;joinRiver?:0|1;
}
/** Scene is required on first activation and optional for retained partial
 * patches; native validation enforces that state-dependent requirement. */
export interface SceneArtOptions {
 scene?:SceneArtName;width?:number;height?:number;
 /** Independent nonnegative safe integer milliseconds; null resumes the scene clock. */
 timeMs?:number|null;
 controls?:SceneArtControls;detail?:SceneArtDetailControls;
}
export type SceneArtWorldQ = readonly [number,number,number,number,number,number,number,number,number,number,number,number,number,number,number,number,number,number,number,number,number,number,number,number];
export type SceneArtDetailQ = readonly [number,number,number,number,number,number,number,number];
/** Complete 24-value natural view of the lossless original source vector. */
export type SceneArtWorldControls = Required<SceneArtControls> & {width:number;height:number;scene:number};
export interface SceneArtInfo {
 scene:SceneArtName;hasWorldDetail:boolean;timeMs:number|null;worldQ:SceneArtWorldQ;detailQ:SceneArtDetailQ;
 controls:SceneArtWorldControls;detail:Required<SceneArtDetailControls>;
 effective:{timeMs:number;worldQ:SceneArtWorldQ;detailQ:SceneArtDetailQ;controls:SceneArtWorldControls;
   detail:Required<SceneArtDetailControls>;width:number;height:number};
}
export type EnvironmentPresentation = 'workbench'|'canvas';
/** Braille-family particles hidden behind the nearest one in a cell: 'hidden' keeps them out of the dots; 'merge' adds their dots. */
export type OccludedDots = 'hidden'|'merge';
/** Where a prompt source paints: a cell rectangle, the active prompt's frame (resolved every frame), a widget's rectangle, or null for the whole viewport. */
export type PromptSourceRegion = {x:number;y:number;width:number;height:number}|'prompt'|{widget:number}|null;
/** A bounded prompt-source layer. Omitted fields keep their value; null restores the defaults. z and order accept only their defaults until the surface-layers design. */
/** 0..1 each, default 1: fg for the source's glyphs, bg for its paper. A number sets both. */
export type PromptSourceAlpha = number|{fg?:number;bg?:number};
export interface PromptSourceLayer {region?:PromptSourceRegion;z?:'above';order?:0;alpha?:PromptSourceAlpha;frame?:'visible'|'invisible'}
export type RibbonOptions = ({interpolation?:'linear';subdivisions?:never}|{interpolation:'catmull-rom';subdivisions?:number}) & {append?:boolean;points:readonly Vector3[];up?:Vector3;closed?:boolean;miterLimit?:number;color?:number;alpha?:number;surfaceId?:number;sampling?:Sampling} & ({width?:number;widths?:never}|{width?:never;widths:readonly number[]});
export interface MeshTriangle {a:Vector3;b:Vector3;c:Vector3;color?:number;alpha?:number;surfaceId?:number;}
export interface SurfaceInfo extends Omit<Required<SurfaceOptions>,'retentionMs'|'fadeMs'> {
 retentionUs:number;fadeUs:number;wetness:number;heat:number;impacts:number;rejectedDeposits:number;
 individualDeposits:number;aggregateDeposits:number;aggregateTiles:number;
}
export interface GeometryInfo {triangles:number;collisionTriangles:number;bvhNodes:number;meshGeneration:number;contactBudgetExhausted:number;collisionQueries:number;triangleTests:number;}
export interface SurfaceContactInfo {particleId:number;surfaceId:number;triangleIndex:number;normal:Vector3;}
export interface EmitterOptions {
 id:number;sampling?:Sampling;surfaceAlpha?:number;effect?:string;seed?:number;count?:number;runningTimeMs?:number;startTimeUs?:number;
 position?:Vector3;extent?:Vector3;velocity?:Vector3;spread?:Vector3;gravity?:Vector3;wind?:Vector3;windVariation?:Vector3;
 /** Active right-handed X, Y, Z degrees, applied in that order to birth offsets and initial velocity/spread. Forces stay in world space. */
 birthOrientation?:Vector3;initialOrientation?:Vector3;angularVelocity?:Vector3;
 drag?:number;lift?:number;flutterHz?:number;flutterAmount?:number;tumble?:Vector3;sizeMin?:number;sizeMax?:number;
 lifetimeMinMs?:number;lifetimeMaxMs?:number;material?:number;alpha?:number;deposit?:boolean;collision?:boolean;colliders?:ColliderSelection;
 distribution?:'legacy'|'uniform';shape?:'point'|'box'|'sphere'|'disc'|'line';schedule?:'uniform'|'seeded-jitter';endStyle?:EndStyle;tailMs?:number;
 topology?:0|1|2|3|4|5;heat?:number;radius?:number;trailMs?:number;
 birthFadeMs?:number;deathFadeMs?:number;windScale?:number;windPeriodSeconds?:number;shapeWeights?:Vector3;coreMs?:number;
 cycles?:number;gapMs?:number;rate?:number;nearDistance?:number;farDistance?:number;farFadeDistance?:number;veinContrast?:number;curl?:number;backTint?:number;twoSided?:boolean;
}
/** Original spatial sampler controls. Q8 values are cells multiplied by 256;
 * milli values and phase1024 retain the source's exact authored precision. */
export interface MaterialPatternOptions {
 kind?:'solid'|'linear'|'diagonal'|'wave'|'rotating-linear'|'plasma'|'concentric'|'moire'|'aurora'|'interference'|'chevrons'|'diamond';
 focusMode?:'none'|'row'|'column'|'radial'|'diagonal-band';focusXQ8?:number;focusYQ8?:number;
 periodMs?:number;saturationMilli?:number;brightnessMilli?:number;
 speedFalloffMilli?:number;saturationFalloffMilli?:number;brightnessFalloffMilli?:number;
 cellAspectMilli?:number;scaleQ8?:number;angleMilliDegrees?:number;pivotXQ8?:number;pivotYQ8?:number;
 rotationPeriodMs?:number;rotationMode?:'fixed'|'continuous'|'pendulum';swingMilliDegrees?:number;
 phase1024?:number;seed?:number;baseRgb?:number;inkRgb?:number;palette?:readonly number[];
 gradientWrap?:'loop'|'mirror'|'hard-stops';interpolation?:'linear'|'eased';colorMode?:'palette'|'hsv'|'rgb-sine';
 hueOffsetDegrees?:number;motion?:boolean;originXCells?:number;originYCells?:number;waveAmplitudeMilli?:number;reverse?:boolean;
}
export interface MaterialOptions {id?:number;space?:ColorSpace;channels?:Record<string,Channel>;alpha?:Channel;hueStep?:number;scope?:'uniform'|'characters';blend?:string;gradient?:readonly (readonly number[])[];spacing?:number;index?:Channel;colors?:readonly number[];pattern?:MaterialPatternOptions|null;}
/** Parsed directly by the current C semantic compiler; no historical runtime. */
export interface WeatherAuthorOptions {
 schema:'nocturne.weather-authoring/v1';id:number;effect:string;
 emission?:Pick<EmitterOptions,'seed'|'count'|'rate'|'runningTimeMs'|'startTimeUs'|'cycles'|'gapMs'|'schedule'>;
 birth?:Pick<EmitterOptions,'shape'|'distribution'|'position'|'extent'|'velocity'|'spread'|'initialOrientation'|'angularVelocity'> & {orientation?:Vector3};
 forces?:Pick<EmitterOptions,'gravity'|'wind'|'windVariation'|'drag'|'lift'|'flutterHz'|'flutterAmount'|'tumble'|'heat'|'windScale'|'windPeriodSeconds'>;
 particle?:Pick<EmitterOptions,'shapeWeights'|'sizeMin'|'sizeMax'|'material'|'alpha'|'radius'|'topology'|'trailMs'|'birthFadeMs'|'deathFadeMs'|'coreMs'|'nearDistance'|'farDistance'|'farFadeDistance'|'veinContrast'|'curl'|'backTint'|'twoSided'|'sampling'|'surfaceAlpha'>;
 collision?:{enabled?:boolean;deposit?:boolean};
 lifecycle?:Pick<EmitterOptions,'lifetimeMinMs'|'lifetimeMaxMs'|'endStyle'|'tailMs'>;
}
export interface CameraOptions {profile?:'default'|'original';navigation?:'orbit'|'fly'|'pan';target?:Vector3;moveSpeed?:number;turnSpeed?:number;sensitivity?:number;position?:Vector3;yaw?:number;pitch?:number;roll?:number;near?:number;far?:number;fov?:number;span?:number;orthographic?:boolean;}
export type CameraRig='orbit'|'head'|'dolly'|'crane'|'follow'|'spacecraft';
export type CameraNavigationMode='orbit'|'pan'|'fly';
export type CameraInputAction='disabled'|'orbit-x'|'orbit-y'|'orbit-z'|'pan-x'|'pan-y'|'pan-z'|'look-x'|'look-y'|'look-z';
export interface CameraInputAxis {action?:CameraInputAction;sensitivity?:number;enabled?:boolean;invert?:boolean;}
export type CameraFollowTarget={kind:'point';point:Vector3}|{kind:'node';id:number};
/** Actual native rig controls. Rotation vectors are [pitch,yaw,roll], in degrees. */
export interface CameraControlsOptions {
 enabled?:true;rig?:CameraRig;mode?:CameraNavigationMode;inputTarget?:'body'|'head';
 inputAxes?:{x?:CameraInputAxis;y?:CameraInputAxis;z?:CameraInputAxis};
 head?:{position?:Vector3;rotation?:Vector3};crane?:{pivot?:Vector3;boom?:Vector3};
 follow?:{target?:CameraFollowTarget;offset?:Vector3;track?:boolean};anchor?:Vector3|null;
}
export interface CameraControlsInfo {
 enabled:boolean;rig:CameraRig;mode:CameraNavigationMode;inputTarget:'body'|'head';
 inputAxes:{x:Required<CameraInputAxis>;y:Required<CameraInputAxis>;z:Required<CameraInputAxis>};
 head:{position:Vector3;rotation:Vector3};crane:{pivot:Vector3;boom:Vector3};
 follow:{target:CameraFollowTarget;offset:Vector3;track:boolean};anchor:Vector3|null;
}
export interface MotionStep {kind:'cruise'|'turn'|'climb'|'dive'|'roll'|'orbit'|'escape'|'falling';durationMs:number;speed?:number;yaw?:number;pitch?:number;roll?:number;bank?:number;radius?:number;target?:Vector3;coordinated?:boolean;}
export interface TextOptions {id:number;text?:string;effect?:string;phase?:'show'|'hide';phaseModel?:'source'|'reverse-show'|'source-paint';local?:boolean;x?:number;y?:number;width?:number;durationMs?:number;staggerMs?:number;jitterMs?:number;batchSize?:number;distance?:number;scatter?:number;variation?:number;wind?:number;overshoot?:number;cycles?:number;scrambleHz?:number;hueSpread?:number;material?:number;seed?:number;alphabet?:string;easing?:Easing|'cubic'|'back'|'bounce';delayMs?:number;reverseOrder?:boolean;randomOrder?:boolean;trailLength?:number;}
export type WindowSourceAction='close'|'minimize'|'maximize'|'background';
export type WindowSourceChrome='mac'|'windows'|'gnome'|'custom';
export interface WindowSourcePresentationOptions {
 opacity:number;depthFade:number;chrome:WindowSourceChrome;controlWidth:number;controlHeight:number;
 customSide:'left'|'right';customOrder:readonly [WindowSourceAction,WindowSourceAction,WindowSourceAction,WindowSourceAction];
 customGlyphs:readonly [number,number,number,number];
}
export interface WindowOptions {id:number;sourceGeometry?:boolean;sourcePresentation?:boolean;depthFade?:number;chrome?:WindowSourceChrome;controlWidth?:number;controlHeight?:number;customSide?:'left'|'right';customOrder?:string;customGlyphs?:string;title?:string;text?:string;effect?:string;shape?:string;position?:Vector3;yaw?:number;pitch?:number;roll?:number;width?:number;height?:number;alpha?:number;material?:number;durationMs?:number;group?:number;minColumns?:number;maxColumns?:number;anchorX?:number;anchorY?:number;overshoot?:number;scatter?:number;bend?:number;folds?:number;meshColumns?:number;meshRows?:number;seed?:number;polygon?:readonly (readonly [number,number])[];padding?:number;border?:Border;chromeSize?:number;fadeStartRatio?:number;fadeEndRatio?:number;}
export interface WidgetOptions {id:number;kind?:WidgetKind;x?:number;y?:number;width?:number;height?:number;padding?:number;alpha?:number;border?:Border;material?:number;backgroundMaterial?:number;enabled?:boolean;selected?:boolean;active?:boolean;text?:string;value?:number;min?:number;max?:number;data?:readonly number[];mode?:number;pulseMs?:number;sampling?:'inherit'|'cell'|'half'|'braille'|'hybrid';cellAspect?:number;innerRadius?:number;startAngle?:number;sweepAngle?:number;revealMs?:number;replay?:boolean;}
/** Owned authored source properties; dimensions are independent of clipping. */
export interface WidgetInfo {
 id:number;kind:number;text:string;value:number;x:number;y:number;width:number;height:number;
 padding:number;border:0|1|2|3|4;material:number;backgroundMaterial:number;alpha:number;
 enabled:boolean;selected:boolean;active:boolean;min:number;max:number;mode:number;
 pulseUs:number;changedUs:number;data:number[];
 plot:{sampling:'inherit'|'cell'|'half'|'braille'|'hybrid';cellAspect:number;innerRadius:number;
  startAngle:number;sweepAngle:number;revealUs:number;revealAtUs:number};
}
export interface AreaOptions {id:number;parent?:number;x?:number;y?:number;width?:number;height?:number;padding?:number;margin?:number;alpha?:number;border?:Border;hideEmpty?:boolean;speedX?:number;speedY?:number;material?:number;fadeMs?:number;gapMs?:number;layout?:'ordered'|'queue'|'direct';}
export interface AreaInfo {
 id:number;parent:number;x:number;y:number;width:number;height:number;padding:number;margin:number;
 border:0|1|2|3|4;hideEmpty:boolean;material:number;alpha:number;speedX:number;speedY:number;
 layout:'ordered'|'queue'|'direct';fadeUs:number;gapUs:number;availableUs:number;
}
export interface WindowTextureOptions {id:number;width?:number;height?:number;offset?:number;cells?:readonly (readonly [number,number,number])[];}
export interface WindowTextureInfo {width:number;height:number;cells:[number,number,number][];}
/** Window-owned rendered text and palette configuration. */
export interface WindowContentOptions {
 profile?:'atelier';chrome?:'mac'|'windows'|'gnome'|'custom';customSide?:'left'|'right';toolWidth?:number;toolHeight?:number;fadeFloor?:number;customOrder?:Array<'minimize'|'maximize'|'fade'|'close'>;customGlyphs?:string[];toolColors?:{minimize?:number;maximize?:number;fade?:number;close?:number};
 id:number;label?:string;sourceIndex?:number;text?:string;colors?:readonly number[];stopWidths?:readonly number[];
 background?:number;ink?:number;lightness?:number;chroma?:number;brightness?:number;hueOffset?:number;
 lockLightness?:boolean;feather?:number;textLightness?:number;textChroma?:number;waveform?:readonly number[];
}
/** Exact original application background styles; distinct from environment styles. */
export type WindowApplicationBackgroundStyle = 'linear'|'double-axis'|'wave'|'plasma'|'caustics'|'vortex'|'contours'|'aurora'|'woven'|'moire'|'tunnel'|'diamond'|'bilinear'|'checker'|'warp';
/** This source sampler accepts vertical and does not accept hybrid. */
export type WindowApplicationSampling = 'half'|'vertical'|'braille'|'cell';
/** Partial original surface-weather controls. Native validation enforces finite
 * ranges, integer count/branches/arcSegments/seed and 1..64 printable glyphs. */
export interface WindowApplicationParticleOptions {
 count?:number;lifeMs?:number;launchSpeed?:number;gravity?:number;drag?:number;
 wind?:number;flickerHz?:number;trailMs?:number;branches?:number;arcSegments?:number;
 arcJitter?:number;coreMs?:number;shockwave?:number;explosionForce?:number;seed?:number;
 brightness?:number;emberSpread?:number;arcReach?:number;glyphs?:string;
}
/** Retained original application settings. All fields are partial patches.
 * paletteWindowId must reference an existing window with generated content;
 * native validation enforces this requirement and all numeric/glyph bounds.
 * Duration fields ending in Ms use milliseconds, not command-clock microseconds. */
export interface WindowApplicationOptions {
 paletteWindowId?:number;scene?:'windows'|'shapes'|'atelier-windows'|'observatory';fps?:number;
 backgroundStyle?:WindowApplicationBackgroundStyle;sampling?:WindowApplicationSampling;
 orbitMode?:'spin'|'pendulum';motion?:boolean;
 gradientScreens?:number;gradientAngle?:number;gradientSpeed?:number;gradientPhase?:number;
 pivotX?:number;pivotY?:number;axisPitch?:number;rotationSpeed?:number;secondAxisSpeed?:number;
 swingAngle?:number;swingSeconds?:number;starDensity?:number;starGlyphs?:string;
 starCount?:number;starSpeed?:number;trailMs?:number;travelYaw?:number;travelPitch?:number;
 weatherIntensity?:number;novaStrength?:number;novaRegularity?:number;
 /** Original Observatory aliases: life 200..8000 ms, speed 1..50 world units/s.
  * Only scene observatory accepts these fields. Its particles patch accepts
  * lifeMs/launchSpeed only; simultaneous aliases must have equal values. */
 weatherLifeMs?:number;weatherSpeed?:number;
 particles?:WindowApplicationParticleOptions;atelierParticles?:AtelierApplicationParticleOptions;
 weatherStyle?:'embers'|'sparks'|'nova'|'rain'|'snow'|'ripples';
}
/** The application must already be enabled. Omitted id advances its event
 * serial; omitted atMs uses its current motion clock. x/y default to zero.
 * Native Kinetic bounds: id/atMs 0..2^53-1, x/y -100000..100000.
 * Original Atelier application events retain the source range -1e12..1e12 for all four fields. */
export interface WindowApplicationEventOptions {
 kind:'embers'|'sparks'|'nova'|'rain'|'snow'|'ripples';
 id?:number;x?:number;y?:number;atMs?:number;
}
export interface AtelierApplicationParticleOptions {
 lifeMs?:number;count?:number;speed?:number;gravity?:number;rise?:number;drag?:number;turbulence?:number;glitterHz?:number;trailMs?:number;branches?:number;jaggedness?:number;coreMs?:number;coreRadius?:number;ejecta?:number;shockwave?:number;intensity?:number;seed?:number;reducedMotion?:boolean;
}
export interface WindowContentInfo {
 label:string;sourceIndex:number;text:string;colors:number[];stopWidths:number[];background:number;ink:number;
 lightness:number;chroma:number;brightness:number;hueOffset:number;lockLightness:boolean;feather:number;
 textLightness:number;textChroma:number;waveform:number[];visibility:number;maximized:number;
}
export interface WindowInfo {
 id:number;title:string;text:string;position:Vector3;visible:number;reader:boolean;scrollRow:number;
 width:number;height:number;alpha:number;material:number;group:number;shape:number;
 yaw:number;pitch:number;roll:number;minColumns:number;maxColumns:number;anchorX:number;anchorY:number;
 overshoot:number;scatter:number;bend:number;folds:number;meshColumns:number;meshRows:number;atUs:number;durationUs:number;
 sourcePresentation:boolean;sourceOptions:WindowSourcePresentationOptions|null;effectiveOpacity:number;sourceOrder:number;
 texture:WindowTextureInfo|null;content:WindowContentInfo|null;
 readability:{padding:number;border:0|1|2|3|4;chromeSize:number;fadeStartRatio:number;fadeEndRatio:number};
}
/** A declared UI intention, not an executable callback. The host handles and acknowledges it. */
export interface NotificationAction {id:number;label:string;event:string;value?:number;dismiss?:boolean;}
export type StatusMode = 'static'|'horizontal'|'vertical'|'fade'|'pop'|'horizontal-fade'|'vertical-fade';
/** Fixed and derived dwell are mutually exclusive. Important records require explicit acknowledgement. */
export interface StatusOptions {
 id?:number;area?:number;text:string;durationMs?:number;mode?:StatusMode;priority?:number;
 startTimeUs?:number;x?:number;y?:number;key?:string;coalesce?:'none'|'count'|'replace-queued';
 important?:boolean;actions?:readonly NotificationAction[];dwellPerCharacterMs?:number;
 minDurationMs?:number;maxDurationMs?:number;
}
export type EventPayload=null|boolean|number|string|readonly EventPayload[]|{readonly [key:string]:EventPayload};
export interface NotificationIntent {id:number;messageId:number;actionId:number;messageSequence:number;atUs:number;event:string;value:number;origin?:'host';payload?:EventPayload;}
/** Bounded current-native condition tree: 31 nodes, depth 8. All leaves are evaluated. */
export type IntentValueCondition =
 | {intentValue:{comparison:'above'|'below'|'equal'|'not-equal'|'at-least'|'at-most';value:number;hysteresis?:0}}
 | {intentValue:{comparison:'between';min:number;max:number;hysteresis?:0}};
export type ValueCondition =
 | {all:readonly ValueCondition[]}
 | {any:readonly ValueCondition[]}
 | {not:ValueCondition}
 | {path:string;comparison:'above'|'below'|'equal'|'not-equal'|'at-least'|'at-most';value:number;hysteresis?:number}
 | {path:string;comparison:'between';min:number;max:number;hysteresis?:number}
 | IntentValueCondition;
export type TriggerActionOperand = {value?:number;valueFrom?:never;expression?:never} | {valueFrom:'intentValue';value?:never;expression?:never} | {expression:NumericExpression|DataExpression;value?:never;valueFrom?:never};
export type TriggerOptions = TriggerActionOperand & {id:number;target:string;action?:'set'|'increment';debounceMs?:number;cooldownMs?:number;edge?:'rising'|'falling'|'change'|'level';event?:string} &
 ({source:string;comparison?:'above'|'below'|'equal';threshold?:number;hysteresis?:number;when?:never;whenExpression?:never} |
 {when:ValueCondition;whenExpression?:never;source?:never;comparison?:never;threshold?:never;hysteresis?:never} |
 {whenExpression:DataExpression;when?:never;source?:never;comparison?:never;threshold?:never;hysteresis?:never});
export interface TriggerInfo {id:number;conditionNodes:number;truth:boolean;pending:boolean;fireCount:number;lastFireUs:number;event:string;lastIntent:number;pendingIntent:number;intentCandidate:NotificationIntent|null;valueSource?:"constant"|"intentValue"|"expression";expressionNodes:number;guardExpressionNodes?:number;}
/** Authored numeric properties; native validation owns ranges and target lifetime. */
export type EmitterVectorValueField=`${'position'|'extent'|'velocity'|'spread'|'gravity'|'wind'|'windVariation'|'tumble'|'shapeWeights'|'birthOrientation'|'initialOrientation'|'angularVelocity'}.${'x'|'y'|'z'}`;
export type EmitterValueField='glitterHz'|'glitterDepth'|'coreAlpha'|'residualMs'|'residualAlpha'|EmitterVectorValueField|'alpha'|'surfaceAlpha'|'veinContrast'|'backTint'|'twoSided'|'heat'|'drag'|'lift'|'flutterHz'|'flutterAmount'|'sizeMin'|'sizeMax'|'radius'|'windScale'|'windPeriodSeconds'|'curl'|'nearDistance'|'farDistance'|'farFadeDistance'|'material'|'sampling'|'deposit'|'collision'|'topology'|'count'|'rate'|'cycles'|'gapMs'|'runningTimeMs'|'lifetimeMinMs'|'lifetimeMaxMs'|'tailMs'|'trailMs'|'birthFadeMs'|'deathFadeMs'|'coreMs'|'windX'|'windY'|'windZ';
export type TextValueField='material'|'x'|'y'|'width'|'batchSize'|'durationMs'|'staggerMs'|'jitterMs'|'delayMs'|'distance'|'scatter'|'variation'|'wind'|'overshoot'|'cycles'|'scrambleHz'|'hueSpread'|'reverseOrder'|'randomOrder'|'trailLength'|'local'|'phase'|'easing';
export type FloorValueField='alpha'|'enabled'|'visible'|'height'|'restitution'|'friction'|'settleSpeed'|'reentrainWindSpeed'|'maxIndividual'|'maxTiles'|'overflow'|'retentionMs'|'fadeMs'|'cellSize'|'evaporation'|'sampling';
export type MaterialTrackBase='alpha'|'index'|'hue'|'lightness'|'brightness'|'channels.l'|'channels.c'|'channels.h'|'channels.a'|'channels.b'|'channels.s'|'channels.v'|'channels.r'|'channels.g'|'channels.m'|'channels.y'|'channels.k'|'channels.i';
export type MaterialTrackMember='initial'|'rate'|'min'|'max'|'step'|'periodMs'|'boundary'|'easing'|'seed';
export type MaterialValueField=MaterialTrackBase|`${MaterialTrackBase}.${MaterialTrackMember}`|'hueStep'|'spacing'|'scope'|'blend';
export type NumericValueBinding =
 | {family:'electrical-arc';id:number;field:'speed'|'jitter'|'alpha'|'flicker'|'delayMs'|'holdMs'|'fadeMs'|'repeatMs'}
 | {family:'accessibility';id?:0;field:'reducedMotion'|'screenReader'}
 | {family:'material';id?:number;field:MaterialValueField}
 | {family:'emitter';id:number;field:EmitterValueField}
 | {family:'widget';id:number;field:`data.${number}`|'value'|'alpha'|'material'|'backgroundMaterial'|'selected'|'enabled'|'active'|'x'|'y'|'width'|'height'|'padding'|'min'|'max'|'mode'|'pulseMs'|'cellAspect'|'innerRadius'|'startAngle'|'sweepAngle'|'border'|'sampling'|'revealMs'}
 | {family:'camera';id?:number;field:'position.x'|'position.y'|'position.z'|'yaw'|'pitch'|'roll'|'near'|'far'|'fov'|'span'|'orthographic'}
 | {family:'window';id:number;field:'alpha'|'material'|'position.x'|'position.y'|'position.z'|'yaw'|'pitch'|'roll'|'width'|'height'|'minColumns'|'maxColumns'|'padding'|'chromeSize'|'fadeStartRatio'|'fadeEndRatio'|'anchorX'|'anchorY'|'overshoot'|'scatter'|'bend'|'folds'|'meshColumns'|'meshRows'|'durationMs'|'border'|'shape'|'group'}
 | {family:'area';id:number;field:'alpha'|'material'|'x'|'y'|'width'|'height'|'padding'|'margin'|'speedX'|'speedY'|'hideEmpty'|'fadeMs'|'gapMs'|'border'|'layout'|'parent'}
 | {family:'text';id:number;field:TextValueField}
 | {family:'floor';id?:0;field:FloorValueField}
 | {family:'state';id:number;field:'active'}
 | {family:'node';id:number;field:'position.x'|'position.y'|'position.z'|'pinned'|'color'|'minColumns'|'maxColumns'|'padding'|'shaPrefix'|'showKind'|'showStatus'|'showSha'|'showDetail'}
 | {family:'indicator';id:number;field:'area'|'x'|'y'|'stepMs'|'material'|'cursor'}
 | {family:'prompt';id?:0;field:'mode'|'alpha'|'minRows'|'maxRows'|'border'|'padding'|'active'}
 | {family:'environment';id?:0;field:'background'|'stars'|'starFar'|'sampling'|'style'|'presentation'|'occlusionTint'|'occludedDots'}
 | {family:'field';id:number;field:'x'|'y'|'width'|'speed'|'strength'|'lifeMs'|'material'|'rings'|'continuous'|'falloff'|'frequency'|'phase'|'interference'|'velocity.x'|'velocity.y'|'surface.x'|'surface.y'|'surface.width'|'surface.height'}
 | {family:'float-body';id:number;field:'mass'|'radius'|'fluidDensity'|'gravity'|'drag'|'visible'|'color'|'surfaceId'|'position.x'|'position.y'|'position.z'|'velocity.x'|'velocity.y'|'velocity.z'|'hull.angularVelocity.x'|'hull.angularVelocity.y'|'hull.angularVelocity.z'|'hull.inertia.x'|'hull.inertia.y'|'hull.inertia.z'}
 | {family:'surface-foam';id:number;field:'enabled'|'sourceRate'|'curvatureThreshold'|'decay'|'impactGain'|'color'|'velocity.x'|'velocity.z'}
 | {family:'mesh';id?:0;field:'alpha'|'color'|'sampling'}
 | {family:'triangle';id:number;field:'alpha'|'color'|'thermal.power'|'thermal.ambientTemperature'|'thermal.conductance'}
 | {family:'cell-art';id:number;field:'x'|'y'|'alpha'|'layer'}
 | {family:'surface-wave';id:number;field:`waves.${number}.${'amplitude'|'kx'|'kz'|'omega'|'phase'}`}
 | {family:'flow';id:number;field:'flux'}
 | {family:'surface';id:number;field:'collisionEnabled'|'renderVisible'|'maxIndividual'|'maxTiles'|'overflow'|'restitution'|'friction'|'settleSpeed'|'reentrainWindSpeed'|'retentionMs'|'fadeMs'|'wetnessGain'|'evaporation'|'heatGain'|'cooling'|'thermalEvaporation'|'wetnessDarkening'|'heatColor'|'heatTintStrength'|'thickness.width'|'thickness.speed'|'water.capacity'|'water.evaporationUs'};
export type StringValueBinding=
 | {family:'indicator';id:number;field:'sequence'}
 | {family:'widget';id:number;field:'text'}
 | {family:'window';id:number;field:'text'|'title'}
 | {family:'text';id:number;field:'text'}
 | {family:'node';id:number;field:'label'|'detail'|'kind'|'status'|'sha'};
export type BooleanValueBinding=
 | {family:'accessibility';id?:0;field:'reducedMotion'|'screenReader'}
 | {family:'emitter';id:number;field:'twoSided'|'collision'|'deposit'}
 | {family:'widget';id:number;field:'enabled'|'selected'|'active'}
 | {family:'camera';id?:number;field:'orthographic'}
 | {family:'text';id:number;field:'local'|'reverseOrder'|'randomOrder'}
 | {family:'area';id:number;field:'hideEmpty'}
 | {family:'floor';id?:0;field:'enabled'|'visible'}
 | {family:'state';id:number;field:'active'}
 | {family:'node';id:number;field:'pinned'|'showKind'|'showStatus'|'showSha'|'showDetail'}
 | {family:'indicator';id:number;field:'cursor'}
 | {family:'prompt';id?:0;field:'active'}
 | {family:'surface';id:number;field:'collisionEnabled'|'renderVisible'}
 | {family:'float-body';id:number;field:'visible'}
 | {family:'field';id:number;field:'continuous'}
 | {family:'surface-foam';id:number;field:'enabled'};
export type JsonValueBinding={family:'widget';id:number;field:'data'};
export type ValueBinding=NumericValueBinding|StringValueBinding|JsonValueBinding;
export interface ValueDescriptor {type:'number'|'boolean'|'string'|'json';readonly:boolean;binding:ValueBinding|null;}
export type ValueDefinition=
 | {op:'define';path:string;type?:'json';value:readonly number[];readonly?:boolean;binding:JsonValueBinding}
 | {op:'define';path:string;type?:'number';value?:number;readonly?:boolean;binding?:NumericValueBinding}
 | {op:'define';path:string;type?:'boolean';value:boolean;readonly?:boolean;binding?:BooleanValueBinding}
 | {op:'define';path:string;type?:'string';value:string;readonly?:boolean;binding?:StringValueBinding}
 | {op:'define';path:string;type:'json';value:EventPayload;readonly?:boolean;binding?:never}
 | {op:'define';path:string;type?:never;value:null|readonly EventPayload[]|{readonly [key:string]:EventPayload};readonly?:boolean;binding?:never};
/** Explicit registered component ownership. Floor, mesh and prompt are singletons. */
export type IdentifiedStyleFamily = 'electrical-arc'|'widget'|'window'|'emitter'|'text'|'area'|'indicator'|'node';
export type SingletonStyleFamily = 'floor'|'mesh'|'prompt';
export type StyleFamily = IdentifiedStyleFamily|SingletonStyleFamily;
export type StateTarget = {family:IdentifiedStyleFamily;id:number}|{family:SingletonStyleFamily;id:0};
export interface StateFlags {active:boolean;selected:boolean;hover:boolean;pressed:boolean;disabled:boolean;}
/** Path matching is exact or segment-bounded prefix; no regular expressions. */
export type StateSelector<F extends StyleFamily = StyleFamily> = {
 family:F;id?:F extends SingletonStyleFamily?0:number;role?:string;states?:Partial<StateFlags>;
} & ({path:string;pathPrefix?:never}|{path?:never;pathPrefix?:string});
/** Clamped linear map. Input bounds must increase; output bounds may descend. */
export interface AppearanceMap {path:string;inputMin:number;inputMax:number;outputMin:number;outputMax:number;}
export type AppearanceScalar = number|AppearanceMap;
export interface WidgetAppearance {material?:number;backgroundMaterial?:number;alpha?:AppearanceScalar;sampling?:Sampling|'inherit';}
export interface WindowAppearance {material?:number;alpha?:AppearanceScalar;}
export interface EmitterAppearance {material?:number;alpha?:AppearanceScalar;sampling?:Sampling;surfaceAlpha?:AppearanceScalar;veinContrast?:AppearanceScalar;}
/** The family fixes which native properties can be affected. Leaf-only emitter
 * properties also require every matching existing emitter to be an autumn leaf. */
export type StyleRuleOptions = {id:number;priority?:number;enabled?:boolean} & ({when?:AppearanceCondition;whenExpression?:never}|{whenExpression:AppearanceExpression;when?:never}) & (
 | {selector:StateSelector<'electrical-arc'>;style:WindowAppearance}
 | {selector:StateSelector<'widget'>;style:WidgetAppearance}
 | {selector:StateSelector<'window'>;style:WindowAppearance}
 | {selector:StateSelector<'emitter'>;style:EmitterAppearance}
 | {selector:StateSelector<'text'>;style:{material?:number}}
 | {selector:StateSelector<'area'>;style:WindowAppearance}
 | {selector:StateSelector<'indicator'>;style:{material?:number}}
 | {selector:StateSelector<'node'>;style:{color?:number}}
 | {selector:StateSelector<'floor'>;style:{alpha?:AppearanceScalar;sampling?:Sampling}}
 | {selector:StateSelector<'mesh'>;style:{alpha?:AppearanceScalar;sampling?:Sampling;color?:number}}
 | {selector:StateSelector<'prompt'>;style:{alpha?:AppearanceScalar}}
);
/** Inspection returns resolved numeric policies: sampling -1 inherit, 0 cell,
 * 1 half, 2 braille, 3 hybrid. Authored values never change during resolution. */
export type AppearanceInfo = Partial<Record<'material'|'backgroundMaterial'|'alpha'|'sampling'|'surfaceAlpha'|'veinContrast'|'color',number>>;
export interface RegisteredStateInfo {id:number;path:string;role:string;family:StyleFamily;targetId:number;exists:boolean;states:StateFlags;authored:AppearanceInfo;effective:AppearanceInfo;}
export interface StyleRuleInfo {id:number;priority:number;enabled:boolean;guard:boolean;conditionNodes:number;guardExpressionNodes?:number;}
/** Retained decorative screen-cell resource; scalar zero is transparent padding. */
export interface CellArtCommand {op:'cell-art';id:number;width?:number;height?:number;cells?:readonly (readonly [number,number,number])[];x?:number;y?:number;alpha?:number;layer?:'background'|'overlay';}
/** Native numeric formulas: at most 31 nodes/depth 8; runtime owns bounds. */
export type NumericIntentField='value'|'id'|'messageId'|'actionId'|'messageSequence'|'atUs';
export type NumericOperands=readonly [NumericExpression,NumericExpression,...NumericExpression[]];
type NumericExpressionSlots={path?:never;pointer?:never;intentField?:never;intentPath?:never;literal?:never;concat?:never;and?:never;or?:never;not?:never;equal?:never;lessThan?:never;lessOrEqual?:never;greaterThan?:never;greaterOrEqual?:never;if?:never;array?:never;object?:never;add?:never;subtract?:never;multiply?:never;divide?:never;min?:never;max?:never;negate?:never;abs?:never;clamp?:never;floor?:never;ceil?:never;round?:never;lerp?:never;remap?:never;convert?:never};
interface NumericPath extends Omit<NumericExpressionSlots,'path'|'pointer'> {path:string;pointer?:string;}
interface NumericPayloadPath extends Omit<NumericExpressionSlots,'intentPath'> {intentPath:string;}
interface NumericIntent extends Omit<NumericExpressionSlots,'intentField'> {intentField:NumericIntentField;}
interface NumericAdd extends Omit<NumericExpressionSlots,'add'> {add:NumericOperands;}
interface NumericSubtract extends Omit<NumericExpressionSlots,'subtract'> {subtract:readonly [NumericExpression,NumericExpression];}
interface NumericMultiply extends Omit<NumericExpressionSlots,'multiply'> {multiply:NumericOperands;}
interface NumericDivide extends Omit<NumericExpressionSlots,'divide'> {divide:readonly [NumericExpression,NumericExpression];}
interface NumericMin extends Omit<NumericExpressionSlots,'min'> {min:NumericOperands;}
interface NumericMax extends Omit<NumericExpressionSlots,'max'> {max:NumericOperands;}
interface NumericNegate extends Omit<NumericExpressionSlots,'negate'> {negate:NumericExpression;}
interface NumericAbs extends Omit<NumericExpressionSlots,'abs'> {abs:NumericExpression;}
interface NumericClamp extends Omit<NumericExpressionSlots,'clamp'> {clamp:{value:NumericExpression;min:NumericExpression;max:NumericExpression};}
export type NumericUnit='seconds'|'milliseconds'|'microseconds'|'nanoseconds'|'minutes'|'hours'|'meters'|'centimeters'|'millimeters'|'kilometers'|'degrees'|'radians'|'celsius'|'fahrenheit'|'kelvin';
interface NumericFloor extends Omit<NumericExpressionSlots,'floor'> {floor:NumericExpression;}
interface NumericCeil extends Omit<NumericExpressionSlots,'ceil'> {ceil:NumericExpression;}
interface NumericRound extends Omit<NumericExpressionSlots,'round'> {round:NumericExpression;}
interface NumericLerp extends Omit<NumericExpressionSlots,'lerp'> {lerp:{from:NumericExpression;to:NumericExpression;amount:NumericExpression};}
interface NumericRemap extends Omit<NumericExpressionSlots,'remap'> {remap:{value:NumericExpression;inMin:NumericExpression;inMax:NumericExpression;outMin:NumericExpression;outMax:NumericExpression};}
interface NumericConvert extends Omit<NumericExpressionSlots,'convert'> {convert:{value:NumericExpression;from:NumericUnit;to:NumericUnit};}
interface DataLiteral extends Omit<NumericExpressionSlots,'literal'> {literal:EventPayload;}
type DataOperands=readonly [DataExpression,DataExpression,...DataExpression[]];
interface DataConcat extends Omit<NumericExpressionSlots,'concat'> {concat:DataOperands;}
interface DataAnd extends Omit<NumericExpressionSlots,'and'> {and:DataOperands;}
interface DataOr extends Omit<NumericExpressionSlots,'or'> {or:DataOperands;}
interface DataNot extends Omit<NumericExpressionSlots,'not'> {not:DataExpression;}
interface DataEqual extends Omit<NumericExpressionSlots,'equal'> {equal:readonly [DataExpression,DataExpression];}
interface DataIf extends Omit<NumericExpressionSlots,'if'> {if:{condition:DataExpression;then:DataExpression;else:DataExpression};}
interface DataArray extends Omit<NumericExpressionSlots,'array'> {array:readonly DataExpression[];}
interface DataObject extends Omit<NumericExpressionSlots,'object'> {object:{readonly [key:string]:DataExpression};}
interface DataLessThan extends Omit<NumericExpressionSlots,'lessThan'> {lessThan:readonly [DataExpression,DataExpression];}
interface DataLessOrEqual extends Omit<NumericExpressionSlots,'lessOrEqual'> {lessOrEqual:readonly [DataExpression,DataExpression];}
interface DataGreaterThan extends Omit<NumericExpressionSlots,'greaterThan'> {greaterThan:readonly [DataExpression,DataExpression];}
interface DataGreaterOrEqual extends Omit<NumericExpressionSlots,'greaterOrEqual'> {greaterOrEqual:readonly [DataExpression,DataExpression];}
export type DataExpression=boolean|string|null|NumericExpression|DataLiteral|DataConcat|DataAnd|DataOr|DataNot|DataEqual|DataLessThan|DataLessOrEqual|DataGreaterThan|DataGreaterOrEqual|DataIf|DataArray|DataObject;
export type NumericExpression=number|NumericPath|NumericIntent|NumericPayloadPath|NumericAdd|NumericSubtract|NumericMultiply|NumericDivide|NumericMin|NumericMax|NumericNegate|NumericAbs|NumericClamp|NumericFloor|NumericCeil|NumericRound|NumericLerp|NumericRemap|NumericConvert;
/** Appearance has no event subscription. Literal JSON is data, so intention-shaped
 * keys inside a literal remain valid; executable operands are excluded recursively. */
type AppearanceValueExpression<T> = T extends NumericIntent|NumericPayloadPath|IntentValueCondition ? never
 : T extends DataLiteral ? T
 : T extends readonly unknown[] ? {readonly [K in keyof T]:AppearanceValueExpression<T[K]>}
 : T extends object ? {[K in keyof T]:AppearanceValueExpression<T[K]>} : T;
export type AppearanceExpression=AppearanceValueExpression<DataExpression>;
export type AppearanceNumericExpression=AppearanceValueExpression<NumericExpression>;
export type AppearanceCondition=AppearanceValueExpression<ValueCondition>;
export interface FirstPromptValues {
 effect?:number;
 layout?:1;
 seed?:number;
 stars?:number;
 densityPermille?:number;
 glyphSet?:number;
 starPeriodMinMs?:number;
 starPeriodRangeMs?:number;
 starDutyPermille?:number;
 starFloorPermille?:number;
 starPeakPermille?:number;
 gradientPeriodMs?:number;
 saturationPermille?:number;
 brightnessPermille?:number;
 focusRow?:number;
 neighborSpeedPermille?:number;
 neighborSaturationPermille?:number;
 neighborBrightnessPermille?:number;
 angleDegrees?:number;
 scaleCells?:number;
 hueStepDegrees?:number;
 hueDegreesPerSecond?:number;
 baseHueDegrees?:number;
 pixelMode?:number;
 originX?:number;
 originY?:number;
 valuePermille?:number;
 motion?:number;
 phaseDegrees?:number;
 grainPermille?:number;
 cursorMode?:number;
 borderStyle?:number;
 selection?:number;
 foregroundColor?:number;
 baseColor?:number;
 waveAmplitudePermille?:number;
 starAttackPermille?:number;
 paletteCount?:number;
 starPaletteCount?:number;
 glyphCount?:number;
 modalOpen?:number;
 hueSaturationPermille?:number;
 hueBrightnessPermille?:number;
 cellAspectPermille?:number;
 textScrimPermille?:number;
 promptBands?:number;
 colorMode?:number;
}
/** Original Stage values. Numeric bounds are validated atomically by C.
 * Dimensions, when supplied, must match the current viewport (<=512x256).
 * Array lengths determine palette/glyph counts; explicit counts must agree. */
export interface SourceStageValues {
 /** Width in terminal cells. Range 0..512. */
 width?:number;
 /** Height in terminal cells. Range 0..256. */
 height?:number;
 /** 0 solid; 1 linear; 2 diagonal; 3 wave; 4 rotating linear; 5 plasma; 6 concentric; 7 moire; 8 aurora; 9 interference; 10 chevrons; 11 diamond. Range 0..11. */
 pattern?:0|1|2|3|4|5|6|7|8|9|10|11;
 /** 0 none; 1 row; 2 column; 3 radial; 4 diagonal band. Range 0..4. */
 focusMode?:0|1|2|3|4;
 /** Focus x in Q8 cells (256 = one column). Range -1048576..1048576. */
 focusX?:number;
 /** Focus y in Q8 cells. Range -1048576..1048576. */
 focusY?:number;
 /** Color field cycle in milliseconds. Range 50..3600000. */
 periodMs?:number;
 /** Color saturation in thousandths. Range 0..2000. */
 saturation?:number;
 /** Field brightness blended from base, in thousandths. Range 0..1000. */
 brightness?:number;
 /** Speed multiplier for each cell away from focus. Range 10..1000. */
 speedFalloff?:number;
 /** Saturation multiplier per cell away from focus. Range 0..1000. */
 saturationFalloff?:number;
 /** Brightness multiplier per cell away from focus. Range 0..1000. */
 brightnessFalloff?:number;
 /** Cell height / width in thousandths; circles compensate for this. Range 500..4000. */
 cellAspect?:number;
 /** Gradient wavelength in Q8 cells. Range 64..262144. */
 scale?:number;
 /** Gradient angle in millidegrees. Range -360000..360000. */
 angle?:number;
 /** Rotation axis x in Q8 cells; may lie offscreen. Range -1048576..1048576. */
 pivotX?:number;
 /** Rotation axis y in Q8 cells; may lie offscreen. Range -1048576..1048576. */
 pivotY?:number;
 /** Independent axis rotation / pendulum period. Range 100..3600000. */
 rotationPeriodMs?:number;
 /** 0 fixed axis; 1 continuous rotation; 2 eased pendulum. Range 0..2. */
 rotationMode?:0|1|2;
 /** Pendulum half-amplitude in millidegrees. Range 0..360000. */
 swing?:number;
 /** Color phase in 1/1024 turns. Range -65536..65536. */
 phase?:number;
 /** 0 whole cell; 1 upper/lower half; 2 left/right half; 3 braille dither. Range 0..3. */
 pixelMode?:0|1|2|3;
 /** Deterministic seed. Stable under resize. Range 0..2147483647. */
 seed?:number;
 /** Opaque bottom color, packed RGB. Range 0..16777215. */
 baseColor?:number;
 /** Default foreground, packed RGB. Range 0..16777215. */
 inkColor?:number;
 /** Number of configured gradient colors (binding-managed). Range 1..32. */
 paletteCount?:number;
 /** 0 seamless loop; 1 mirrored forward/back; 2 hard cyclic stops. Range 0..2. */
 gradientWrap?:0|1|2;
 /** 0 encoded RGB linear; 1 eased RGB interpolation. Range 0..1. */
 interpolation?:0|1;
 /** 0 palette; 1 full HSV wheel; 2 three phase-separated RGB sine channels. Range 0..2. */
 colorMode?:0|1|2;
 /** Hue-wheel offset in degrees. Range -3600..3600. */
 hueOffset?:number;
 /** Enable stable-glyph twinkling stars. Range 0..1. */
 stars?:0|1;
 /** Chance per cell, in thousandths. Range 0..1000. */
 starDensity?:number;
 /** Minimum independent star period. Range 100..3600000. */
 starMinMs?:number;
 /** Additional deterministic period range. Range 0..3600000. */
 starRangeMs?:number;
 /** Visible portion of a star cycle, in thousandths. Range 1..1000. */
 starDuty?:number;
 /** Peak star opacity relative to its configured peak color. Range 0..1000. */
 starPeak?:number;
 /** Number of chosen ordinary star glyphs. Range 1..32. */
 starGlyphCount?:number;
 /** Number of star peak colors. Range 1..32. */
 starColorCount?:number;
 /** Per world-tile chance per nova cycle, in thousandths. Zero disables automatic novae. Range 0..1000. */
 novaChance?:number;
 /** Stable world-tile nova opportunity cycle. Range 1000..3600000. */
 novaCycleMs?:number;
 /** Nova glyph evolution and shockwave duration. Range 100..30000. */
 novaDurationMs?:number;
 /** Ordered expansion glyph sequence; contracts on fade. Range 1..16. */
 novaGlyphCount?:number;
 /** Shockwave propagation in Q8 cells per second. Range 1..262144. */
 rippleSpeed?:number;
 /** Soft ring thickness in Q8 cells. Range 16..8192. */
 rippleWidth?:number;
 /** Lifetime of a user/data ripple. Range 100..30000. */
 rippleLifeMs?:number;
 /** Peak background ring opacity. Range 0..1000. */
 rippleOpacity?:number;
 /** Number of trailing concentric wavefronts. Range 1..6. */
 rippleRings?:number;
 /** 0 evaluates decorative fields at time zero; host pause holds explicit time instead. Range 0..1. */
 motion?:0|1;
 /** 0 RGB; 1 canonical ANSI16 approximation; 2 xterm256 approximation. Range 0..2. */
 quantize?:0|1|2;
 /** World origin x in whole cells; stable sky coordinates. Range -4096..4096. */
 originX?:number;
 /** World origin y in whole cells. Range -4096..4096. */
 originY?:number;
 /** Wave deformation in thousandths. Range 0..4000. */
 waveAmplitude?:number;
 /** Fraction of visible star lifetime used for brightening. Range 10..990. */
 starAttack?:number;
 /** Reverse decorative phase and continuous rotation. Range 0..1. */
 reverse?:0|1;
}
export interface SourceStageConfig {values?:SourceStageValues;palette?:readonly number[];starPalette?:readonly number[];glyphs?:readonly number[];novaGlyphs?:readonly number[];}
/** Positions are cells, packed to original Q8 via round(x*256). */
export interface SourceStageImpulse {x:number;y:number;atMs:number;strength?:number;kind?:0|1;id?:number;}
export interface SourceStageInfo {enabled:boolean;timeMs:number;config:{values:Required<SourceStageValues>;palette:number[];starPalette:number[];glyphs:number[];novaGlyphs:number[]};events:Required<SourceStageImpulse>[];}

/** Original Workbench stack. Text strings retain their complete scalar content. */
export type SourceModalKind='center'|'fullscreen'|'drawer-left'|'drawer-right'|'drawer-top'|'drawer-bottom'|'corner'|'toast'|'error'|'confirmation'|'dropdown';
export interface SourceModalEntry {id:string;kind:SourceModalKind;title:string;body:string;atMs:number;dismissible:boolean;}
export interface SourceModalInfo {componentIds:number[];depth:number;revision:number;blocking:boolean;associated:boolean;workspace:string;context:string;query:string;selected:number;entries:readonly (SourceModalEntry & {context:string;query:string;selected:number})[];}
export type NativeCommand =
 | {op:"source-modal";action:"push";entry:SourceModalEntry;context:string;workspace?:string}
 | {op:"source-modal";action:"edit";context?:string;query?:string;selected?:number;workspace?:string}
 | {op:"source-modal";action:"dismiss"|"clear"}
 | {op:"source-modal";action:"associate";componentIds:readonly number[];boxId:number}
 | {op:'model-view';width?:number;height?:number;controls?:SceneArtControls}
 | {op:'remove-model-view'}
 | ({op:'scene-art'} & SceneArtOptions)
 | {op:'remove-scene-art'}
 | {op:'burst-style';id:number;glitterHz?:number;glitterDepth?:number;coreAlpha?:number;residualMs?:number;residualAlpha?:number;coreMs?:number}
 | {op:'corona-style';id:number;paint?:'source'|'material';speed?:number;width?:number;intensity?:number;durationMs?:number}
 | {op:'remove-corona-style';id:number}
 | {op:'observatory-style';id:number;paint?:'source'|'material';seed?:number;speed?:number;intensity?:number;durationMs?:number}
 | {op:'remove-observatory-style';id:number}
 | {op:'studio-style';id:number;paint?:'source'|'material';seed?:number;novaDurationMs?:number;rippleSpeed?:number;rippleWidth?:number;rippleOpacity?:number;rippleRings?:number;cellAspect?:number;strength?:number;waveScale?:number;glyphs?:string;palette?:number[];starPalette?:number[]}
 | {op:'remove-studio-style';id:number}
 | {op:'world-style';id:number;paint?:'source'|'material';seed?:number;count?:number;scale?:number;lifeMs?:number;gravity?:number}
 | {op:'remove-world-style';id:number}
 | {op:'thermal-style';id:number;paint?:'source'|'material';seed?:number;lifeMs?:number}
 | {op:'remove-thermal-style';id:number}
 | {op:'atelier-style';id:number;paint?:'source'|'material';lifeMs?:number;count?:number;speed?:number;gravity?:number;rise?:number;drag?:number;turbulence?:number;glitterHz?:number;trailMs?:number;branches?:number;jaggedness?:number;coreMs?:number;coreRadius?:number;ejecta?:number;shockwave?:number;intensity?:number;seed?:number;eventId?:number;reducedMotion?:boolean}
 | {op:'remove-atelier-style';id:number}
 | {op:'kinetic-style';id:number;paint?:'source'|'material';count?:number;lifeMs?:number;launchSpeed?:number;gravity?:number;drag?:number;wind?:number;flickerHz?:number;trailMs?:number;branches?:number;arcSegments?:number;arcJitter?:number;coreMs?:number;shockwave?:number;explosionForce?:number;seed?:number;eventId?:number;brightness?:number;glyphs?:string;emberSpread?:number;arcReach?:number}
 | {op:'remove-kinetic-style';id:number}
 | {op:'electrical-arc';id:number;points:readonly {position:readonly [number,number,number];parent:number}[];seed?:number;material?:number;speed?:number;jitter?:number;alpha?:number;flicker?:number;delayMs?:number;holdMs?:number;fadeMs?:number;repeatMs?:number}
 | {op:'remove-electrical-arc';id:number}
 | CellArtCommand
 | {op:'remove-cell-art';id:number}
 | {op:'reset';seed?:number;preservePrompt?:boolean}
 | {op:'time';timeUs:number;budget?:number}
 | {op:'resize';width:number;height:number}
 | {op:'pause';paused:boolean}
 | {op:'accessibility';reducedMotion?:boolean;screenReader?:boolean}
 | {op:'batch';commands:readonly SceneEdit[]}
 | {op:'schedule';id:number;atUs:number;command:SceneEdit|{op:'batch';commands:readonly SceneEdit[]}}
 | {op:'cancel-schedule';id:number}
 | ({op:'camera'} & CameraOptions)
 | ({op:'camera-controls'} & CameraControlsOptions)
 | {op:'camera-controls';enabled:false}
 | {op:'camera-input';delta:Vector3;pan?:boolean}
 | {op:'flight';steps:readonly MotionStep[];profile?:'original'}
 | {op:'flight';profile:'original';cruise:{speed:number;heading?:{yaw:number;pitch:number}}}
 | {op:'flight';profile:'original';orbit:{mode?:'stable'|'escape'|'falling';target?:Vector3;periodSeconds?:number;radialRate?:number;bank?:number}}
 | {op:'camera-action';action:'rotate';yaw?:number;pitch?:number}
 | {op:'camera-action';action:'move';local:Vector3}
 | {op:'camera-action';action:'dolly';units:number}
 | {op:'camera-action';action:'view';name:'front'|'back'|'left'|'right'|'top'|'bottom'|'iso'}
 | {op:'camera-action';action:'fit';points?:Vector3[];width?:number;height?:number;padding?:number}
 | {op:'look';yaw?:number;pitch?:number;roll?:number}
 | {op:'brake'}
 | ({op:'emitter'} & EmitterOptions)
 | ({op:'weather-author'} & WeatherAuthorOptions)
 | ({op:'surface'} & SurfaceOptions)
 | {op:'mesh-style';triangleIndex?:never;alpha?:number;color?:number;sampling?:Sampling}
 | {op:'mesh-style';triangleIndex:number;alpha?:number;color?:number;sampling?:never}
 | ({op:'surface-waves'} & SurfaceWavesOptions)
 | ({op:'surface-foam'} & SurfaceFoamOptions)
 | {op:'surface-foam-transport';surfaceId:number;velocity:[number,number]}
 | {op:'clear-surface-foam';surfaceId:number}
 | ({op:'float-body'} & FloatBodyOptions)
 | {op:'remove-float-body';id:number}
 | {op:'float-hull';id:number;vertices:[number,number,number][];faces:[number,number,number][];inertia:[number,number,number];centerOfMass?:[number,number,number];orientation?:[number,number,number,number];angularVelocity?:[number,number,number]}
 | {op:'remove-float-hull';id:number}
 | {op:'surface-fluid';surfaceId:number;mass:number;velocity?:Vector3}
 | {op:'surface-fluid-angular';surfaceId:number;inertia:number;omega?:Vector3;pivot?:Vector3;orientation?:readonly [number,number,number,number]}
 | {op:'stop-surface-fluid';surfaceId:number}
 | {op:'export-surface-fluid';surfaceId:number}
 | {op:'clear-surface';id:number;scope:'response'|'deposits'|'all'}
 | {op:'emitter-colliders';id:number;colliders:ColliderSelection}
 | {op:'emitter-style';id:number;sampling?:Sampling;surfaceAlpha?:number;veinContrast?:number;backTint?:number;twoSided?:boolean}
 | {op:'forces';id:number;wind?:Vector3;windVariation?:Vector3;gravity?:Vector3;drag?:number;heat?:number}
 | {op:'stop';id:number;style?:EndStyle;tailMs?:number}
 | {op:'resume';id:number}
 | {op:'cancel';id:number;style?:Exclude<EndStyle,'drain'>;tailMs?:number}
 | {op:'clear-instance';id:number}
 | {op:'clear-deposits';emitterId?:number}
 | {op:'clear';scope?:'weather'|'deposits'|'graph'|'text'|'status'}
 | {op:'floor';sampling?:Sampling;enabled?:boolean;visible?:boolean;height?:number;restitution?:number;friction?:number;settleSpeed?:number;reentrainWindSpeed?:number;maxIndividual?:number;maxTiles?:number;overflow?:'reject-new'|'merge-to-field';retentionMs?:number;fadeMs?:number;evaporation?:number;cellSize?:number;alpha?:number}
 | ({op:'material'} & MaterialOptions)
 | {op:'flow';id:number;flux:number;stages:readonly {name:string;delayUs?:number;tailUs?:number}[]}
 | {op:'flow-rate';id:number;flux:number}
 | {op:'flow-surface';surfaceId:number;flowId:number;stage:string;referenceFlux:number}
 | {op:'remove-flow-surface';surfaceId:number}
 | {op:'flow-thickness';surfaceId:number;width:number;speed:number;maxDepth:number;direction?:Vector3}
 | ({op:'flow-thickness-settings';surfaceId:number}&({width:number;speed?:number}|{width?:number;speed:number}))
 | {op:'remove-flow-thickness';surfaceId:number}
 | {op:'flow-sink';surfaceId:number;flowId:number;fraction:number;capacity:number;evaporationUs?:number}
 | {op:'flow-spray';flowId:number;emitterId:number;fraction:number;particleVolume:number}
 | {op:'waterfall';channelSurfaceId:number;sheetSurfaceId:number;flowId:number;channelStage:string;sheetStage:string;referenceFlux:number;drop:number;color?:number;alpha?:number}
 | {op:'surface-water';surfaceId:number;capacity:number;evaporationUs?:number}
 | {op:'surface-water-add';triangleIndex:number;volume:number}
 | ({op:'surface-water-settings';surfaceId:number;capacity?:number;evaporationUs?:number}&({capacity:number}|{evaporationUs:number}))
 | {op:'aggregate-reemit';tileIndex:number;count:number;velocity:Vector3}
 | {op:'material-thermal';id:number;temperature:number;capacity:number;contactFraction?:number;conductance?:number}
 | {op:'remove-material-thermal';id:number}
 | {op:'surface-water-thermal';triangleIndex:number;latentHeatPerVolume:number}
 | {op:'surface-water-transfer';fromTriangle:number;toTriangle:number;volume:number;heatCapacityPerVolume?:number}
 | {op:'surface-water-link';id:number;fromTriangle:number;toTriangle:number;rate:number;heatCapacityPerVolume?:number}
 | {op:'remove-surface-water-link';id:number}
 | {op:'surface-water-reemit';triangleIndex:number;emitterId:number;volume:number}
 | {op:'surface-thermal';triangleIndex:number;temperature:number;capacity:number;ambientTemperature?:number;conductance?:number;power?:number}
 | {op:'surface-thermal-power';triangleIndex:number;power:number}
 | ({op:'surface-thermal-settings';triangleIndex:number;ambientTemperature?:number;conductance?:number;power?:number}&({ambientTemperature:number}|{conductance:number}|{power:number}))
 | {op:'surface-thermal-transfer';fromTriangle:number;toTriangle:number;energy:number}
 | {op:'surface-thermal-link';id:number;fromTriangle:number;toTriangle:number;conductance:number}
 | {op:'remove-surface-thermal-link';id:number}
 | {op:'environment';starProfile?:'default'|'source';worldSeed?:number;skyDensity?:number;skyRadius?:number;skyExposure?:number;trailMs?:number;textLightness?:number;textChroma?:number;background?:number;stars?:number;starFar?:number;sampling?:'cell'|'half'|'braille'|'hybrid';style?:'solid'|'linear'|'plasma'|'wave'|'caustic'|'contours';presentation?:EnvironmentPresentation;/** 0..1, default 1: how strongly hidden braille-family particles tint the cell background. */occlusionTint?:number;occludedDots?:OccludedDots}
 | {op:'field';effect?:string;x?:number;y?:number;lifeMs?:number;speed?:number;width?:number;strength?:number;material?:number;seed?:number;optics?:'legacy'|'source';paint?:'field'|'source';rings?:number;continuous?:boolean;falloff?:number;frequency?:number;phase?:number;interference?:number;velocity?:readonly [number,number];surface?:{x:number;y:number;width:number;height:number}}
 | {op:'remove-field';id:number}
 | {op:'input';text:string}
 | {op:'paste';text:string}
 | {op:'select';anchor?:number;caret?:number;unit?:'scalar'|'grapheme';id?:never;durationMs?:never}
 | {op:'draft';text:string;caret?:number;emitWeather?:boolean}
 | {op:'key';key:string;unit?:'scalar'|'grapheme';ctrl?:boolean;shift?:boolean;alt?:boolean;meta?:boolean}
 | {op:'prompt-appearance';cursor?:PromptCursorAppearance;weather?:PromptTypingWeather}
 | {op:'prompt-source';enabled?:boolean;values?:FirstPromptValues;palette?:readonly number[];starPalette?:readonly number[];glyphs?:readonly number[];layer?:PromptSourceLayer|null}
 | {op:'prompt';layout?:'scalar'|'grapheme'|'bidi';direction?:'ltr'|'rtl'|'auto';ambiguousWidth?:1|2;mode?:PromptMode;alpha?:number;minRows?:number;maxRows?:number;border?:Border;padding?:number;active?:boolean;presentation?:'compact'|'framed';background?:number|string;foreground?:number|string;accent?:number|string;selectionColor?:number|string;paddingX?:number;paddingY?:number;margin?:number;inlineRows?:number;inlineWidth?:number;lineNumbers?:boolean;selected?:boolean;hueStep?:number;hueSpeed?:number;huePeriodMs?:number;maxChars?:number}
 | ({op:'text'} & TextOptions)
 | ({op:'widget'} & WidgetOptions)
 | {op:'source-stage';enabled?:boolean;config?:SourceStageConfig;timeMs?:number;events?:readonly SourceStageImpulse[]}
 | ({op:'observatory-overlay'} & ObservatoryOverlayOptions)
 | ({op:'source-stage-component'} & SourceStageComponentOptions)
 | {op:'remove-source-stage-component';id:number}
 | ({op:'window'} & WindowOptions)
 | ({op:'window-texture'} & WindowTextureOptions)
 | {op:'remove-window-texture';id:number}
 | ({op:'window-content'} & WindowContentOptions)
 | {op:'remove-window-content';id:number}
 | ({op:'window-application'} & WindowApplicationOptions)
 | ({op:'window-application-event'} & WindowApplicationEventOptions)
 | {op:'remove-window-application'}
 | {op:'window-action';id:number;action:WindowAction;rows?:number;dx?:number;dy?:number;forward?:number;yaw?:number;pitch?:number;roll?:number;durationMs?:number;effect?:string;group?:number}
 | {op:'dock-page';page:number}
 | {op:'gather';group?:number}
 | {op:'node';id:number;label?:string;detail?:string;kind?:string;status?:string;sha?:string;position?:Vector3;pinned?:boolean;color?:number;minColumns?:number;maxColumns?:number;padding?:number;shaPrefix?:number;showKind?:boolean;showStatus?:boolean;showSha?:boolean;showDetail?:boolean}
 | {op:'edge';from:number;to:number;kind?:'contains'|'depends'|'parent'|'reference'|'produces'|'related'}
 | {op:'layout';profile?:'source';dimensions?:2|3;mode?:'layered'|'force'|'radial';iterations?:number;spacing?:number;seed?:number;nodeGap?:number;layerGap?:number;depthGap?:number;repulsion?:number;spring?:number;linkLength?:number;damping?:number;timeStep?:number;sweeps?:number;collision?:number;orientation?:'TB'|'LR';nodeSizes?:Array<{id:number;width?:number;height?:number}>;edgeWeights?:Array<{from:number;to:number;kind?:'contains'|'depends'|'parent'|'reference'|'produces'|'related';weight:number}>}
 | {op:'inspector-scroll';rows:number}
 | {op:'select';id:number;durationMs?:number;anchor?:never;caret?:never;unit?:never}
 | ({op:'area'} & AreaOptions)
 | ({op:'status'} & StatusOptions)
 | {op:'notification-action';id:number;actionId:number}
 | {op:'emit-intent';event:string;value?:number;payload?:EventPayload}
 | {op:'ack-intent';id:number}
 | {op:'ack-status';id:number}
 | {op:'dismiss'|'purge-status';id:number}
 | {op:'indicator';id:number;area?:number;x?:number;y?:number;sequence?:string;stepMs?:number;material?:number;cursor?:boolean}
 | {op:'state-register';id:number;path:string;role:string;target:StateTarget;active?:boolean}
 | {op:'state-update';id:number;role?:string;active?:boolean}
 | {op:'state-unregister';id:number}
 | ({op:'style-rule'} & StyleRuleOptions)
 | {op:'remove-style-rule';id:number}
 | {op:'character-rule';rule:CharacterRule}
 | {op:'remove-character-rule';id:string}
 | {op:'character-region';region:CharacterRegion}
 | {op:'remove-character-region';id:string}
 | {op:'remove-value';path:string}
 | {op:'remove-trigger';id:number}
 | ValueDefinition
 | {op:'bind';path:string;binding:ValueBinding|null}
 | {op:'set';path:string;value:EventPayload;expression?:never;intentId?:never}
 | {op:'set';path:string;expression:NumericExpression|DataExpression;intentId?:number;value?:never}
 | ({op:'trigger'} & TriggerOptions)
 | {op:'mesh';subdivisions?:number;append?:boolean;sampling?:Sampling;triangles?:readonly MeshTriangle[]}
 | ({op:'model-import'} & ModelImportOptions)
 | ({op:'ribbon'} & RibbonOptions)
 | ({op:'path-travel'} & PathTravelOptions)
 | {op:'remove-path-travel';id:number}
 | {op:'wheel';delta:number;shift?:boolean;x?:number;y?:number}
 | {op:'pointer';phase?:'down'|'move'|'up'|'cancel';x:number;y:number;button?:0|1|2;shift?:boolean;alt?:boolean};

/** No clocks, reset, routing or nested transactions inside atomic/scheduled edits. */
export type SceneEdit = Exclude<NativeCommand, {op:'batch'|'schedule'|'cancel-schedule'|'time'|'reset'|'pointer'|'wheel'|'pause'}>;
export type WindowAction = 'fade'|'restore'|'minimize'|'close'|'maximize'|'move'|'rotate'|'summon'|'visit'|'background'|'roll-up'|'roll-down'|'read'|'scroll'|'page-next'|'page-prev';
export interface ClockInfo {timeUs:number;step:number;targetUs:number;paused:boolean;pending:boolean;}
export interface StatusRecord {id:number;area:number;text:string;priority:number;state:'queued'|'active'|'expired'|'dismissed';readyUs:number;startUs:number;durationUs:number;sequence:number;key:string;occurrences:number;replacements:number;important:boolean;acknowledged:boolean;actions:readonly (NotificationAction & {activated:boolean})[];}

/** Original Observatory workspace typography/connector controls. */
export type ObservatoryOverlayOptions={enabled:false}|{enabled?:true;kind?:'text'|'dag'|'spatial-menu'|'warp';/** Original0..4000ms. */fallMs?:number;/** Original-90..90degrees. */hueStep?:number;/** Original-90..90degrees/second. */textHueSpeed?:number;flatNavigation?:boolean};
export type ObservatoryOverlayInfo={enabled:false}|{enabled:true;kind:'text'|'dag'|'spatial-menu'|'warp';flatNavigation:boolean;fallMs:number;hueStep:number;textHueSpeed:number};
