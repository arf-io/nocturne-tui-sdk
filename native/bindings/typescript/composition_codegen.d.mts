import type {CompositionProject} from './composition_project.mjs';
export function generateProjectFiles(project:CompositionProject):Record<string,string|Uint8Array>;
export function projectCodeArchive(project:CompositionProject):Uint8Array;
