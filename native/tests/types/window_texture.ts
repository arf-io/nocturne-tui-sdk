import type {NativeCommand,WindowTextureInfo,WindowTextureOptions} from '../../bindings/typescript/contracts.js';
const init:NativeCommand={op:'window-texture',id:1,width:100,height:40};
const patch:NativeCommand={op:'window-texture',id:1,offset:10,cells:[[0x28ff,0xaabbcc,0x112233],[0x2580,1,2]]};
const remove:NativeCommand={op:'remove-window-texture',id:1};
const options:WindowTextureOptions={id:2,width:2,height:2};
const info:WindowTextureInfo={width:1,height:1,cells:[[65,1,2]]};
// @ts-expect-error exactly glyph/foreground/background, not a hit ID
const extra:NativeCommand={op:'window-texture',id:1,cells:[[65,1,2,3]]};
// @ts-expect-error glyph is a Unicode scalar number
const stringGlyph:NativeCommand={op:'window-texture',id:1,cells:[['A',1,2]]};
// @ts-expect-error offset must be numeric
const badOffset:WindowTextureOptions={id:1,offset:'one'};
void [init,patch,remove,options,info,extra,stringGlyph,badOffset];
