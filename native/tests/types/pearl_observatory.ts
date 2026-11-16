import {NativeScene} from '../../bindings/typescript/native_scene.mjs';
import {PearlObservatorySession} from '../../bindings/typescript/pearl_observatory_stage.mjs';
import {PearlObservatoryOriginal} from '../../bindings/typescript/pearl_observatory_original.mjs';
declare const scene:NativeScene;
const session=new PearlObservatorySession(scene,{scene:'scope'});session.action({op:'configure',patch:{weatherStyle:'nova',motion:false}});session.action({op:'input',text:'文👩‍💻'});session.model.ingest({source:'explicit',value:.5,atMs:0,seq:1});session.restoreCheckpoint(session.checkpoint());const model=new PearlObservatoryOriginal.ObservatoryModel();model.setScene('nano');
// @ts-expect-error original scene identity is explicit
new PearlObservatorySession(scene,{scene:'invented'});
// @ts-expect-error authored weather alternatives are explicit
session.action({op:'configure',patch:{weatherStyle:'invented'}});
// @ts-expect-error a document input is text
session.action({op:'input',text:123});

import {createObservatoryAudio} from '../../bindings/typescript/pearl_observatory_audio.mjs';
declare const stream:MediaStream;const audio=createObservatoryAudio({session:()=>session,running:()=>true});audio.attach(stream,{quality:'synthetic',label:'actual synthetic input'});audio.start('microphone');audio.stop();
// @ts-expect-error capture modes are explicit
audio.start('automatic');
// @ts-expect-error a supplied source is a MediaStream
audio.attach('not a stream');
