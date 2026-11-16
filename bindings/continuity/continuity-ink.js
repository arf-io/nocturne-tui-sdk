import {clamp,mixColor,flattened} from './observatory.js';
/** Paint independent rings, preserving occupied glyphs and semantic hit IDs.
 * Maximum radius is 26 cells; at most 96 retained events; palette samples are
 * computed once per ring, not once per pixel. Returns active impulse count. */
export function paintInkWeather(frame, events, timeMs, color) {
    let active = 0;
    for (const e of events) {
        const age = (timeMs - e.atMs) / 1000, life = e.lifeMs / 1000;
        if (age <= 0 || age >= life)
            continue;
        active++;
        const radius = Math.min(26, age * e.speed), fade = Math.min(1, age / .055) * Math.pow(1 - age / life, 1.3), colors = Array.from({ length: e.rings }, (_, r) => color(e.hue + r * 48 + age * 24));
        const extent = Math.min(28, radius + e.width * 2), x0 = Math.max(0, Math.floor(e.x - extent)), x1 = Math.min(frame.width - 1, Math.ceil(e.x + extent)), y0 = Math.max(0, Math.floor(e.y - extent / 2)), y1 = Math.min(frame.height - 1, Math.ceil(e.y + extent / 2));
        for (let y = y0; y <= y1; y++)
            for (let x = x0; x <= x1; x++) {
                const k = (y * frame.width + x) * 4, old = flattened(frame, k);
                let upper = old, lower = old, opacity = 0;
                for (let half = 0; half < 2; half++) {
                    const distance = Math.hypot(x + .5 - e.x, (y + (half ? .75 : .25) - e.y) * 2);
                    let alpha = 0, ring = 0;
                    for (let r = 0; r < e.rings; r++) {
                        const rr = radius - r * 2.4;
                        if (rr < 0)
                            continue;
                        const a = clamp(1 - Math.abs(distance - rr) / (e.width * 2), 0, 1);
                        const power = a * a * (3 - 2 * a) * Math.pow(.84, r);
                        if (power > alpha) {
                            alpha = power;
                            ring = r;
                        }
                    }
                    alpha *= fade * e.gain;
                    opacity += alpha;
                    if (half)
                        lower = mixColor(old, colors[ring], alpha);
                    else
                        upper = mixColor(old, colors[ring], alpha);
                }
                if (opacity < .008)
                    continue;
                if (frame.cells[k] === 32 || frame.cells[k] === 0x2580) {
                    frame.cells[k] = 0x2580;
                    frame.cells[k + 1] = upper;
                    frame.cells[k + 2] = lower;
                }
                else
                    frame.cells[k + 2] = mixColor(upper, lower, .5);
            }
    }
    return active;
}

