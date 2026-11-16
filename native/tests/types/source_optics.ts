import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const source:NativeCommand={op:'field',effect:'surface-field/opal-fronts',optics:'source'};
const legacy:NativeCommand={op:'field',optics:'legacy'};
// @ts-expect-error optics is an explicit native enum
const invalid:NativeCommand={op:'field',optics:'kinetic'};
void [source,legacy,invalid];

const originalPaint:NativeCommand={op:'field',effect:'surface-field/silk-tide',paint:'source'};
const retainedField:NativeCommand={op:'field',paint:'field'};
// @ts-expect-error paint is a finite native choice
const invalidPaint:NativeCommand={op:'field',paint:'recovered'};
void [originalPaint,retainedField,invalidPaint];
