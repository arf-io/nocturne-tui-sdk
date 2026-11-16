import {WorkbenchModel} from './workbench.js';
import {exportRestorationConfiguration,applyRestorationConfiguration} from './restoration-config.js';
import {validatePrompt,PROMPT_MODES} from './prompt.js';
import {validateDecoration,validateChangeStyle} from './styles.js';
/** Visual recipe only. Draft recovery uses PromptDocument.snapshot separately,
 * so importing a palette/view recipe never overwrites the current document. */
export function exportWorkbenchConfiguration(model){return {...exportRestorationConfiguration(model),workbench:{version:1,prompt:{mode:model.document.mode,normalMode:model.document.normalMode,minimizedMode:model.document.minimizedMode,options:{...model.document.options}},decoration:{...model.decoration},showDecoration:model.showDecoration,changeStyle:structuredClone(model.changeTrack.style),showChangeTrack:model.showChangeTrack}};}
/** Validate both inherited visual configuration and every current extension on
 * an isolated model before touching the live one. A v1 recipe preserves current
 * draft, caret and undo; explicitly restored snapshots have separate consent. */
export function applyWorkbenchConfiguration(model,input){
 const trial=new WorkbenchModel();trial.document.restore(model.document.snapshot());trial.draft=trial.document.text;trial.draftCaret=trial.document.caret;
 applyRestorationConfiguration(trial,input);let current=null;
 if(input?.workbench){const w=input.workbench;if(w.version!==1||Object.keys(w).some(k=>!['version','prompt','decoration','showDecoration','changeStyle','showChangeTrack'].includes(k)))throw RangeError('Workbench recipe version/fields');
  const p=w.prompt;if(!p||!PROMPT_MODES.includes(p.mode)||!['marquee','grow'].includes(p.normalMode)||![null,'vim-inline','vim-full'].includes(p.minimizedMode))throw RangeError('Prompt view recipe');
  const options=validatePrompt(p.options);if([...model.document.text].length>options.maxChars)throw RangeError('Recipe maxChars would truncate current draft');
  if(typeof w.showDecoration!=='boolean'||typeof w.showChangeTrack!=='boolean')throw RangeError('Boolean recipe flags');
  current={...w,prompt:{...p,options},decoration:validateDecoration(w.decoration),changeStyle:validateChangeStyle(w.changeStyle)};
 }
 applyRestorationConfiguration(model,input);
 if(current){model.configurePrompt(current.prompt.options);model.promptMode(current.prompt.mode);model.document.normalMode=current.prompt.normalMode;model.document.minimizedMode=current.prompt.minimizedMode;model.decoration=current.decoration;model.showDecoration=current.showDecoration;model.changeTrack.configure(current.changeStyle);model.showChangeTrack=current.showChangeTrack;}
 model.draft=model.document.text;model.draftCaret=model.document.caret;return model;
}
