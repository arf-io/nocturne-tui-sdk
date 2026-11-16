"""Independent exact-arithmetic color reference for the native ABI test matrix.

Reference: W3C Compositing and Blending Level 1, 2024-03-21, sections 6,
9.1 and 10 (https://www.w3.org/TR/2024/CRD-compositing-1-20240321/).
Nocturne's additional arithmetic modes are specified in COLOR-REFERENCE.md.
This module imports no SDK, native math, generated output, or historical engine.
"""
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache

BLENDS = ('normal', 'multiply', 'screen', 'overlay', 'darken', 'lighten',
          'color-dodge', 'color-burn', 'hard-light', 'soft-light', 'difference',
          'exclusion', 'hue', 'saturation', 'color', 'luminosity', 'additive',
          'subtractive', 'divide', 'linear-burn', 'linear-light', 'vivid-light',
          'pin-light', 'hard-mix', 'darker-color', 'lighter-color', 'dissolve', 'none')
OPERATORS = ('source-over', 'clear', 'source', 'destination', 'destination-over',
             'source-in', 'destination-in', 'source-out', 'destination-out',
             'source-atop', 'destination-atop', 'xor', 'lighter')
ONE = Fraction(1)
ZERO = Fraction(0)


def clamp(value):
    """Return a rational coverage/channel clipped to the inclusive unit range."""
    return max(ZERO, min(ONE, value))


def unpackRgb(packed):
    """Decode an RGB24 integer into three exact encoded-sRGB channel fractions."""
    return tuple(Fraction((packed >> shift) & 255, 255) for shift in (16, 8, 0))


def luminance(channels):
    return sum(c * w for c, w in zip(channels, (Fraction(30, 100), Fraction(59, 100), Fraction(11, 100))))


def withLuminance(channels, target):
    shifted = tuple(c + target - luminance(channels) for c in channels)
    low, high = min(shifted), max(shifted)
    if low < 0:
        shifted = tuple(target + (c - target) * target / (target - low) for c in shifted)
    if high > 1:
        shifted = tuple(target + (c - target) * (1 - target) / (high - target) for c in shifted)
    return shifted


def withSaturation(channels, target):
    # Work through sorted channel identities, as defined by the reference, to
    # exercise equal-channel cases independently of native's vector shortcut.
    order = sorted(range(3), key=lambda i: (channels[i], i))
    low, middle, high = order
    result = [ZERO, ZERO, ZERO]
    if channels[high] != channels[low]:
        result[middle] = (channels[middle] - channels[low]) * target / (channels[high] - channels[low])
        result[high] = target
    return tuple(result)


def softLight(backdrop, source):
    if source <= Fraction(1, 2):
        return backdrop - (1 - 2 * source) * backdrop * (1 - backdrop)
    if backdrop <= Fraction(1, 4):
        response = ((16 * backdrop - 12) * backdrop + 4) * backdrop
    else:
        with localcontext() as context:
            context.prec = 70
            response = Fraction((Decimal(backdrop.numerator) / Decimal(backdrop.denominator)).sqrt())
    return backdrop + (2 * source - 1) * (response - backdrop)


def dodge(backdrop, source):
    if backdrop == 0:
        return ZERO
    return ONE if source == 1 else clamp(backdrop / (1 - source))


def burn(backdrop, source):
    if backdrop == 1:
        return ONE
    return ZERO if source == 0 else 1 - clamp((1 - backdrop) / source)


def hardLight(backdrop, source):
    return 2 * backdrop * source if source <= Fraction(1, 2) else 1 - 2 * (1 - backdrop) * (1 - source)


