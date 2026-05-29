"""Backdrop asset fetcher.

Default source = Lorem Picsum (https://picsum.photos): free, no API key, returns
license-free stock photos. Optional Pexels source if an API key is set in config
(env PEXELS_API_KEY) — useful for query-driven backgrounds (nature/buildings).

Downloaded files cache under assets/cache/ which is git-ignored — never committed.
"""
import os
import io
import hashlib
import requests
from PIL import Image

CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "cache")
os.makedirs(CACHE, exist_ok=True)


def _cache_path(key, ext="jpg"):
    return os.path.join(CACHE, hashlib.md5(key.encode()).hexdigest() + "." + ext)


def picsum(w, h, seed=0):
    """Deterministic license-free backdrop from Lorem Picsum."""
    key = f"picsum:{seed}:{w}x{h}"
    cp = _cache_path(key)
    if os.path.exists(cp):
        return Image.open(cp).convert("RGB")
    url = f"https://picsum.photos/seed/{seed}/{w}/{h}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    img.save(cp, quality=90)
    return img


def pexels(query, w, h, api_key=None):
    """Query-driven backdrop (nature/buildings/etc). Needs a Pexels API key."""
    api_key = api_key or os.environ.get("PEXELS_API_KEY")
    if not api_key:
        raise RuntimeError("no PEXELS_API_KEY set; falling back to picsum")
    key = f"pexels:{query}:{w}x{h}"
    cp = _cache_path(key)
    if os.path.exists(cp):
        return Image.open(cp).convert("RGB")
    r = requests.get("https://api.pexels.com/v1/search",
                     headers={"Authorization": api_key},
                     params={"query": query, "per_page": 1, "orientation": "portrait" if h >= w else "landscape"},
                     timeout=20)
    r.raise_for_status()
    photos = r.json().get("photos", [])
    if not photos:
        raise RuntimeError(f"no pexels result for '{query}'")
    src = requests.get(photos[0]["src"]["large2x"], timeout=20)
    img = Image.open(io.BytesIO(src.content)).convert("RGB")
    img.save(cp, quality=90)
    return img


def backdrop(w, h, scene="environment", seed=0, cfg=None):
    """High-level: pick a backdrop. Tries Pexels (if key + scene query) else Picsum."""
    cfg = cfg or {}
    query = {"environment": "nature landscape", "person": "abstract texture dark"}.get(scene)
    if cfg.get("use_pexels") and query:
        try:
            return pexels(query, w, h, cfg.get("pexels_key"))
        except Exception:
            pass
    return picsum(w, h, seed=seed)
