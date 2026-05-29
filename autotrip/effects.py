"""Pixel-level trippy effects + style presets. Pure numpy/Pillow, deterministic."""
import numpy as np
from PIL import Image, ImageFilter


def to_arr(img):
    return np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0


def to_img(arr):
    arr = np.clip(arr, 0.0, 1.0)
    return Image.fromarray((arr * 255.0 + 0.5).astype(np.uint8), "RGB")


def _bilinear(arr, xs, ys):
    h, w = arr.shape[:2]
    xs = np.clip(xs, 0, w - 1); ys = np.clip(ys, 0, h - 1)
    x0 = np.floor(xs).astype(np.int32); x1 = np.minimum(x0 + 1, w - 1)
    y0 = np.floor(ys).astype(np.int32); y1 = np.minimum(y0 + 1, h - 1)
    wx = (xs - x0)[..., None]; wy = (ys - y0)[..., None]
    a = arr[y0, x0]; b = arr[y0, x1]; c = arr[y1, x0]; d = arr[y1, x1]
    return (a * (1 - wx) + b * wx) * (1 - wy) + (c * (1 - wx) + d * wx) * wy


def _rgb_to_hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); df = mx - mn + 1e-12
    h = np.zeros_like(mx)
    m = mx == r; h[m] = ((g - b) / df)[m] % 6
    m = mx == g; h[m] = ((b - r) / df)[m] + 2
    m = mx == b; h[m] = ((r - g) / df)[m] + 4
    return np.stack([h / 6.0, np.where(mx == 0, 0, df / (mx + 1e-12)), mx], -1)


def _hsv_to_rgb(a):
    h, s, v = a[..., 0] * 6, a[..., 1], a[..., 2]
    i = np.floor(h).astype(int) % 6; f = h - np.floor(h)
    p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
    out = np.zeros(a.shape, np.float32)
    R = [v, q, p, p, t, v]; G = [t, v, v, q, p, p]; B = [p, p, t, v, v, q]
    for k in range(6):
        c = i == k
        out[c, 0] = R[k][c]; out[c, 1] = G[k][c]; out[c, 2] = B[k][c]
    return out


def hue(a, t):
    hsv = _rgb_to_hsv(a)
    hsv[..., 0] = (hsv[..., 0] + t) % 1.0
    hsv[..., 1] = np.clip(hsv[..., 1] * (1 + t), 0, 1)
    return _hsv_to_rgb(hsv)


def chroma(a, t):
    sh = int(max(1, t * 0.03 * a.shape[1]))
    out = a.copy()
    out[..., 0] = np.roll(a[..., 0], sh, axis=1)
    out[..., 2] = np.roll(a[..., 2], -sh, axis=1)
    return out


def swirl(a, t):
    h, w = a.shape[:2]; cy, cx = h / 2, w / 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = xx - cx; dy = yy - cy
    r = np.sqrt(dx * dx + dy * dy); ang = np.arctan2(dy, dx)
    rmax = np.sqrt(cx * cx + cy * cy)
    ang = ang + t * 4.0 * (1 - r / rmax)
    return _bilinear(a, cx + r * np.cos(ang), cy + r * np.sin(ang))


def wave(a, t):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    amp = t * 0.04 * w
    return _bilinear(a, xx + amp * np.sin(2 * np.pi * yy / (h / 6.0)),
                     yy + amp * np.cos(2 * np.pi * xx / (w / 6.0)))


def kaleido(a, t):
    h, w = a.shape[:2]; seg = max(3, int(3 + t * 9)); cy, cx = h / 2, w / 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = xx - cx; dy = yy - cy
    r = np.sqrt(dx * dx + dy * dy); ang = np.arctan2(dy, dx)
    wedge = 2 * np.pi / seg
    ang = np.abs(((ang % wedge) + wedge) % wedge - wedge / 2)
    return _bilinear(a, cx + r * np.cos(ang), cy + r * np.sin(ang))


def gradmap(a, t, palette=None):
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    if palette is None:  # violet -> magenta -> warm dream
        palette = np.array([[0.04, 0.02, 0.12], [0.28, 0.05, 0.42], [0.55, 0.08, 0.55],
                            [0.85, 0.25, 0.55], [0.95, 0.6, 0.5], [0.98, 0.9, 0.75]], np.float32)
    pos = np.linspace(0, 1, len(palette))
    out = np.stack([np.interp(lum, pos, palette[:, c]) for c in range(3)], -1)
    return a * (1 - t) + out * t


