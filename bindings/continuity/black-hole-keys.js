
const MOD_ORDER = ['Ctrl', 'Alt', 'Shift', 'Super'];
/** Canonical aliases: Option=Alt, Cmd/Meta=Super. Hyper means all FOUR named
 * modifiers in this library; physical kitty Hyper is mapped to the same chord. */
export function normalizeChord(input) {
    if (typeof input !== 'string' || input.length > 128)
        throw new RangeError('Bounded chord required');
    let parts = input.split('+').map(s => s.trim()).filter(Boolean);
    const mods = new Set(), keys = [];
    for (const raw of parts) {
        const s = raw.toLowerCase();
        if (s === 'hyper') {
            MOD_ORDER.forEach(m => mods.add(m));
            continue;
        }
        const m = { control: 'Ctrl', ctrl: 'Ctrl', alt: 'Alt', option: 'Alt', shift: 'Shift', meta: 'Super', cmd: 'Super', command: 'Super', super: 'Super' }[s];
        if (m)
            mods.add(m);
        else
            keys.push(raw);
    }
    if (keys.length !== 1)
        throw new RangeError('Chord requires one non-modifier key');
    let key = keys[0];
    const names = { esc: 'Escape', escape: 'Escape', space: 'Space', spacebar: 'Space', enter: 'Enter', return: 'Enter', tab: 'Tab', backspace: 'Backspace', delete: 'Delete', arrowleft: 'ArrowLeft', arrowright: 'ArrowRight', arrowup: 'ArrowUp', arrowdown: 'ArrowDown', home: 'Home', end: 'End', pageup: 'PageUp', pagedown: 'PageDown' };
    key = names[key.toLowerCase()] ?? key.toUpperCase();
    return [...MOD_ORDER.filter(m => mods.has(m)), key].join('+');
}
function reserved(chord, profile) {
    if (['Ctrl+C', 'Ctrl+Z', 'Ctrl+S', 'Ctrl+Q'].includes(chord))
        return 'Terminal interrupt/suspend/flow-control policy';
    if (['Alt+Tab', 'Super+Tab'].includes(chord))
        return 'Often intercepted by the OS window switcher';
    if (profile === 'browser' && ['Ctrl+T', 'Ctrl+W', 'Ctrl+N', 'Ctrl+L', 'Ctrl+R', 'Super+T', 'Super+N', 'Super+W'].includes(chord))
        return 'Browser-reserved action; delivery cannot be guaranteed';
    if ((profile === 'mac' || profile === 'windows') && chord.startsWith('Super+'))
        return 'Host/window-manager shortcut may intercept Super';
    if (profile === 'tmux' && chord === 'Ctrl+B')
        return 'Common tmux prefix';
    return undefined;
}
/** Compile declarations atomically. Collisions always throw; intentional OS
 * override acknowledges risk only and cannot authorize two active handlers.
 * Example: new Keymap(bindings,'browser',true).resolve('F1','warp',false). */
