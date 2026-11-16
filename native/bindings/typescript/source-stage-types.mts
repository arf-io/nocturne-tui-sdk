import {NativeScene} from './native_scene.mjs';import type {NativeCommand,SourceStageConfig} from './contracts.js';
declare const s:NativeScene;const config:SourceStageConfig={values:{pattern:11,pixelMode:3,motion:0},palette:[0x123456],glyphs:[0x2801]};const command:NativeCommand={op:'source-stage',config,timeMs:4294967301,events:[{x:1.5,y:2,atMs:0,id:100001}]};s.command(command);const h:{id:number;item:number}|null=s.sourceStageHit(1,2);s.sourceStageTween(0,1,2,3,1);s.sourceStageInkOpacity(420,420,768,1536,760);
// @ts-expect-error invalid original pixel mode
s.command({op:'source-stage',config:{values:{pixelMode:4}}});
// @ts-expect-error config glyphs are scalar integers, not strings
s.command({op:'source-stage',config:{glyphs:['x']}});
// @ts-expect-error every impulse requires its original timestamp
s.command({op:'source-stage',events:[{x:0,y:0}]});
// @ts-expect-error invalid easing
s.sourceStageTween(0,1,0,1,4);
