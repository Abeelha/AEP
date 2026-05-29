"""Scene understanding: faces, portrait orientation, optional subject matte.

Uses OpenCV Haar cascades (bundled with opencv-python, no download).
Subject segmentation uses `rembg` if installed; otherwise returns None and the
compositor falls back to a radial/box mask.
"""
import numpy as np
from PIL import Image

try:
    import cv2
    _FACE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    _PROFILE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
except Exception:  # pragma: no cover
    cv2 = None
    _FACE = _PROFILE = None

_REMBG = None
def _rembg_session():
    global _REMBG
    if _REMBG is None:
        try:
            from rembg import new_session
            _REMBG = new_session("u2net")
        except Exception:
            _REMBG = False
    return _REMBG


def detect_faces(img):
    if _FACE is None:
        return []
    gray = cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    boxes = list(_FACE.detectMultiScale(gray, 1.15, 5, minSize=(40, 40)))
    if _PROFILE is not None and not boxes:
        boxes = list(_PROFILE.detectMultiScale(gray, 1.15, 5, minSize=(40, 40)))
    return [tuple(int(v) for v in b) for b in boxes]


def subject_mask(img):
    """Return float mask (H,W) 1=subject 0=background, or None if unavailable."""
    sess = _rembg_session()
    if not sess:
        return None
    try:
        from rembg import remove
        cut = remove(img.convert("RGBA"), session=sess)
        a = np.asarray(cut)[..., 3].astype(np.float32) / 255.0
        return a
    except Exception:
        return None


def analyze(img):
    """Return scene dict driving the edit recipe."""
    w, h = img.size
    faces = detect_faces(img)
    has_subject = len(faces) > 0
    mask = subject_mask(img) if has_subject else None
    return {
        "w": w, "h": h,
        "portrait": h >= w,
        "n_faces": len(faces),
        "faces": faces,
        "scene": "person" if has_subject else "environment",
        "has_mask": mask is not None,
        "mask": mask,
    }
