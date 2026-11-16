/** Paint the native eight-dot mask without system-font substitution. */
export function paintBraille(ctx, glyph, x, y, width, height) {
 if (!Number.isInteger(glyph) || glyph < 0x2800 || glyph > 0x28ff) return false;
 const mask = glyph - 0x2800;
 const dots = [[.2,.1],[.2,.3],[.2,.55],[.7,.1],[.7,.3],[.7,.55],[.2,.8],[.7,.8]];
 for (let bit = 0; bit < 8; bit++) {
  if (mask & (1 << bit)) {
   const [column, row] = dots[bit];
   ctx.fillRect(x + column * width, y + row * height, width * .2, height * .1);
  }
 }
 return true;
}

/** Paint canonical full and half blocks as cell geometry. */
export function paintBlock(ctx, glyph, x, y, width, height) {
 switch (glyph) {
  case 0x2588: ctx.fillRect(x, y, width, height); return true;
  case 0x2580: ctx.fillRect(x, y, width, height / 2); return true;
  case 0x2584: ctx.fillRect(x, y + height / 2, width, height / 2); return true;
  case 0x258c: ctx.fillRect(x, y, width / 2, height); return true;
  case 0x2590: ctx.fillRect(x + width / 2, y, width / 2, height); return true;
  default: return false;
 }
}
