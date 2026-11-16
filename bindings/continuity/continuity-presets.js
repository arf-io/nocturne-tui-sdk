import {EFFECT_CATALOG} from './effect-catalog.js';
export const CONTINUITY_PRESETS = [
    { id: 'oblique', name: 'Oblique Hyperlane / continuous flight' },
    { id: 'banked', name: 'Flight / coordinated left turn' },
    { id: 'flat', name: 'Flight / flat right turn' },
    { id: 'climb-dive', name: 'Flight / climb, roll, dive' },
    { id: 'orbit', name: 'Stable orbit / anchored nova' },
    { id: 'escape-orbit', name: 'Escape spiral / anchored matter' },
    { id: 'falling-orbit', name: 'Inward orbit / anchored matter' },
    { id: 'typographic-rain', name: 'Typography / rain in, ash out' },
    { id: 'fleet-weather', name: 'Fleet / prompt bands + per-character rain' },
    { id: 'graph-family', name: 'Graph / eased family inspection' },
    { id: 'moonlight', name: 'Tidal Glass / long cross-swell' },
    { id: 'winter-swell', name: 'Tidal Glass / steep wind chop' },
    { id: 'waterfall', name: 'Pearl Cascade / connected river' },
    ...EFFECT_CATALOG.map(e => ({ id: 'effect:' + e.id, name: e.label }))
];
/** All paths use the same model, clock and seed machinery as user actions. */
export function applyContinuityPreset(m, id) {
    if (typeof id !== "string" || !CONTINUITY_PRESETS.some(p => p.id === id)) throw new RangeError("Unknown Continuity preset");
    m.configure({ motion: true });
    m.effectShelf.clear();
    m.events = [];
    m.worldEvents = [];
    if (id.startsWith('effect:')) {
        const effect = id.slice(7);
        m.setScene('world-weather');
        m.flight.anchor(m.camera.snapshot());
        m.selectedEffect = effect;
        m.playEffect(effect, 'world', m.width * .5, m.height * .62);
        return;
    }
    if (id === 'oblique') {
        m.launchHyperlane();
        return;
    }
    if (['banked', 'flat', 'climb-dive'].includes(id)) {
        m.launchHyperlane();
        m.flight.plan(m.motionMs, m.camera.snapshot(), id === 'climb-dive' ? [{ kind: 'climb', seconds: 9, degrees: 22, speed: 9 }, { kind: 'roll', seconds: 6, degrees: 60, speed: 9 }, { kind: 'dive', seconds: 12, degrees: 35, speed: 9 }] : [{ kind: 'turn', seconds: 18, degrees: id === 'banked' ? -90 : 90, speed: 9, coordinated: id === 'banked', bank: 32 }]);
        return;
    }
    if (['orbit', 'escape-orbit', 'falling-orbit'].includes(id)) {
        m.setScene('world-weather');
        m.camera.configure({ x: 0, y: 2, z: -48, yaw: 0, pitch: 0, roll: 0 });
        m.flight.orbit(m.motionMs, m.camera.snapshot(), { x: 0, y: 0, z: 0 }, { mode: id === 'orbit' ? 'stable' : id === 'escape-orbit' ? 'escape' : 'falling', periodSeconds: 24, radialRate: 1.2, bank: 12 });
        m.playEffect('world.nova', 'world');
        return;
    }
    if (id === 'typographic-rain') {
        m.setScene('text');
        m.atelierTextEnabled = false;
        m.textOptions = { ...m.textOptions, effect: 'rain' };
        m.hideEffect = 'ash';
        m.hardReplayText();
        return;
    }
    if (id === 'fleet-weather') {
        m.setScene('fleet-room');
        m.configure({ backgroundStyle: 'warp' });
        m.inputWeather.enabled = true;
        m.playEffect('thermal.embers', 'world', m.width * .85, m.height * .7);
        return;
    }
    if (id === 'graph-family') {
        m.setScene('graph-explorer');
        while (m.layoutJob)
            m.stepLayout(128);
        m.selectGraph(m.richGraph.nodes[Math.min(3, m.richGraph.nodes.length - 1)].id);
        return;
    }
    if (id === 'moonlight' || id === 'winter-swell') {
        m.setScene('ocean');
        Object.assign(m.worldDetail, id === 'moonlight' ? { waveHeight: 1.8, wavelength: 42, windAngle: 18, crossSwell: .66, choppiness: .35, foam: .4, waveSpeed: .7 } : { waveHeight: 3.1, wavelength: 19, windAngle: 42, crossSwell: .82, choppiness: .8, foam: .9, waveSpeed: 1.25 });
        return;
    }
    if (id === 'waterfall') {
        m.setScene('waterfall');
        return;
    }
    throw new RangeError('Unknown continuity preset');
}