@lru_cache(maxsize=1024)
def referenceBlend(base, source, mode):
    """Evaluate a documented blend using rational arithmetic, not SDK output.

    Inputs are RGB24 colors and one name in BLENDS except dissolve. Returns three
    fractions. Dissolve is deliberately tested as its two coverage outcomes; this
    oracle does not reimplement the SDK's keyed random function.
    """
    b, s = unpackRgb(base), unpackRgb(source)
    if mode in ('normal', 'none'):
        return s
    if mode == 'hue':
        return withLuminance(withSaturation(s, max(b) - min(b)), luminance(b))
    if mode == 'saturation':
        return withLuminance(withSaturation(b, max(s) - min(s)), luminance(b))
    if mode == 'color':
        return withLuminance(s, luminance(b))
    if mode == 'luminosity':
        return withLuminance(b, luminance(s))
    if mode == 'darker-color':
        return s if luminance(s) < luminance(b) else b
    if mode == 'lighter-color':
        return s if luminance(s) > luminance(b) else b
    equations = {
        'multiply': lambda b, s: b * s,
        'screen': lambda b, s: 1 - (1 - b) * (1 - s),
        'overlay': lambda b, s: hardLight(s, b),
        'darken': min,
        'lighten': max,
        'color-dodge': dodge,
        'color-burn': burn,
        'hard-light': hardLight,
        'soft-light': softLight,
        'difference': lambda b, s: abs(b - s),
        'exclusion': lambda b, s: b * (1 - s) + s * (1 - b),
        'additive': lambda b, s: clamp(b + s),
        'subtractive': lambda b, s: clamp(b - s),
        'divide': lambda b, s: ONE if s == 0 else clamp(b / s),
        'linear-burn': lambda b, s: clamp(b + s - 1),
        'linear-light': lambda b, s: clamp(b + 2 * s - 1),
        'vivid-light': lambda b, s: burn(b, 2 * s) if s < Fraction(1, 2) else dodge(b, 2 * s - 1),
        'pin-light': lambda b, s: min(b, 2 * s) if s < Fraction(1, 2) else max(b, 2 * s - 1),
        'hard-mix': lambda b, s: ZERO if b + s < 1 else ONE,
    }
    return tuple(equations[mode](bc, sc) for bc, sc in zip(b, s))


def quantize(value, scale):
    """Round a unit fraction to an unsigned scale, exact half-up at the boundary."""
    scaled = clamp(value) * scale
    return (scaled.numerator * 2 + scaled.denominator) // (scaled.denominator * 2)


def referenceComposite(base, source, baseAlpha, sourceAlpha, blend, operation):
    """Return RGB24/alpha16 from exact Porter-Duff area coefficients.

    Invalid names raise KeyError. The caller supplies valid ABI integer ranges.
    The lighter operator saturates premultiplied color and alpha before division.
    Example: referenceComposite(0, 0xffffff, 65535, 65535, 'normal', 'source').
    """
    ab, ass = Fraction(baseAlpha, 65535), Fraction(sourceAlpha, 65535)
    # Each pair is source area, destination area. These coefficients are the
    # Porter-Duff coverage table, evaluated independently of the implementation.
    factors = {
        'source-over': (ONE, 1 - ass), 'clear': (ZERO, ZERO),
        'source': (ONE, ZERO), 'destination': (ZERO, ONE),
        'destination-over': (1 - ab, ONE), 'source-in': (ab, ZERO),
        'destination-in': (ZERO, ass), 'source-out': (1 - ab, ZERO),
        'destination-out': (ZERO, 1 - ass), 'source-atop': (ab, 1 - ass),
        'destination-atop': (1 - ab, ass), 'xor': (1 - ab, 1 - ass),
        'lighter': (ONE, ONE),
    }
    fs, fb = factors[operation]
    alpha = ass * fs + ab * fb
    if alpha == 0:
        return 0, 0
    channels = []
    for b, s, mixed in zip(unpackRgb(base), unpackRgb(source), referenceBlend(base, source, blend)):
        premultiplied = ass * fs * ((1 - ab) * s + ab * clamp(mixed)) + ab * fb * b
        channels.append(quantize(clamp(premultiplied) / clamp(alpha), 255))
    return (channels[0] << 16) | (channels[1] << 8) | channels[2], quantize(alpha, 65535)
