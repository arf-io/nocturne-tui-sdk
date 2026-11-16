import {atelierTextOptions,AtelierTextPlayer} from './atelier-text.js';
import {EFFECT_CATALOG} from './effect-catalog.js';
import {exportBlackHoleConfiguration,applyBlackHoleConfiguration} from './black-hole-config.js';
import {WORLD_FIELDS} from './world-fields.js';
import {WORLD_DETAIL_FIELDS} from './world-detail-fields.js';
/** Additive v0.8 recipe. All extra data validates before the original atomic import. */
export function exportRestorationConfiguration(m) { return { ...exportBlackHoleConfiguration(m), restoration: { version: 9, worldDetail: { ...m.worldDetail }, inputWeather: { ...m.inputWeather }, graphTransitMs: m.graphTransitMs, selectedEffect: m.selectedEffect, effectSpace: m.effectSpace, scenicMode: m.scenicMode, worldView: { ...m.worldView }, hashLength: m.hashLength, typeColors: { ...m.graphTypeColors }, atelierText: { enabled: m.atelierTextEnabled, options: m.atelierPlayer.options } } }; }
export function applyRestorationConfiguration(m, input) {
    let extras = null;
    if (input?.restoration) {
        const r = input.restoration;
        if (![8, 9].includes(r.version) || !['world', 'classic'].includes(r.scenicMode) || !Number.isInteger(r.hashLength) || r.hashLength < 6 || r.hashLength > 64)
            throw new RangeError('Invalid restoration options');
        const world = { ...m.worldView };
        if (!r.worldView || typeof r.worldView !== 'object')
            throw new RangeError('worldView required');
        for (const [k, v] of Object.entries(r.worldView)) {
            const f = WORLD_FIELDS.find(f => f.name === k);
            if (!(k in world) || !f || typeof v !== 'number' || !Number.isFinite(v) || v < f.min || v > f.max || (f.scale === 1 && !Number.isInteger(v)))
                throw new RangeError('Invalid worldView ' + k);
            world[k] = v;
        }
        const colors = {};
        if (!r.typeColors || typeof r.typeColors !== 'object' || Array.isArray(r.typeColors) || Object.keys(r.typeColors).length > 64)
            throw new RangeError('Invalid typeColors');
        for (const [k, v] of Object.entries(r.typeColors)) {
            if (!/^[\w .-]{1,64}$/.test(k) || ['__proto__', 'constructor', 'prototype'].includes(k) || typeof v !== 'number' || !Number.isInteger(v) || v < 0 || v > 0xffffff)
                throw new RangeError('Invalid type color');
            colors[k] = v;
        }
        const atelier = r.atelierText ?? { enabled: false, options: {} };
        if (typeof atelier.enabled !== 'boolean')
            throw new RangeError('atelier text enabled');
        const atelierOptions = atelierTextOptions(atelier.options);
        const continuation = {};
        if (r.version === 9) {
            if (typeof r.graphTransitMs !== 'number' || !Number.isFinite(r.graphTransitMs) || r.graphTransitMs < 0 || r.graphTransitMs > 3000)
                throw new RangeError('graphTransitMs');
            if (!EFFECT_CATALOG.some(e => e.id === r.selectedEffect) || !['world', 'screen'].includes(r.effectSpace))
                throw new RangeError('Effect catalogue setting');
            const d = { ...m.worldDetail };
            if (!r.worldDetail || typeof r.worldDetail !== 'object' || Array.isArray(r.worldDetail))
                throw new RangeError('worldDetail');
            for (const [k, v] of Object.entries(r.worldDetail)) {
                const f = WORLD_DETAIL_FIELDS.find(f => f.name === k);
                if (!f || typeof v !== 'number' || !Number.isFinite(v) || v < f.min || v > f.max || (f.scale === 1 && !Number.isInteger(v)))
                    throw new RangeError('worldDetail ' + k);
                d[k] = v;
            }
            const ink = { ...m.inputWeather };
            if (!r.inputWeather || typeof r.inputWeather !== 'object' || Array.isArray(r.inputWeather))
                throw new RangeError('inputWeather');
            const ranges = { lifeMs: [100, 6000], speed: [1, 40], width: [.2, 3], gain: [0, .65], rings: [1, 4] };
            for (const [k, v] of Object.entries(r.inputWeather)) {
                if (k === 'enabled') {
                    if (typeof v !== 'boolean')
                        throw new RangeError('inputWeather enabled');
                    ink.enabled = v;
                    continue;
                }
                const range = ranges[k];
                if (!range || typeof v !== 'number' || !Number.isFinite(v) || v < range[0] || v > range[1] || (k === 'rings' && !Number.isInteger(v)))
                    throw new RangeError('inputWeather ' + k);
                ink[k] = v;
            }
            Object.assign(continuation, { worldDetail: d, inputWeather: ink, graphTransitMs: r.graphTransitMs, selectedEffect: r.selectedEffect, effectSpace: r.effectSpace });
        }
        extras = { ...continuation, atelierTextEnabled: atelier.enabled, atelierOptions, scenicMode: r.scenicMode, worldView: world, hashLength: r.hashLength, graphTypeColors: colors };
    }
    const meshScene = input?.scene === 'model-viewer';
    applyBlackHoleConfiguration(m, meshScene ? { ...input, scene: 'black-hole' } : input);
    if (meshScene)
        m.scene = 'model-viewer';
    if (extras) {
        const { atelierOptions, ...values } = extras;
        Object.assign(m, values);
        m.atelierPlayer = new AtelierTextPlayer(m.textSource.slice(0, 2048), atelierOptions);
        m.atelierPlayer.show(m.motionMs);
    }
    m.graphFrom.clear();
    m.graphTo.clear();
    m.inkEvents = [];
    m.effectShelf.clear();
}

