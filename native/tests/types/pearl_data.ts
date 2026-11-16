import {NativeScene} from '../../bindings/typescript/native_scene.mjs';
import {StudioDataSource,observatorySample} from '../../bindings/typescript/pearl_data.mjs';
import {PearlStageSession} from '../../bindings/typescript/pearl_stage.mjs';
declare const scene:NativeScene;
const studio=new StudioDataSource();studio.advanceTo(94,{onCommit:row=>row.value});studio.promptCommit('文');observatorySample(50).bus[0].quality satisfies 'synthetic';
const fleet=new PearlStageSession(scene,'fleet');fleet.fleet?.configure({arrivalMs:520,readMode:true});fleet.advanceBudgetedTo(80,12);fleet.fleet?.send('local');
// @ts-expect-error exact known source families
new PearlStageSession(scene,'invented');
// @ts-expect-error source time is numeric
studio.advanceTo('47');
// @ts-expect-error source options preserve boolean policy
fleet.fleet?.configure({readMode:1});

const cp=fleet.checkpoint();fleet.restoreCheckpoint(cp);new PearlStageSession(scene,'fleet',{revision:'initial'});
// @ts-expect-error explicit original source revisions
new PearlStageSession(scene,'fleet',{revision:'fake'});
