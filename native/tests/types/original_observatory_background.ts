import type { NativeCommand, WindowApplicationOptions } from '../../bindings/typescript/contracts.js';
const surface: WindowApplicationOptions = {scene:'observatory',paletteWindowId:1,weatherLifeMs:8000,weatherSpeed:50,starSpeed:14,travelYaw:31,travelPitch:-12,trailMs:130};
const command: NativeCommand = {op:'window-application',...surface};
const retained: NativeCommand = {op:'window-application',scene:'windows',particles:{gravity:8,launchSpeed:9}};
// @ts-expect-error Unknown source scene must be rejected.
const badScene: NativeCommand = {op:'window-application',scene:'unknown'};
// @ts-expect-error Original duration is numeric milliseconds.
const badLife: WindowApplicationOptions = {scene:'observatory',weatherLifeMs:'8000'};
// @ts-expect-error Original speed is numeric world units per second.
const badSpeed: NativeCommand = {op:'window-application',weatherSpeed:true};
void [command,retained,badScene,badLife,badSpeed];
