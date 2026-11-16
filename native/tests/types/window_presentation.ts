import type {NativeCommand,WindowInfo,WindowOptions,WindowSourcePresentationOptions,WindowAction} from '../../bindings/typescript/contracts.js';

const enable:NativeCommand={op:'window',id:7,sourcePresentation:true};
const partial:NativeCommand={op:'window',id:7,depthFade:.04,chrome:'gnome',controlWidth:12,
 customSide:'left',customOrder:'close,minimize,maximize,background',customGlyphs:'×,−,□,◇'};
const clear:NativeCommand={op:'window',id:7,sourcePresentation:false};
const action:WindowAction='background';
const options:WindowOptions={id:7,sourcePresentation:true,alpha:.85};
const info:WindowInfo={id:7,title:'',text:'',position:[0,0,0],visible:1,reader:false,scrollRow:0,
 width:1,height:1,alpha:.85,material:0,group:0,shape:0,yaw:0,pitch:0,roll:0,minColumns:0,maxColumns:0,
 anchorX:0,anchorY:0,overshoot:0,scatter:0,bend:0,folds:0,meshColumns:0,meshRows:0,atUs:0,durationUs:0,
 texture:null,content:null,sourcePresentation:true,sourceOptions:null,effectiveOpacity:.85,sourceOrder:0,
 readability:{padding:0,border:0,chromeSize:0,fadeStartRatio:0,fadeEndRatio:0}};
const sourceOptions:WindowSourcePresentationOptions={opacity:.85,depthFade:.008,chrome:'mac',controlWidth:10,
 controlHeight:3,customSide:'right',customOrder:['minimize','maximize','background','close'],
 customGlyphs:[0x2212,0x25a1,0x25c7,0xd7]};

// @ts-expect-error opt-in is strictly Boolean
const badOptIn:NativeCommand={op:'window',id:7,sourcePresentation:1};
// @ts-expect-error chrome must be a supported source profile
const badChrome:NativeCommand={op:'window',id:7,chrome:'aqua'};
// @ts-expect-error custom order is carried as source CSV text
const badOrder:NativeCommand={op:'window',id:7,customOrder:['close','minimize','maximize','background']};
// @ts-expect-error action remains a closed union
const badAction:WindowAction='send-behind';
// @ts-expect-error metadata carries exactly four custom actions
const badSourceOrder:WindowSourcePresentationOptions={...sourceOptions,customOrder:['close','close','maximize']};

void [enable,partial,clear,action,options,info,sourceOptions,badOptIn,badChrome,badOrder,badAction,badSourceOrder];
