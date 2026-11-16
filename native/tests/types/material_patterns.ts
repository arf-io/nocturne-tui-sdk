import type {NativeCommand, MaterialPatternOptions} from '../../bindings/typescript/contracts.js';
const pattern:MaterialPatternOptions={kind:'wave',focusMode:'radial',focusXQ8:123,
  palette:[0x123456,0xffffff],motion:true,reverse:false,rotationMode:'pendulum',
  gradientWrap:'mirror',interpolation:'eased',colorMode:'hsv'};
const apply:NativeCommand={op:'material',id:5,pattern,alpha:.75};
const clear:NativeCommand={op:'material',id:5,pattern:null};
// @ts-expect-error pattern names are closed
const unknown:NativeCommand={op:'material',pattern:{kind:'unknown'}};
// @ts-expect-error motion is a boolean
const wrong:NativeCommand={op:'material',pattern:{motion:1}};
void [apply,clear,unknown,wrong];
