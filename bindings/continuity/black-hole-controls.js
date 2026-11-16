
export class FormState {
    constructor(specs) {
        this.specs = new Map();
        this.revision = 0;
        if (!Array.isArray(specs) || specs.length > 128)
            throw new RangeError('128 controls max');
        for (const s of specs) {
            if (!s || !['text', 'textarea', 'checkbox', 'radio', 'select', 'multiselect', 'transfer', 'number'].includes(s.kind) || typeof s.label !== 'string' || s.label.length > 160 || s.disabled !== undefined && typeof s.disabled !== 'boolean' || s.required !== undefined && typeof s.required !== 'boolean' || s.min !== undefined && !Number.isFinite(s.min) || s.max !== undefined && !Number.isFinite(s.max) || s.min !== undefined && s.max !== undefined && s.min > s.max || s.choices !== undefined && (!Array.isArray(s.choices) || s.choices.length > 256 || s.choices.some(c => typeof c !== 'string' || c.length > 512)))
                throw new RangeError('Invalid control schema');
            if (!/^[\w.-]{1,64}$/.test(s.id) || this.specs.has(s.id))
                throw new RangeError('Unique control ID');
            this.specs.set(s.id, { ...s, choices: s.choices ? [...s.choices] : undefined, value: Array.isArray(s.value) ? [...s.value] : s.value });
            this.validate(s, s.value);
        }
    }
    validate(s, v) {
        if (s.kind === 'checkbox') {
            if (typeof v !== 'boolean')
                throw new TypeError('checkbox requires boolean');
        }
        else if (s.kind === 'number') {
            if (typeof v !== 'number' || !Number.isFinite(v) || v < (s.min ?? -1e9) || v > (s.max ?? 1e9))
                throw new RangeError('number bounds');
        }
        else if (s.kind === 'multiselect' || s.kind === 'transfer') {
            if (!Array.isArray(v) || new Set(v).size !== v.length || v.some(x => !s.choices?.includes(x)))
                throw new RangeError('selected values must be unique choices');
        }
        else {
            if (typeof v !== 'string' || v.length > 8192)
                throw new RangeError('bounded text required');
            if (['select', 'radio'].includes(s.kind) && !s.choices?.includes(v))
                throw new RangeError('unknown choice');
            if (s.required && !v.trim())
                throw new RangeError('required field');
        }
    }
    set(id, value) { const s = this.specs.get(id); if (!s)
        throw new RangeError('unknown control'); if (s.disabled)
        throw new Error('disabled control'); this.validate(s, value); s.value = Array.isArray(value) ? [...value] : value; this.revision++; }
    list() { return [...this.specs.values()].map(s => ({ ...s, choices: s.choices ? [...s.choices] : undefined, value: Array.isArray(s.value) ? [...s.value] : s.value })); }
    values() { return Object.fromEntries(this.list().map(s => [s.id, s.value])); }
}
export const MODAL_KINDS = ['center', 'fullscreen', 'drawer-left', 'drawer-right', 'drawer-top', 'drawer-bottom', 'corner', 'toast', 'error', 'confirmation', 'dropdown'];
/** Topmost modal exclusively owns its input scope. Escape dismisses one level. */
export class ModalStack {
    constructor() {
        this.items = [];
    }
    push(entry) { if (!entry || typeof entry.id !== 'string' || !/^[\w.-]{1,64}$/.test(entry.id) || !Number.isFinite(entry.atMs) || entry.atMs < 0 || typeof entry.dismissible !== 'boolean' || this.items.length >= 8 || !MODAL_KINDS.includes(entry.kind) || typeof entry.title !== 'string' || entry.title.length > 160 || typeof entry.body !== 'string' || entry.body.length > 16384)
        throw new RangeError('modal bounds'); this.items.push({ ...entry }); }
    peek() { const e = this.items[this.items.length - 1]; return e ? { ...e } : undefined; }
    dismiss() { if (!this.peek()?.dismissible)
        return false; this.items.pop(); return true; }
    clear() { this.items = []; }
}
/** Evaluate bounded + - * / parentheses and named numeric variables. No eval,
 * function calls, property access, loops, or assignments. Division by zero rejects. */
export function calculateFormula(source, variables) {
    if (typeof source !== 'string' || source.length > 512)
        throw new RangeError('Formula limit');
    const tokens = source.match(/(?:\d+(?:\.\d*)?|\.\d+)|[A-Za-z_][A-Za-z0-9_]*|[()+*/-]/g) ?? [];
    if (tokens.join('') !== source.replace(/\s/g, '') || tokens.length > 128)
        throw new Error('Unsupported formula syntax');
    let at = 0;
    function atom() { const t = tokens[at++]; if (t === '(') {
        const n = expression();
        if (tokens[at++] !== ')')
            throw new Error('Missing )');
        return n;
    } if (t === '-')
        return -atom(); if (t === '+')
        return atom(); if (t === undefined)
        throw new Error('Missing operand'); if (/^\d|^\./.test(t))
        return Number(t); if (!Object.prototype.hasOwnProperty.call(variables, t) || !Number.isFinite(variables[t]))
        throw new Error('Unknown numeric variable ' + t); return variables[t]; }
    function product() { let v = atom(); while (tokens[at] === '*' || tokens[at] === '/') {
        const op = tokens[at++], b = atom();
        if (op === '/' && b === 0)
            throw new Error('Division by zero');
        v = op === '*' ? v * b : v / b;
    } return v; }
    function expression() { let v = product(); while (tokens[at] === '+' || tokens[at] === '-') {
        const op = tokens[at++], b = product();
        v = op === '+' ? v + b : v - b;
    } return v; }
    const result = expression();
    if (at !== tokens.length || !Number.isFinite(result))
        throw new Error('Invalid formula result');
    return result;
}

