import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const commands:NativeCommand[]=[
 {op:'prompt-appearance',cursor:{shape:'custom',glyph:'◆',blinkMs:600,duty:0.5,color:'#a3cabe',secondaryColor:'#c7aed7',colorMode:'pulse',colorPeriodMs:2000}},
 {op:'prompt-appearance',weather:{style:'snow',intensity:0.6,lifeMs:1800,speed:12,paste:'off'}},
 {op:'prompt-appearance',cursor:{shape:'inherit'}}
];void commands;
// @ts-expect-error camera actions are not cursor shapes
const badShape:NativeCommand={op:'prompt-appearance',cursor:{shape:'orbit'}};
// @ts-expect-error unsupported typing weather
const badWeather:NativeCommand={op:'prompt-appearance',weather:{style:'hurricane'}};
// @ts-expect-error color must be a string
const badColor:NativeCommand={op:'prompt-appearance',cursor:{color:123}};
void badShape;void badWeather;void badColor;
