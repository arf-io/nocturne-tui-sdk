import type {NativeCommand,WidgetInfo} from '../../bindings/typescript/contracts.js';
const commands:NativeCommand[]=[
 {op:'widget',id:1,kind:'donut',value:1e-7,min:-1e-7,max:.987654321,alpha:.123456789,data:[.1,.3,1e-7,-0.0],cellAspect:2.123456789,innerRadius:.234567891,startAngle:.987654321,sweepAngle:270.123456789},
 {op:'define',path:'/v',value:1e-7,binding:{family:'widget',id:1,field:'value'}},
 {op:'set',path:'/v',expression:{multiply:[0,-1]}}
];
declare const widget:WidgetInfo;
const value:number=widget.value;
void commands;void value;
