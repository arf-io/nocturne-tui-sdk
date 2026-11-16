import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const nested:NativeCommand={op:'weather-author',schema:'nocturne.weather-authoring/v1',id:1,effect:'weather/autumn-drift',emission:{rate:4,cycles:2,gapMs:250,startTimeUs:250000,schedule:'seeded-jitter'},birth:{distribution:'uniform',orientation:[10,20,30]},forces:{windScale:1.2,windPeriodSeconds:2},particle:{backTint:.3,birthFadeMs:100,deathFadeMs:200,twoSided:true},lifecycle:{endStyle:'dissolve',tailMs:500}};
// @ts-expect-error schema is closed and versioned
const bad:NativeCommand={op:'weather-author',schema:'unsupported',id:1,effect:'weather/autumn-drift'};
void [nested,bad];
