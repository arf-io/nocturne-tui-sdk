import {ScenicOriginalClock,ScenicOriginalSession,SCENIC_PRESETS} from '../../bindings/typescript/scenic_original.mjs';
import type {NativeScene} from '../../bindings/typescript/native_scene.mjs';
declare const native:NativeScene;
const clock=new ScenicOriginalClock('pearl-cascade');clock.configure(1700,{waterFlow:1.6,landscapeSpeed:37});native.command(clock.sample(2301));ScenicOriginalClock.fromSnapshot(clock.snapshot());
const session=new ScenicOriginalSession(native,'tidal-glass');session.configure({waterFlow:0});session.advanceTo(1000000,12);session.restore(session.checkpoint());native.command({op:'scene-art',detail:SCENIC_PRESETS.moonlight});
// @ts-expect-error not an original source scene
new ScenicOriginalClock('generic-ocean');
// @ts-expect-error source rates are numeric
clock.configure(1700,{waterFlow:'fast'});
// @ts-expect-error other controls are native scene-art fields
clock.configure(1700,{projection:0});
