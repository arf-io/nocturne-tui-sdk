import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const source: NativeCommand = {op:'text',id:1,effect:'text/glyph-fall',phaseModel:'source'};
const extension: NativeCommand = {op:'text',id:1,effect:'text/ash-type',phaseModel:'reverse-show'};
// @ts-expect-error unsupported phase model
const unknown: NativeCommand = {op:'text',id:1,phaseModel:'invented'};
// @ts-expect-error model is an enumerated string
const numeric: NativeCommand = {op:'text',id:1,phaseModel:1};
void [source,extension,unknown,numeric];
