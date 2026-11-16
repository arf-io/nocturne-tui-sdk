import {createProject,placeComponent,prepareProject,ProjectHistory} from '../../bindings/typescript/composition_project.mjs';
import {generateProjectFiles} from '../../bindings/typescript/composition_codegen.mjs';
import type {NativeScene} from '../../bindings/typescript/native_scene.mjs';
const project=createProject({seed:4,width:120,height:40});project.elements.push(placeComponent('button',1));project.elements[0].events.activate.push({op:'draft',text:'Hello',emitWeather:false});
declare const scene:NativeScene;const prepared=prepareProject(scene,project);new ProjectHistory(project,prepared.snapshot).undo();const files:Record<string,string|Uint8Array>=generateProjectFiles(project);void files;
// @ts-expect-error a catalogue component requires an implemented adapter
placeComponent('imaginary',1);
// @ts-expect-error source is a string
project.prompt.text=22;
// @ts-expect-error identities are numeric
project.elements[0].id='1';
import {projectFromCommands} from '../../bindings/typescript/composition_project.mjs';
import {bindCompositionEditor} from '../../bindings/typescript/composition_editor.mjs';
const base=projectFromCommands([{op:'camera',position:[0,0,85]}],{seed:12,timeUs:700000});
void base;
void bindCompositionEditor;

import type {CompositionEditor} from '../../bindings/typescript/composition_editor.mjs';
declare const editor:CompositionEditor;editor.replaceCommands([{op:'draft',text:'Ready'}],{timeline:[{timeUs:700000,command:{op:'draft',text:'Later'}}]});

import {PROJECT_PRESETS,createPreset} from '../../bindings/typescript/composition_presets.mjs';
const selectedProject=createPreset(PROJECT_PRESETS[0].id);prepareProject(scene,selectedProject);
// @ts-expect-error project identities are strings
createPreset(10);
