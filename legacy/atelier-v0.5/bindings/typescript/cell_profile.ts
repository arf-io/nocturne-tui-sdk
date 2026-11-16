/** Pinned single-cell display profile. Stored text is never rewritten. Wide
 * glyphs, combining sequences and terminal control characters display as '?'.
 * Host terminals still control ambiguous-width font rendering. No emoji/IME
 * or general grapheme-width promise is made by this compact material SDK. */
export function safeCellCodepoint(cp:number):number{
 if(!Number.isInteger(cp))return 0x3f;
 if(cp>=0x20&&cp<=0x7e||cp>=0xa1&&cp<=0x2ff&&cp!==0xad||cp>=0x370&&cp<=0x3ff||cp>=0x2010&&cp<=0x2027||cp>=0x2190&&cp<=0x22ff||cp>=0x2500&&cp<=0x25fc||cp>=0x2800&&cp<=0x28ff||[0x2302,0x2310,0x2605,0x2606,0x2610,0x2611,0x2726,0x2727,0x2736,0x2739].includes(cp))return cp;
 return 0x3f;
}
/** Reject glyphs not admitted by the single-cell profile. */
export function requireCellGlyph(glyph:unknown):string{if(typeof glyph!=='string'||[...glyph].length!==1||safeCellCodepoint(glyph.codePointAt(0)!)!==glyph.codePointAt(0))throw new RangeError('Expected one supported single-cell glyph');return glyph;}
