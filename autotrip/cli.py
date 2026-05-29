"""autotrip CLI.

    python -m autotrip once  [--input DIR] [--out DIR] [-n N]   # process existing images
    python -m autotrip watch [--input DIR] [--out DIR] [-n N]   # live folder watch
    python -m autotrip one   IMAGE [--out DIR] [-n N]           # single image
    python -m autotrip rate  LABEL +1|-1 [--note TEXT]          # rate a recipe
    python -m autotrip memory                                   # print preference digest
"""
import os
import sys
import time
import glob
import argparse
from . import pipeline, memory

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(ROOT, "input")
OUT = os.path.join(ROOT, "output")
EXTS = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp")


def _images(d):
    out = []
    for e in EXTS:
        out += glob.glob(os.path.join(d, e))
    return sorted(out)


def main(argv=None):
    p = argparse.ArgumentParser(prog="autotrip")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("once", "watch"):
        sp = sub.add_parser(name)
        sp.add_argument("--input", default=IN)
        sp.add_argument("--out", default=OUT)
        sp.add_argument("-n", type=int, default=5)

    sp = sub.add_parser("one"); sp.add_argument("image"); sp.add_argument("--out", default=OUT); sp.add_argument("-n", type=int, default=5)
    sp = sub.add_parser("rate"); sp.add_argument("label"); sp.add_argument("score", type=int); sp.add_argument("--note", default="")
    sub.add_parser("memory")

    a = p.parse_args(argv)

    if a.cmd == "once":
        os.makedirs(a.input, exist_ok=True)
        imgs = _images(a.input)
        if not imgs:
            print(f"no images in {a.input}"); return
        for fp in imgs:
            meta = pipeline.process(fp, a.out, a.n)
            memory.log_batch(meta, ts=int(time.time()))
            print(f"{os.path.basename(fp):40s} -> {len(meta['variants'])} variants ({meta['scene']['scene']})")
        memory.rebuild_digest()
        print("digest:", memory.DIGEST)

    elif a.cmd == "one":
        meta = pipeline.process(a.image, a.out, a.n)
        memory.log_batch(meta, ts=int(time.time())); memory.rebuild_digest()
        print(f"{len(meta['variants'])} variants -> {meta['dest']}")

    elif a.cmd == "watch":
        from . import watcher
        watcher.watch(a.input, a.out, a.n)

    elif a.cmd == "rate":
        d = memory.rate(a.label, a.score, ts=int(time.time()), note=a.note)
        print("updated", d)

    elif a.cmd == "memory":
        memory.rebuild_digest()
        print(open(memory.DIGEST, encoding="utf-8").read())


if __name__ == "__main__":
    main()
