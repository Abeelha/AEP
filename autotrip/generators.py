"""Procedural backdrop generators — license-free, made from math, safe for a
public repo. Each returns an RGB float array (h,w,3) in 0..1."""
import numpy as np

PALETTES = {
    "violet": [(0.04, 0.02, 0.12), (0.35, 0.05, 0.5), (0.75, 0.15, 0.6)],
    "ember": [(0.05, 0.02, 0.05), (0.4, 0.08, 0.05), (0.95, 0.45, 0.1)],
    "cyber": [(0.02, 0.05, 0.1), (0.0, 0.4, 0.55), (0.2, 0.95, 0.85)],
    "noir": [(0.02, 0.02, 0.03), (0.2, 0.2, 0.22), (0.6, 0.6, 0.62)],
}


def _ramp(stops, t):
    stops = np.array(stops, np.float32)
    pos = np.linspace(0, 1, len(stops))
    return np.stack([np.interp(t, pos, stops[:, c]) for c in range(3)], -1)


def gradient(h, w, palette="violet", angle=0.4, seed=0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = (np.cos(angle) * xx / w + np.sin(angle) * yy / h)
    t = (t - t.min()) / (np.ptp(t) + 1e-9)
    return _ramp(PALETTES.get(palette, PALETTES["violet"]), t)


def swirl_field(h, w, palette="cyber", turns=3.0, seed=0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cy, cx = h / 2, w / 2
    ang = np.arctan2(yy - cy, xx - cx)
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(h, w)
    t = (np.sin(ang * turns + r * 12) * 0.5 + 0.5)
    return _ramp(PALETTES.get(palette, PALETTES["cyber"]), t)


def lines(h, w, palette="ember", spacing=26, angle=0.6, seed=0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    p = (np.cos(angle) * xx + np.sin(angle) * yy)
    stripe = 0.5 + 0.5 * np.sign(np.sin(p / spacing * np.pi))
    base = _ramp(PALETTES.get(palette, PALETTES["ember"]), yy / h)
    return base * (0.55 + 0.45 * stripe[..., None])


def hue_field(h, w, seed=0, **_):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    hphase = rng.uniform(0, 6.28)
    hh = (np.sin(xx / w * 6.28 + hphase) + np.cos(yy / h * 6.28)) * 0.25 + 0.5
    from .effects import _hsv_to_rgb
    hsv = np.stack([hh % 1.0, np.full_like(hh, 0.55), np.full_like(hh, 0.7)], -1)
    return _hsv_to_rgb(hsv)


GENERATORS = {"gradient": gradient, "swirl": swirl_field, "lines": lines, "hue": hue_field}
