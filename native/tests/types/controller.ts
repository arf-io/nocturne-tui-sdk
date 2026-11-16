import type {NativeCommand,SceneEdit} from '../../bindings/typescript/contracts.js';
const preserve:NativeCommand={op:'reset',seed:99,preservePrompt:true};
const clear:NativeCommand={op:'reset',preservePrompt:false};
const clock:NativeCommand={op:'time',timeUs:1000000,budget:120};
// @ts-expect-error preservePrompt must be boolean
const bad:NativeCommand={op:'reset',preservePrompt:1};
// @ts-expect-error reset remains excluded from atomic/scheduled SceneEdit
const nested:SceneEdit={op:'reset',preservePrompt:true};
void [preserve,clear,clock,bad,nested];
