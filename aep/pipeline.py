"""Orchestrator: image in -> scene analysis -> N edited variants out + contact sheet.

Recipe selection is scene-aware:
  person       -> protect subject, treat background (blur/darken/replace), grade
  environment  -> full-frame grade + procedural overlay + tone/hue shift
Each variant is logged so the memory module can learn which recipes you prefer.
"""
import os
import numpy as np
from PIL import Image
from . import detect, generators, assets, compositor as comp
from .effects import to_arr, to_img, apply_chain, PRESETS, EFFECTS


def _grid(images, cols=None):
    cols = cols or min(len(images), 3)
    rows = (len(images) + cols - 1) // cols
    w, h = images[0].size
    sheet = Image.new("RGB", (w * cols, h * rows), (12, 12, 14))
    for i, im in enumerate(images):
        sheet.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
    return sheet


def build_recipes(scene, n):
    """Return list of (label, callable arr->arr) tailored to the scene."""
    recipes = []

    def person_recipe(label, preset, bg_mode, gen=None, pal="violet"):
        chain = PRESETS[preset]

        def fn(arr, sc):
            mask = sc["mask"] if sc["has_mask"] else comp.radial_mask(*arr.shape[:2], sc["faces"])
            if bg_mode == "blur":
                arr = comp.blur_background(arr, mask, 16)
            elif bg_mode == "darken":
                arr = comp.darken_background(arr, mask, 0.6)
            elif bg_mode == "replace":
                bg = to_arr(assets.backdrop(arr.shape[1], arr.shape[0], "person", seed=hash(label) % 1000))
                arr = comp.replace_background(arr, mask, bg)
            if gen:
                layer = generators.GENERATORS[gen](*arr.shape[:2], palette=pal, seed=7)
                arr = comp.overlay(arr, layer, 0.35, "screen", mask=mask)
            return apply_chain(arr, chain)
        return label, fn

    def env_recipe(label, preset, gen, pal):
        chain = PRESETS[preset]

        def fn(arr, sc):
            layer = generators.GENERATORS[gen](*arr.shape[:2], palette=pal, seed=11)
            arr = comp.overlay(arr, layer, 0.4, "screen")
            return apply_chain(arr, chain)
        return label, fn

    if scene == "person":
        recipes += [
            person_recipe("night_blur", "gabriel_night", "blur"),
            person_recipe("night_dark", "gabriel_night", "darken", gen="lines", pal="ember"),
            person_recipe("duotone_swirl", "gabriel_duotone", "darken", gen="swirl", pal="violet"),
            person_recipe("bw_blur", "gabriel_bw", "blur"),
            person_recipe("acid_replace", "acid", "replace", gen="hue"),
        ]
    else:
        recipes += [
            env_recipe("night_grad", "gabriel_night", "gradient", "violet"),
            env_recipe("duotone", "gabriel_duotone", "swirl", "cyber"),
            env_recipe("acid", "acid", "hue", "violet"),
            env_recipe("vhs", "vhs_dream", "lines", "ember"),
            env_recipe("bw_grit", "gabriel_bw", "gradient", "noir"),
        ]
    return recipes[:n]


def process(path, out_dir, n_variants=5, contact_sheet=True):
    img = Image.open(path).convert("RGB")
    scene = detect.analyze(img)
    arr0 = to_arr(img)
    stem = os.path.splitext(os.path.basename(path))[0]
    dest = os.path.join(out_dir, stem)
    os.makedirs(dest, exist_ok=True)

    variants, results = [], []
    for label, fn in build_recipes(scene["scene"], n_variants):
        try:
            out = to_img(np.clip(fn(arr0.copy(), scene), 0, 1))
        except Exception as e:                       # never let one recipe kill the batch
            results.append({"label": label, "error": str(e)})
            continue
        fp = os.path.join(dest, f"{label}.jpg")
        out.save(fp, quality=92)
        variants.append(out)
        results.append({"label": label, "file": fp})

    if contact_sheet and variants:
        sheet = _grid([v.resize((v.width // 2, v.height // 2)) for v in variants])
        sheet.save(os.path.join(dest, "_contact_sheet.jpg"), quality=88)

    meta = {"input": path, "scene": {k: scene[k] for k in ("scene", "n_faces", "portrait", "has_mask")},
            "variants": results, "dest": dest}
    return meta
