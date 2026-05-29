"""Mask-aware compositing: separate subject from background and treat each.

If no real matte is available, falls back to a soft radial mask centered on the
detected face (or frame center) — good enough for vignette / background blur.
"""
import numpy as np
from PIL import Image, ImageFilter
from .effects import to_arr, to_img


def radial_mask(h, w, faces=None, softness=0.6):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    if faces:
        fx, fy, fw, fh = faces[0]
        cx, cy = fx + fw / 2, fy + fh / 2 + fh * 0.8  # bias down to body
        rad = max(fw, fh) * 2.4
    else:
        cx, cy, rad = w / 2, h / 2, min(h, w) * 0.55
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / rad
    return np.clip(1 - (d - softness) / (1 - softness + 1e-9), 0, 1)


def _mask3(mask):
    return mask[..., None]


def blur_background(arr, mask, radius=14):
    blurred = to_arr(to_img(arr).filter(ImageFilter.GaussianBlur(radius)))
    m = _mask3(mask)
    return arr * m + blurred * (1 - m)


def darken_background(arr, mask, amount=0.55):
    m = _mask3(mask)
    return arr * m + arr * (1 - amount) * (1 - m)


def replace_background(arr, mask, bg_arr):
    if bg_arr.shape[:2] != arr.shape[:2]:
        bg_arr = to_arr(to_img(bg_arr).resize((arr.shape[1], arr.shape[0])))
    m = _mask3(mask)
    return arr * m + bg_arr * (1 - m)


def overlay(arr, layer, opacity=0.5, mode="screen", mask=None):
    """Blend a generated layer over the image. mask: where to apply (None=all)."""
    if layer.shape[:2] != arr.shape[:2]:
        layer = to_arr(to_img(layer).resize((arr.shape[1], arr.shape[0])))
    if mode == "screen":
        blended = 1 - (1 - arr) * (1 - layer)
    elif mode == "multiply":
        blended = arr * layer
    elif mode == "add":
        blended = np.clip(arr + layer, 0, 1)
    else:  # normal
        blended = layer
    out = arr * (1 - opacity) + blended * opacity
    if mask is not None:
        m = _mask3(mask)
        out = arr * m + out * (1 - m)   # protect subject by default
    return np.clip(out, 0, 1)