def posterize(a, t):
    levels = max(2, int(8 - t * 6))
    return np.round(a * (levels - 1)) / (levels - 1)


def solarize(a, t):
    thr = 1 - t * 0.5
    return np.where(a < thr, a, 1 - a)


def glitch(a, t):
    h, w = a.shape[:2]; out = a.copy(); rng = np.random.default_rng(7)
    for _ in range(int(t * 30) + 1):
        y0 = rng.integers(0, h); hh = rng.integers(1, max(2, h // 20))
        sh = rng.integers(-int(0.1 * w), int(0.1 * w) + 1); ch = rng.integers(0, 3)
        out[y0:y0 + hh, :, ch] = np.roll(out[y0:y0 + hh, :, ch], sh, axis=1)
    return out


def grain(a, t):
    return a + np.random.default_rng(1).normal(0, t * 0.12, a.shape).astype(np.float32)


def bloom(a, t):
    blur = to_arr(to_img(np.clip(a - 0.6, 0, 1) * 2.5).filter(ImageFilter.GaussianBlur(8)))
    return np.clip(a + blur * t * 1.5, 0, 1)


def vignette(a, t):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); cy, cx = h / 2, w / 2
    d = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / np.sqrt(2)
    return a * (1 - t * np.clip(d, 0, 1) ** 2.2)[..., None]


def crush(a, t):
    a = np.clip((a - 0.04 * t) / (1 - 0.04 * t), 0, 1)
    a = a ** (1 + 0.4 * t)
    a = a + t * 0.25 * (a - a ** 2) * (a - 0.5)
    return np.clip(a, 0, 0.96)


def splittone(a, t):
    lum = (a @ [0.299, 0.587, 0.114])[..., None]
    shadow = np.array([0.15, 0.25, 0.55], np.float32)
    high = np.array([0.85, 0.45, 0.25], np.float32)
    tint = shadow * (1 - lum) + high * lum
    return np.clip(a * (1 - t * 0.35) + tint * a * t * 0.7 + (tint - 0.5) * t * 0.18, 0, 1)


def halftone(a, t):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    grid = (0.5 + 0.5 * np.cos(yy * np.pi)) * (0.85 + 0.15 * np.cos(xx * np.pi))
    return a * (1 - t * 0.35 * (1 - grid))[..., None]


def mono(a, t):
    lum = a @ [0.299, 0.587, 0.114]
    bw = np.clip((np.repeat(lum[..., None], 3, -1) - 0.05) / 0.9, 0, 1) ** 1.15
    return a * (1 - t) + bw * t


EFFECTS = {
    "hue": hue, "chroma": chroma, "swirl": swirl, "wave": wave, "kaleido": kaleido,
    "gradmap": gradmap, "posterize": posterize, "solarize": solarize, "glitch": glitch,
    "grain": grain, "bloom": bloom, "vignette": vignette, "crush": crush,
    "splittone": splittone, "halftone": halftone, "mono": mono,
}

# Style presets distilled from the reference edit set (dark lo-fi nightlife).
PRESETS = {
    "gabriel_night": [("crush", 0.8), ("splittone", 0.7), ("vignette", 0.6),
                      ("halftone", 0.5), ("grain", 0.45)],
    "gabriel_duotone": [("crush", 0.6), ("gradmap", 0.6), ("vignette", 0.55),
                        ("grain", 0.4), ("halftone", 0.4)],
    "gabriel_bw": [("mono", 1.0), ("crush", 0.7), ("vignette", 0.6),
                   ("grain", 0.6), ("halftone", 0.45)],
    "acid": [("hue", 0.25), ("gradmap", 0.5), ("chroma", 0.5), ("bloom", 0.5), ("grain", 0.3)],
    "vhs_dream": [("chroma", 0.6), ("halftone", 0.6), ("crush", 0.5), ("grain", 0.5),
                  ("splittone", 0.4)],
}


def apply_chain(arr, chain):
    for name, t in chain:
        arr = EFFECTS[name](arr, t)
    return arr
