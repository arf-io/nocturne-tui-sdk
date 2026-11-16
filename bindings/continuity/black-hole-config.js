import {KINETIC_SCENES,exportKineticConfiguration,applyKineticConfiguration} from './kinetic-model.js';
import {WORLD_WEATHER} from './black-hole-space.js';
import {Keymap} from './black-hole-keys.js';
import {GraphIndex} from './black-hole-graph.js';
import {BLACK_HOLE_SCENES,validateBlackHoleOptions,BlackHoleModel} from './black-hole-model.js';
/** Visual recipes only. No capture permissions, secrets, transcripts, or live
 * transport state are exported. Import validates an isolated candidate first. */
export function exportBlackHoleConfiguration(model) {
    const base = exportKineticConfiguration(model);
    return JSON.parse(JSON.stringify({ ...base, version: 7, blackHole: { options: model.bh, autoNovas: model.autoNovas, weather: model.selectedWeather, weatherSpace: model.weatherSpace, coordinated: model.coordinated, graph: { nodes: model.richGraph.nodes, edges: model.richGraph.edges }, colorField: model.graphColorField, groups: model.worldGroups, windowMode: model.windowMode, keys: model.keymap.bindings, visualRoutes: model.visualRoutes, form: model.form.values() } }));
}
/** Apply a bounded visual recipe atomically; retained drafts, observations and
 * messages survive. Motion restarts at zero. The host should seek its clock to 0.
 * Throws before mutation for invalid options, keys, graph, groups or form values. */
export function applyBlackHoleConfiguration(model, input) {
    if (!input || typeof input !== 'object' || Array.isArray(input))
        throw Error('Recipe object required');
    const raw = JSON.stringify(input);
    if (raw.length > 1048576)
        throw Error('Recipe exceeds 1 MiB');
    const c = JSON.parse(raw);
    if (![4, 5, 7].includes(c.version))
        throw Error('Unsupported recipe version');
    const target = c.scene ?? model.scene;
    if (!BLACK_HOLE_SCENES.some(s => s.id === target))
        throw Error('Unknown scene');
    const candidate = new BlackHoleModel();
    const safe = { ...c, version: c.version === 7 ? 5 : c.version, scene: KINETIC_SCENES.some(s => s.id === target) ? target : 'warp' };
    delete safe.blackHole;
    applyKineticConfiguration(candidate, safe);
    const camera = candidate.camera.snapshot(), cameraTarget = { ...candidate.camera.target };
    if (c.version === 7) {
        const b = c.blackHole;
        if (!b || typeof b !== 'object')
            throw Error('Missing Black Hole configuration');
        candidate.bh = validateBlackHoleOptions(b.options);
        if (typeof b.autoNovas !== 'boolean' || typeof b.coordinated !== 'boolean' || !WORLD_WEATHER.includes(b.weather) || !['visit', 'summon'].includes(b.windowMode))
            throw Error('Invalid policy');
        candidate.autoNovas = b.autoNovas;
        candidate.coordinated = b.coordinated;
        candidate.selectedWeather = b.weather;
        if (!['world', 'screen'].includes(b.weatherSpace ?? 'world'))
            throw Error('Weather space');
        candidate.weatherSpace = b.weatherSpace ?? 'world';
        candidate.windowMode = b.windowMode;
        candidate.richGraph = new GraphIndex(b.graph);
        candidate.keymap = new Keymap(b.keys, 'browser', true);
        if (typeof b.colorField !== 'string' || b.colorField.length > 64)
            throw Error('Color field');
        candidate.graphColorField = b.colorField;
        if (!Array.isArray(b.visualRoutes) || b.visualRoutes.length > 16)
            throw Error('Visual routes');
        for (const r of b.visualRoutes)
            candidate.bindVisual(r);
        if (!b.groups || typeof b.groups !== 'object' || Array.isArray(b.groups) || Object.keys(b.groups).length > 32)
            throw Error('Group map');
        for (const [name, ids] of Object.entries(b.groups)) {
            if (!Array.isArray(ids))
                throw Error('Group IDs');
            candidate.groupWindows(name, ids);
        }
        for (const [id, v] of Object.entries(b.form ?? {}))
            candidate.form.set(id, v);
    }
    candidate.setScene(target);
    candidate.camera.configure(camera);
    candidate.camera.target = cameraTarget;
    candidate.flight.anchor(camera);
    candidate.surfaceDistance.set(0, candidate.bh.landscapeSpeed * .44704);
    candidate.waterfallPhase.set(0, candidate.bh.waterFlow);
    candidate.worldEvents = [];
    candidate.setTime(0);
    candidate.graph = candidate.richGraph.graph;
    if (['graph-explorer', 'git-history'].includes(target)) {
        candidate.startLayout(candidate.graph, candidate.layoutOptions);
        candidate.layoutFitOnCommit = false;
    }
    // Commit visual state only; source data, text drafts, sensors and permissions stay owned by the host.
    for (const k of ['options', 'palette', 'camera', 'spaceWindows', 'particles', 'textOptions', 'textActor', 'hideEffect', 'textSource', 'travel', 'orbit', 'orbit2', 'warpTravel', 'vectorTravel', 'surfaceDistance', 'waterfallPhase', 'scene', 'bh', 'flight', 'richGraph', 'graph', 'layoutOptions', 'layout', 'layoutJob', 'layoutFitOnCommit', 'keymap', 'autoNovas', 'coordinated', 'selectedWeather', 'weatherSpace', 'windowMode', 'worldGroups', 'visualRoutes', 'graphColorField', 'form'])
        model[k] = candidate[k];
    for (const b of [...model.bus.bindings])
        model.bus.unbind(b.target);
    for (const b of candidate.bus.bindings)
        model.bus.bind(b);
    model.worldEvents = [];
    model.modalStack.clear();
    model.setTime(0);
    model.revision++;
    model.notice = 'v0.7 visual recipe applied / motion reset; local data retained';
}

