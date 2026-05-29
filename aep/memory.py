"""Preference memory: log every produced variant, let the user rate them, and
roll an aggregate digest so the system (and the AI assistant) learns which
recipes trend better/worse over time.

- ratings.jsonl : append-only event log (git-ignored, local history)
- MEMORY.md     : human + AI readable digest, regenerated from the log
"""
import os
import json
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM_DIR = os.path.join(ROOT, "memory")
LOG = os.path.join(MEM_DIR, "ratings.jsonl")
DIGEST = os.path.join(MEM_DIR, "MEMORY.md")
os.makedirs(MEM_DIR, exist_ok=True)


def _append(event):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def log_batch(meta, ts):
    for v in meta.get("variants", []):
        if "file" in v:
            _append({"ts": ts, "kind": "produced", "input": os.path.basename(meta["input"]),
                     "scene": meta["scene"]["scene"], "label": v["label"]})


def rate(label_or_file, score, ts, note=""):
    """score: +1 good, -1 bad, 0 meh. label_or_file = recipe label."""
    _append({"ts": ts, "kind": "rating", "label": label_or_file, "score": int(score), "note": note})
    return rebuild_digest()


def _read():
    if not os.path.exists(LOG):
        return []
    with open(LOG, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def rebuild_digest():
    events = _read()
    produced = defaultdict(int)
    score = defaultdict(int)
    votes = defaultdict(int)
    for e in events:
        if e["kind"] == "produced":
            produced[e["label"]] += 1
        elif e["kind"] == "rating":
            score[e["label"]] += e["score"]
            votes[e["label"]] += 1
    ranked = sorted(score.items(), key=lambda kv: kv[1], reverse=True)
    lines = ["# AEP — preference memory", "",
             f"Total variants produced: {sum(produced.values())}  |  rated: {sum(votes.values())}", "",
             "## Recipe ranking (by net score)", ""]
    if ranked:
        for label, s in ranked:
            v = votes[label]; avg = s / v if v else 0
            tag = "✅ keep" if s > 0 else ("❌ drop" if s < 0 else "· neutral")
            lines.append(f"- **{label}**: net {s:+d} over {v} votes (avg {avg:+.2f}) — {tag}")
    else:
        lines.append("_No ratings yet. Rate variants with `python -m aep rate <label> <+1|-1>`._")
    lines += ["", "## Most-produced recipes", ""]
    for label, c in sorted(produced.items(), key=lambda kv: kv[1], reverse=True)[:10]:
        lines.append(f"- {label}: {c}")
    with open(DIGEST, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return DIGEST
