import type { NativeCommand, SourceStageComponentOptions, SourceStageComponentInfo } from '../../bindings/typescript/contracts.js';
import type { NativeMetadata } from '../../bindings/typescript/native_scene.mjs';

const complete: SourceStageComponentOptions = {
  id: 9,
  kind: 'pie',
  x: -12,
  y: 4,
  width: 40,
  height: 20,
  materialId: 2,
  legacyFlags: 37,
  fg: 0xe2d9c9,
  bg: 0x11100e,
  fgOpacity: 820,
  bgOpacity: 0,
  text: 'A中9',
  data: [300, 200, 500],
  changedMs: 1_700_000_000_123,
  colorAnimation: 1,
  hueStep: 17,
  hueSpeed: 24,
  hueSaturation: 620,
  hueBrightness: 830,
};

const author: NativeCommand = { op: 'source-stage-component', ...complete };
const remove: NativeCommand = { op: 'remove-source-stage-component', id: 9 };
const record: SourceStageComponentInfo = {
  id: 9,
  materialId: 2,
  kind: 'pie',
  legacyFlags: 37,
  node: [0, 37, -12, 4, 40, 20, 0, 0, 0, 0, 0, 0, 0xe2d9c9,
    0x11100e, 820, 0, 0, 0, 3, 0, 3, 17, 24, 0, 0, 0, 620, 830,
    1, 0, 1, 0],
  text: 'A中9',
  data: [300, 200, 500],
};
const metadata: NativeMetadata['sourceStageComponents'] = [record];
void [author, remove, metadata];

// @ts-expect-error source kinds are the recovered fourteen-kind registry.
const badKind: SourceStageComponentOptions = { id: 1, kind: 'unsupported', width: 1, height: 1 };
// @ts-expect-error identity and source kind are required for authoring.
const missingIdentity: SourceStageComponentOptions = { width: 1, height: 1 };
// @ts-expect-error dimensions are needed for every source primitive.
const missingDimensions: NativeCommand = { op: 'source-stage-component', id: 1, kind: 'box' };
// @ts-expect-error packed source node words are metadata, not writable options.
const nodeInjection: NativeCommand = { op: 'source-stage-component', id: 1, kind: 'box', width: 1, height: 1, node: record.node };
// @ts-expect-error material IDs are numeric retained references.
const badMaterial: NativeCommand = { op: 'source-stage-component', id: 1, kind: 'text', width: 1, height: 1, materialId: '2' };
// @ts-expect-error remove command carries only its stable SDK ID.
const malformedRemoval: NativeCommand = { op: 'remove-source-stage-component', id: 1, kind: 'box' };
void [badKind, missingIdentity, missingDimensions, nodeInjection, badMaterial, malformedRemoval];
