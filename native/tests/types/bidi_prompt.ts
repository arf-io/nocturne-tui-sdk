import type {NativeCommand} from '../../bindings/typescript/contracts.js';
import type {NativeScene} from '../../bindings/typescript/native_scene.mjs';
declare const scene:NativeScene;
const command:NativeCommand={op:'prompt',layout:'bidi',direction:'rtl'};
const rows:number[][]=scene.promptVisualLayout();
// @ts-expect-error invalid direction
const bad:NativeCommand={op:'prompt',layout:'bidi',direction:'up'};
void [command,rows,bad];

const documentRows:number[][]=scene.documentLayout('אב',8);
const documentBoundaries:number[]=scene.documentBoundaries('a\u202a\u202cb');
const documentHit:number=scene.documentHit('אב',8,0,0);
const documentCaret:number[]=scene.documentCaret('אב',8,1);
const originalApplication:NativeCommand={op:'window-application',scene:'windows',particles:{count:4}};
const originalShapes:NativeCommand={op:'window-application',scene:'shapes',backgroundStyle:'woven',sampling:'vertical'};
const atelierApplication:NativeCommand={op:'window-application',scene:'atelier-windows',atelierParticles:{lifeMs:3000},weatherStyle:'nova'};
// @ts-expect-error source text must be a string
scene.documentLayout(42,8);
// @ts-expect-error affinity is a number
scene.documentCaret('אב',8,1,'next');
// @ts-expect-error invalid original application scene
const badApplication:NativeCommand={op:'window-application',scene:'invented'};
void [documentRows,documentBoundaries,documentHit,documentCaret,originalApplication,originalShapes,atelierApplication,badApplication];
