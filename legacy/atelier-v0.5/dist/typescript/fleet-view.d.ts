/** Shared cell scene composition for the browser and terminal Fleet hosts.
 * No drawing APIs here: every primitive is rendered by the common C/WASM kernel.
 */
import type { FleetController, FleetScene } from './fleet.js';
/** Compose a bounded, replayable FleetScene. Input state is never mutated. */
export declare function composeFleet(c: FleetController): FleetScene;
