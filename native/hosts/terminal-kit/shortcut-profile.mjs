/** Terminal Kit capability map; caller reservations, never OS availability probes. */
const functionKey=0x110000;
const actions=[[1,'Quit',['CTRL_Q','ALT_Q']],[2,'Hold',['CTRL_P','ALT_P']],[3,'Help',['F1','F7']],[4,'Reader',['F6','F8']]];
export function normalizedShortcut(name){
 let match=/^F([1-9]|1[0-2])$/.exec(name);if(match)return [functionKey+Number(match[1]),0];
 match=/^(CTRL|ALT)_([A-Z])$/.exec(name);if(match)return [match[2].toLowerCase().codePointAt(0),match[1]==='CTRL'?2:4];
 throw RangeError('Unknown managed Terminal Kit chord: '+name);
}
export function negotiateHostShortcuts(scene,reserved=[]){
 if(!Array.isArray(reserved))throw TypeError('Shortcut reservation array required');
 const names=[...new Set(actions.flatMap(a=>a[2]))];if(reserved.some(name=>!names.includes(name)))throw RangeError('Reservation is outside managed shortcuts');
 const host=names.map(name=>[...normalizedShortcut(name),Number(reserved.includes(name))]);
 const candidates=actions.flatMap(([id,,preferences])=>preferences.map(name=>[id,...normalizedShortcut(name)]));
 const rows=scene.negotiateShortcuts(actions.map(a=>a[0]),candidates,host),bindings=new Map();
 const hints=rows.map(([id,key,mod,assigned])=>{
  const name=assigned?names.find(n=>{const [k,m]=normalizedShortcut(n);return key===k&&mod===m}):null;
  if(name)bindings.set(name,id);return actions.find(a=>a[0]===id)[1]+': '+(name??'unassigned');
 }).join(' | ');
 return {rows,bindings,hints,managed:new Set(names)};
}