export class Keymap {
    constructor(bindings, profile = 'posix', strict = false) {
        this.warnings = [];
        if (!['browser', 'posix', 'mac', 'windows', 'tmux'].includes(profile) || typeof strict !== 'boolean')
            throw new RangeError('Unknown host profile / strict policy');
        if (!Array.isArray(bindings) || bindings.length > 256)
            throw new RangeError('At most 256 bindings');
        const ids = new Set();
        this.bindings = bindings.map(b => {
            if (!b || typeof b.id !== 'string' || !/^[\w.-]{1,64}$/.test(b.id) || ids.has(b.id) || !Array.isArray(b.scopes) || !b.scopes.length || b.scopes.length > 64 || b.scopes.some(s => typeof s !== 'string' || s.length < 1 || s.length > 64) || b.label !== undefined && (typeof b.label !== 'string' || b.label.length > 160) || b.allowInText !== undefined && typeof b.allowInText !== 'boolean' || b.overrideReserved !== undefined && typeof b.overrideReserved !== 'boolean')
                throw new RangeError('Unique IDs and bounded scopes required');
            ids.add(b.id);
            return { ...b, scopes: [...b.scopes], chord: normalizeChord(b.chord) };
        });
        for (let i = 0; i < this.bindings.length; i++) {
            const a = this.bindings[i], reason = reserved(a.chord, profile);
            if (reason && !a.overrideReserved) {
                this.warnings.push({ id: a.id, chord: a.chord, reason });
                if (strict)
                    throw new Error(`Reserved ${a.chord}: explicit overrideReserved required`);
            }
            for (let j = 0; j < i; j++) {
                const b = this.bindings[j];
                if (a.chord === b.chord && (a.scopes.includes('*') || b.scopes.includes('*') || a.scopes.some(s => b.scopes.includes(s))))
                    throw new Error(`Overlapping shortcut ${a.chord}: ${a.id} / ${b.id}`);
            }
        }
    }
    resolve(chord, screen, textFocused) { const key = normalizeChord(chord); return this.bindings.find(b => b.chord === key && (b.scopes.includes('*') || b.scopes.includes(screen)) && (!textFocused || b.allowInText)); }
    search(query) { const q = query.toLowerCase(); return this.bindings.filter(b => `${b.id} ${b.label ?? ''} ${b.chord}`.toLowerCase().includes(q)); }
}
export function browserChord(e) {
    if (['Control', 'Alt', 'Shift', 'Meta', 'Dead', 'Unidentified'].includes(e.key))
        return null;
    const key = e.key === ' ' ? 'Space' : e.key === '+' ? 'Plus' : e.key;
    try {
        return normalizeChord([e.ctrlKey ? 'Ctrl' : '', e.altKey ? 'Alt' : '', e.shiftKey ? 'Shift' : '', e.metaKey ? 'Super' : '', key].filter(Boolean).join('+'));
    }
    catch {
        return null;
    }
}
/** Decode the press form of kitty CSI-u. Does not negotiate the protocol or
 * claim that legacy terminals distinguish every modifier combination. */
export function decodeKittyKey(sequence) {
    const match = /^\x1b\[(\d+)(?::\d+)?(?:;(\d+)(?::(\d+))?)?u$/.exec(sequence);
    if (!match || match[3] === '3')
        return null;
    const cp = Number(match[1]), bits = Number(match[2] ?? 1) - 1;
    if (cp < 0 || cp > 0x10ffff)
        return null;
    const specials = { 13: 'Enter', 27: 'Escape', 9: 'Tab', 127: 'Backspace', 57350: 'ArrowLeft', 57351: 'ArrowRight', 57352: 'ArrowUp', 57353: 'ArrowDown', 57364: 'F1' };
    return normalizeChord([(bits & 4) ? 'Ctrl' : '', (bits & 2) ? 'Alt' : '', (bits & 1) ? 'Shift' : '', (bits & 8) ? 'Super' : '', (bits & 16) ? 'Hyper' : '', specials[cp] ?? (cp === 32 ? 'Space' : String.fromCodePoint(cp))].filter(Boolean).join('+'));
}
export const DEFAULT_BLACK_HOLE_KEYS = [
    { id: 'help', label: 'Help / searchable commands', chord: 'F1', scopes: ['*'], allowInText: true },
    { id: 'escape', label: 'Dismiss topmost overlay, then open menu', chord: 'Escape', scopes: ['*'], allowInText: true },
    { id: 'commands', label: 'Search commands and shortcuts', chord: 'Ctrl+/', scopes: ['*'], allowInText: true },
    { id: 'windows', label: 'Window switcher', chord: 'F6', scopes: ['*'], allowInText: true },
    { id: 'hold', label: 'Hold decorative motion', chord: 'Ctrl+P', scopes: ['*'], allowInText: true },
    { id: 'brake', label: 'Brake travel', chord: 'Space', scopes: ['warp', 'black-hole', 'infinite', 'ocean', 'tarmac', 'waterfall'] },
    { id: 'new-window', label: 'New window', chord: 'Ctrl+N', scopes: ['windows', 'fleet-room'], overrideReserved: true },
    { id: 'new-tab', label: 'Next agent tab', chord: 'Ctrl+T', scopes: ['fleet-room'], overrideReserved: true },
    { id: 'gather', label: 'Gather windows', chord: 'G', scopes: ['windows', 'fleet-room'] },
    { id: 'visit', label: 'Visit selected window', chord: 'V', scopes: ['windows', 'fleet-room'] },
    { id: 'summon', label: 'Summon selected window', chord: 'B', scopes: ['windows', 'fleet-room'] }
];

