/** Original Workbench modal composition, with the native stack as authority.
 * Source: BlackHoleRenderer.modal and WorkbenchModel stack transitions.
 * Text capacity adaptation: retain complete source; send only visible glyphs to
 * the original bounded Stage viewport painter. No legacy engine runs here. */
const rgb=v=>typeof v==='number'?v:parseInt(v.replace(/^#/,''),16);
const softStep=n=>{n=Math.max(0,Math.min(1,n));return n*n*(3-2*n)};
export const SOURCE_MODAL_KINDS=Object.freeze(['center','fullscreen','drawer-left','drawer-right','drawer-top','drawer-bottom','corner','toast','error','confirmation','dropdown']);
function originalModal(view, m) {
        const entry = m.modalStack.peek();
        if (!entry)
            return;
        const w = view.frame.width, h = view.frame.height, isDrawer = entry.kind.startsWith('drawer'), width = entry.kind === 'fullscreen' ? w - 4 : isDrawer ? Math.min(62, Math.floor(w * .55)) : Math.min(76, w - 8), height = entry.kind === 'toast' ? 6 : entry.kind === 'dropdown' ? 12 : Math.min(28, h - 8);
        let x = Math.floor((w - width) / 2), y = Math.floor((h - height) / 2);
        if (entry.kind === 'drawer-right')
            x = w - width - 2;
        if (entry.kind === 'drawer-left')
            x = 2;
        if (entry.kind === 'drawer-top')
            y = 4;
        if (entry.kind === 'drawer-bottom')
            y = h - height - 5;
        if (entry.kind === 'corner') {
            x = w - width - 2;
            y = h - height - 5;
        }
        const progress = m.options.motion ? softStep((m.motionMs - entry.atMs) / 280) : 1;
        if (entry.kind === 'drawer-right')
            x += Math.round((1 - progress) * (width - 5));
        if (entry.kind === 'drawer-left')
            x -= Math.round((1 - progress) * (width - 5));
        if (entry.kind === 'drawer-top')
            y -= Math.round((1 - progress) * (height - 3));
        if (entry.kind === 'drawer-bottom')
            y += Math.round((1 - progress) * (height - 3));
        const ns = [{ kind: 'box', id: 49999, x, y, width, height, fg: this.ink(250), bg: 0x101721, bgOpacity: Math.round(m.bh.modalOpacity * 1000), fgOpacity: 1000, text: ' ' + entry.title + ' ', style: 0 }], sem = [], actions = {};
        const row = (id, yy, label, kind, value, extra) => { ns.push({ kind: 'item', id, x: x + 2, y: yy, width: width - 4, height: 1, text: label, fg: this.ink(180), bg: 0x223845, bgOpacity: 900, fgOpacity: 1000, state: sem.length === m.modalSelected ? 2 : 0 }); sem.push({ id, label }); actions[id] = { kind, value, extra }; };
        if (m.modalContext === 'node') {
            const n = m.richGraph.node(m.modalNode), hood = m.richGraph.neighborhood(n.id);
            let yy = y + 2;
            for (const [k, v] of Object.entries(n.metadata ?? {}).slice(0, 6)) {
                ns.push({ kind: 'text', x: x + 2, y: yy++, width: width - 4, height: 1, text: k + ': ' + v, fg: this.ink(250), fgOpacity: 900 });
            }
            yy++;
            for (const [group, ids] of Object.entries({ Parents: hood.parents, Children: hood.children, Siblings: hood.siblings })) {
                if (yy >= y + height - 4)
                    break;
                ns.push({ kind: 'text', x: x + 2, y: yy++, width: width - 4, height: 1, text: group.toUpperCase(), fg: this.ink(50), fgOpacity: 850 });
                for (const id of ids) {
                    if (yy >= y + height - 3)
                        break;
                    row(47000 + sem.length, yy++, '↳ ' + (m.richGraph.node(id).label ?? id), 'rich-node', id);
                }
            }
        }
        else if (m.modalContext === 'windows') {
            m.spaceWindows.list().filter(w => `${w.id} ${w.title}`.toLowerCase().includes(m.modalQuery.toLowerCase())).slice(0, height - 5).forEach((win, i) => row(47100 + i, y + 3 + i, `${win.state.padEnd(10)} ${win.title}`, 'focus-window', win.id, m.windowMode));
        }
        else if (m.modalContext === 'commands') {
            m.keymap.search(m.modalQuery).slice(0, height - 5).forEach((b, i) => row(47200 + i, y + 3 + i, `${b.chord.padEnd(17)} ${b.label ?? b.id}`, 'shortcut', b.id));
        }
        else {
            ns.push({ kind: 'text', x: x + 3, y: y + 3, width: width - 6, height: 4, text: entry.kind === 'confirmation' ? 'This specimen does not authorize an external action. Confirm applies only to the local demonstration.' : entry.body, fg: rgb(m.palette.ink), fgOpacity: 1000 });
            if (entry.kind === 'confirmation')
                row(47800, y + height - 4, '✓ Confirm local demonstration', 'confirm', 'local');
        }
        row(47999, y + height - 2, '× Close / Escape', 'dismiss', '');
        // Node composition only: the current native Stage paints this layer.
        view.nodes.push(...ns);
        view.semantics = sem;
        view.actions = actions;
    }
export function composeSourceModal({state,width,height,timeMs,motion=true,modalOpacity=.9,palette={ink:'#dfd8cc'},ink,graph,windows=[],commands=[],windowMode='tiled',modalNode}){
 const entry=state.entries.at(-1);if(!entry)return {nodes:[],semantics:[],actions:{}};
 const view={frame:{width,height},nodes:[],semantics:[],actions:{}};
 const m={modalStack:{peek:()=>entry},options:{motion},motionMs:timeMs,bh:{modalOpacity},palette,modalContext:state.context,modalQuery:state.query,modalSelected:state.selected,modalNode,richGraph:graph,spaceWindows:{list:()=>windows},keymap:{search:q=>commands.filter(b=>`${b.chord} ${b.label??b.id} ${b.id}`.toLowerCase().includes(q.toLowerCase()))},windowMode};
 originalModal.call({ink},view,m);return {nodes:view.nodes,semantics:view.semantics,actions:view.actions};
}
function visibleText(node){const chars=[...String(node.text??'')],limit=Math.max(0,node.width)*Math.max(0,node.height);return chars.slice(0,limit).join('');}
export class SourceModalController {
 constructor(scene,options={}){this.scene=scene;this.options=options;this.ids=[];this.view={nodes:[],semantics:[],actions:{}};}
 state(){return this.scene.infoComplete().sourceModal;}
 push(kind='center',context='commands',extra={}){const state=this.state(),timeMs=this.options.timeMs?.()??0;this.scene.command({op:'source-modal',action:'push',context,workspace:this.options.workspace?.()??'',entry:{id:'modal-'+state.revision,kind,title:context==='windows'?'WINDOW SWITCHER':context==='commands'?'COMMANDS & SHORTCUTS':'INTERFACE / '+kind.toUpperCase(),body:'Every action also has a visible control. Escape dismisses one layer.',atMs:timeMs,dismissible:true,...extra}});return this.compose();}
 edit(patch){this.scene.command({op:'source-modal',action:'edit',...patch});return this.compose();}
 dismiss(){this.scene.command({op:'source-modal',action:'dismiss'});return this.compose();}
 clear(){this.scene.command({op:'source-modal',action:'clear'});return this.compose();}
 /* The state compose() last read, while no command has followed it; otherwise a fresh read. */
 current(){return this.lastState??this.state();}
 compose(){const info=this.scene.infoComplete(),state=info.sourceModal;this.lastState=null;
  /* Nothing open and nothing to remove: the composition is empty and sends no command, so skip the option
     callbacks (each a whole-state read in the Gallery) and keep the state for current(). */
  if(!state.entries.length&&!state.componentIds.length){this.ids=[];this.view={nodes:[],semantics:[],actions:{}};this.lastState=state;return this.view;}
  const o=this.options,options=typeof o.source==='function'?o.source():o.source??{},timeMs=o.timeMs?.()??0;
  const l=Math.round((options.textLightness??.83)*1000),chroma=Math.round((options.textChroma??.1)*10000),ink=h=>this.scene.sourceStageOklch(l,chroma,((Math.round(h)%360)+360)%360*1000);
  const view=composeSourceModal({state,width:this.scene.exports.nrWidth(this.scene.context),height:this.scene.exports.nrHeight(this.scene.context),timeMs,motion:options.motion??true,modalOpacity:options.modalOpacity??.9,palette:options.palette??{ink:'#dfd8cc'},ink,graph:o.graph?.(),windows:o.windows?.()??[],commands:o.commands?.()??[],windowMode:o.windowMode?.()??'tiled',modalNode:o.modalNode?.()});
  const commands=[],current=new Set(info.sourceStageComponents.map(n=>n.id));for(const id of state.componentIds)if(current.has(id)){commands.push({op:'remove-source-stage-component',id});current.delete(id);}
  let next=60000;const ids=[];for(const node of view.nodes){while(current.has(next)){next++;if(next>65535)next=1;}const {id:legacyFlags=0,...shape}=node;if(shape.width<=0||shape.height<=0)continue;const id=next++;current.add(id);ids.push(id);commands.push({op:'source-stage-component',id,legacyFlags,...shape,text:visibleText(shape)});}
  if(ids.length)commands.push({op:'source-modal',action:'associate',componentIds:ids,boxId:ids[0]});
  if(commands.length)this.scene.command({op:'batch',commands});else this.lastState=state;this.ids=ids;this.view=view;return view;
 }
 hit(x,y){const hit=this.scene.sourceStageHit(x,y);return hit&&this.view.actions[hit.id]?{...hit,action:this.view.actions[hit.id]}:null;}
 activate(x,y){const hit=this.hit(x,y);if(!hit)return false;if(hit.action.kind==='dismiss')this.dismiss();else this.options.onAction?.(hit.action);return true;}
 key(key){const info=this.scene.infoComplete();if(info.modal)return false;const state=info.sourceModal;if(!state.depth)return false;if(key==='F1')return false;if(key==='Escape'){this.dismiss();return true;}if(key==='ArrowDown'||key==='ArrowUp'){const count=this.view.semantics.length;this.edit({selected:(state.selected+(key==='ArrowDown'?1:-1)+count)%Math.max(1,count)});return true;}if(key==='Backspace'){this.edit({query:[...state.query].slice(0,-1).join(''),selected:0});return true;}if(key==='Enter'){const item=this.view.semantics[state.selected],action=item&&this.view.actions[item.id];if(action?.kind==='dismiss')this.dismiss();else if(action)this.options.onAction?.(action);return true;}if([...key].length===1){this.edit({query:state.query+key,selected:0});return true;}return state.blocking;}
}
