/** Pure composition policy between terminal-emulator cells and material cells.
 * No escape parsing, subprocesses, device access, or optimistic keyboard echo.
 * Semantic foreground/background choices belong to the child by default.
 */
const ANSI16=[0x000000,0xcd0000,0x00cd00,0xcdcd00,0x0000ee,0xcd00cd,0x00cdcd,0xe5e5e5,0x7f7f7f,0xff0000,0x00ff00,0xffff00,0x5c5cff,0xff00ff,0x00ffff,0xffffff];
export function ansiColor(index){if(!Number.isInteger(index)||index<0||index>255)return 0;if(index<16)return ANSI16[index];if(index>=232){const n=8+(index-232)*10;return(n<<16)|(n<<8)|n;}const k=index-16,v=[0,95,135,175,215,255];return(v[Math.floor(k/36)]<<16)|(v[Math.floor(k/6)%6]<<8)|v[k%6];}
export function flattenColor(frame,index){const g=frame.cells[index],a=frame.cells[index+1],b=frame.cells[index+2];if(![0x2580,0x2584,0x258c,0x2590].includes(g))return b;return(Math.round(((a>>>16)+(b>>>16))/2)<<16)|(Math.round((((a>>>8)&255)+((b>>>8)&255))/2)<<8)|Math.round(((a&255)+(b&255))/2);}
/** Resolve one authoritative emulator cell. Colors in default mode may inherit
 * the material plane; explicit colors, inverse selections, and hidden text do
 * not. Wide/combined characters remain strings plus emulator-supplied widths.
 */
export function skinCell(cell,surface,index,{ink=0xdcd9d0,background=0x101319,recolorDefault=false,hueColor=ink}={}){
 const chars=(cell?.getChars()||' ').replace(/[\x00-\x1f\x7f-\x9f]/g,''),width=cell?.getWidth()??1,inv=!!cell?.isInverse(),hidden=!!cell?.isInvisible(),defaultFg=!cell||cell.isFgDefault(),defaultBg=!cell||cell.isBgDefault();
 let fg=defaultFg?ink:cell.isFgRGB()?cell.getFgColor():ansiColor(cell.getFgColor()),bg=defaultBg?background:cell.isBgRGB()?cell.getBgColor():ansiColor(cell.getBgColor());
 const theme=defaultBg&&!inv&&!hidden,plainSpace=chars===' '&&width===1&&!cell?.isUnderline?.()&&!cell?.isStrikethrough?.()&&!cell?.isOverline?.();
 if(theme){bg=flattenColor(surface,index);if(plainSpace){return {chars:String.fromCodePoint(surface.cells[index]||32),width,fg:surface.cells[index+1],bg:surface.cells[index+2],attrs:''};}if(defaultFg&&recolorDefault)fg=hueColor;}
 const attrs=[];if(cell){for(const [method,sgr]of [['isBold',1],['isDim',2],['isItalic',3],['isUnderline',4],['isBlink',5],['isInverse',7],['isInvisible',8],['isStrikethrough',9],['isOverline',53]])if(cell[method]?.())attrs.push(sgr);}
 return {chars:chars||' ',width,fg,bg,attrs:attrs.join(';')};
}
export function rowAnsi(cells){let out='',style='';for(const c of cells){if(c.width===0)continue;const next=`0;${c.attrs?c.attrs+';':''}38;2;${c.fg>>>16};${c.fg>>>8&255};${c.fg&255};48;2;${c.bg>>>16};${c.bg>>>8&255};${c.bg&255}`;if(next!==style){out+='\x1b['+next+'m';style=next;}out+=c.chars;}return out;}
