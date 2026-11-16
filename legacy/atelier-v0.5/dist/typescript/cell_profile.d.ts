/** Pinned single-cell display profile. Stored text is never rewritten. Wide
 * glyphs, combining sequences and terminal control characters display as '?'.
 * Host terminals still control ambiguous-width font rendering. No emoji/IME
 * or general grapheme-width promise is made by this compact material SDK. */
export declare function safeCellCodepoint(cp: number): number;
/** Reject glyphs not admitted by the single-cell profile. */
export declare function requireCellGlyph(glyph: unknown): string;
