import type {NativeCommand,WindowContentInfo,WindowContentOptions,WindowInfo} from '../../bindings/typescript/contracts.js';

const initial:NativeCommand={op:'window-content',id:7,label:'source.7',sourceIndex:2,
 text:'A window-owned source',colors:[0x345678,0xccaabb],stopWidths:[.25,2],
 background:0x101319,ink:0xdfd8cc,lightness:.62,chroma:.14,brightness:.28,
 hueOffset:18,lockLightness:true,feather:.8,textLightness:.83,textChroma:.1,
 waveform:[0,.5,-.5,1]};
const patch:WindowContentOptions={id:7,text:'Updated source'};
const remove:NativeCommand={op:'remove-window-content',id:7};
const content:WindowContentInfo={label:'source.7',sourceIndex:2,text:'A window-owned source',
 colors:[0x345678,0xccaabb],stopWidths:[.25,2],background:0x101319,ink:0xdfd8cc,
 lightness:.62,chroma:.14,brightness:.28,hueOffset:18,lockLightness:true,feather:.8,
 textLightness:.83,textChroma:.1,waveform:[0,.5,-.5,1],visibility:.75,maximized:.4};
const info:WindowInfo={id:7,title:'',text:'',position:[0,0,0],visible:1,reader:false,scrollRow:0,
 width:1,height:1,alpha:1,material:0,group:0,shape:0,yaw:0,pitch:0,roll:0,minColumns:0,maxColumns:0,
 anchorX:0,anchorY:0,overshoot:0,scatter:0,bend:0,folds:0,meshColumns:0,meshRows:0,atUs:0,durationUs:0,
 texture:null,content,sourcePresentation:false,sourceOptions:null,effectiveOpacity:1,sourceOrder:0,
 readability:{padding:0,border:0,chromeSize:0,fadeStartRatio:0,fadeEndRatio:0}};

// @ts-expect-error every content command needs its window identity
const missingId:NativeCommand={op:'window-content',text:'missing identity'};
// @ts-expect-error colors are numeric RGB values
const stringColor:NativeCommand={op:'window-content',id:7,colors:['#345678']};
// @ts-expect-error stop widths are numeric weights
const stringWeight:WindowContentOptions={id:7,stopWidths:['wide']};
// @ts-expect-error content metadata is nullable, but when present it is complete
const incomplete:WindowContentInfo={label:'source.7',sourceIndex:2,text:'partial'};
// @ts-expect-error window content must be a complete record or null
const invalidContent:WindowInfo={...info,content:{label:'source.7'}};
// @ts-expect-error metadata visibility is numeric
const invalidVisibility:WindowContentInfo={...content,visibility:true};
// @ts-expect-error maximized progress is numeric
const invalidMaximized:WindowContentInfo={...content,maximized:false};

void [initial,patch,remove,content,info,missingId,stringColor,stringWeight,incomplete,invalidContent,
 invalidVisibility,invalidMaximized];
