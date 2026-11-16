import {NativeScene} from './native_scene.mjs';import type {NativeCommand,ObservatoryOverlayInfo} from './contracts.js';declare const s:NativeScene;
const q:NativeCommand={op:'observatory-overlay',kind:'text',fallMs:0,hueStep:-90,textHueSpeed:90,flatNavigation:false};s.command(q);s.command({op:'observatory-overlay',kind:'warp'});s.command({op:'observatory-overlay',enabled:false});const info:ObservatoryOverlayInfo=s.info().observatoryOverlay;if(info.enabled){const kind:'text'|'dag'|'spatial-menu'|'warp'=info.kind;}
// @ts-expect-error unsupported workspace
s.command({op:'observatory-overlay',kind:'windows'});
// @ts-expect-error original flat navigation is boolean
s.command({op:'observatory-overlay',flatNavigation:1});
// @ts-expect-error disabled record has no patch
s.command({op:'observatory-overlay',enabled:false,fallMs:1});
