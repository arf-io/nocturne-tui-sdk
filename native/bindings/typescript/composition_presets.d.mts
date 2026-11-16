import type {CompositionProject} from './composition_project.mjs';
export type ProjectPresetId='signal-desk'|'flight-deck'|'tidal-console';
export interface ProjectPreset {readonly id:ProjectPresetId;readonly name:string;readonly create:()=>CompositionProject;}
export const PROJECT_PRESETS:readonly ProjectPreset[];
export function createPreset(id:ProjectPresetId):CompositionProject;
