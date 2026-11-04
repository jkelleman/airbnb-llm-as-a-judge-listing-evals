"""Loading listings, candidates, and human labels."""

import csv
import json
from pathlib import Path

from .config import COMMODITY, DATA, DIMENSIONS, LABELS


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_listings(path=DATA / "listings.jsonl"):
    return {l["listing_id"]: l for l in read_jsonl(path)}


def load_candidates(path=DATA / "candidates.jsonl"):
    return read_jsonl(path)


def standouts(listing):
    """What makes this home worth a click: its design, distinctive features, and views.

    In production this list would come from search and booking signals (what guests
    filter on and click). Here it is derived from the structured data so the salience
    judge checks coverage against a fixed reference instead of its own taste.
    """
    out = [listing["design"]]
    out += [f for f in listing.get("features", []) if f not in COMMODITY]
    out += listing.get("views", [])
    return out


def judge_view(listing):
    """The listing as the judge sees it: structured data only, no labels or notes."""
    return {k: v for k, v in listing.items() if k != "listing_id"}


def load_labels(rater=None, path=LABELS):
    """Human labels: one CSV per rater at data/labels/<rater>.csv.

    Returns {rater: {candidate_id: {dim: 0/1, ...}}}.
    """
    out = {}
    p = Path(path)
    if not p.exists():
        return out
    for f in sorted(p.glob("*.csv")):
        name = f.stem
        if rater and name != rater:
            continue
        rows = {}
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                rec = {}
                for d in DIMENSIONS:
                    v = (r.get(d) or "").strip()
                    if v in ("0", "1"):
                        rec[d] = int(v)
                rec["notes"] = r.get("notes", "")
                rows[r["candidate_id"]] = rec
        out[name] = rows
    return out


def intent_labels(candidates):
    """Author intent as a provisional label set. Never report it as human agreement."""
    return {c["candidate_id"]: {d: c["author_intent"][d] for d in DIMENSIONS}
            for c in candidates if "author_intent" in c}


def consensus(labels_by_rater):
    """Majority label per item and dimension; ties are dropped (left unlabeled)."""
    items = {}
    for rows in labels_by_rater.values():
        for cid, rec in rows.items():
            for d in DIMENSIONS:
                if d in rec:
                    items.setdefault(cid, {}).setdefault(d, []).append(rec[d])
    out = {}
    for cid, dims in items.items():
        for d, votes in dims.items():
            ones = sum(votes)
            zeros = len(votes) - ones
            if ones != zeros:
                out.setdefault(cid, {})[d] = int(ones > zeros)
    return out
