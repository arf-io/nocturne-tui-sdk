/** Versioned visual settings, not transcript/session restore. Loading validates
 * into an independent model first. A host swaps the returned model atomically.
 * No local draft, provider record, filesystem path or credential is exported. */
import { AtelierModel } from './atelier.js';
/** Return owned JSON-safe settings. Window motions are normalized to intent,
 * so reopening settings starts at settled visibility rather than an old clock.
 * Example: JSON.stringify(exportAtelierSettings(model), null, 2). */
export declare function exportAtelierSettings(m: AtelierModel): Record<string, unknown>;
/** Validate all settings and create an owned model at time zero. Throws on
 * invalid versions/ranges/IDs/masks; caller state is untouched on failure.
 * Layout is solved with fixed iterations. For large force imports, call this
 * in a worker or use GraphLayoutJob in the host. Bounded to 256 graph nodes. */
export declare function loadAtelierSettings(value: unknown): AtelierModel;
