import {createFontGallery,parseTdfCellArtImport} from '../../bindings/typescript/font_gallery.mjs';
import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const controller=createFontGallery();const font:string=controller.canvasFont(16);const command:NativeCommand=parseTdfCellArtImport({op:'cell-art'});void font;void command;
void controller.load(new Uint8Array([1,2]),'font.otf');
