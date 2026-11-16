import type {NativeCommand} from '../../bindings/typescript/contracts.js';import type {NativeScene} from '../../bindings/typescript/native_scene.mjs';
const cmd:NativeCommand={op:'prompt',layout:'grapheme',ambiguousWidth:2};declare const scene:NativeScene;const rows:number[][]=scene.promptLayout();
// @ts-expect-error ambiguity is1or2
const bad:NativeCommand={op:'prompt',ambiguousWidth:3};void [cmd,rows,bad];

const layout:'scalar'|'grapheme'|'bidi'=scene.info().prompt.layout;const ambiguous:1|2=scene.info().prompt.ambiguousWidth;void [layout,ambiguous];

const originalPrompt: import("../../bindings/typescript/contracts.js").NativeCommand={op:"prompt-source",enabled:true,values:{layout:1,effect:1,cursorMode:3,gradientPeriodMs:1800},palette:[0x416d78,0x896273]};
void originalPrompt;
