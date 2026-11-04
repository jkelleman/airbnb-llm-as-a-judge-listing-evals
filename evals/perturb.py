"""Perturbation tests: inject a known defect into a known-good highlight and check
whether the stack catches it. Ground truth comes from construction, not opinion,
so this measures sensitivity directly. Controls (unchanged highlights) measure
false alarms.

Each perturbation returns the new text, or None when it doesn't apply to that highlight.
"""

import re

from .config import COMMODITY

UNLISTED_POOL = ["hot tub", "sauna", "heated pool", "fireplace", "home gym", "ocean view"]
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
         9: "nine", 10: "ten", 12: "twelve", 15: "15", 18: "18", 20: "20", 22: "22"}
NUMS = {v: k for k, v in WORDS.items()}


def _minutes(tok):
    return int(tok) if tok.isdigit() else NUMS.get(tok.lower())


def unlisted_amenity(text, listing):
    blob = " ".join(listing.get("features", []) + listing.get("amenities", []) + listing.get("views", [])).lower()
    options = [x for x in UNLISTED_POOL if x.split()[-1] not in blob]
    if not options:
        return None
    extra = options[int(listing["listing_id"][1:]) % len(options)]  # rotate, deterministically
    if " with " not in text:
        return None
    return text.replace(" with ", f" with a {extra}, ", 1)


_WALK = re.compile(r"\b(?:an? )?(\w+)[- ]minute walk (?:from|to)|\b(\w+) minutes on foot from", re.I)


def distance_compression(text, listing):
    m = _WALK.search(text)
    if not m:
        return None
    mins = _minutes(m.group(1) or m.group(2))
    if not mins or mins <= 2:
        return None
    return text[:m.start()] + "steps from" + text[m.end():]


_DRIVE = re.compile(r"\b(\w+) minutes by car from", re.I)


def drive_as_walk(text, listing):
    m = _DRIVE.search(text)
    if not m:
        return None
    n = _minutes(m.group(1))
    if not n:
        return None
    article = "an" if str(n).startswith("8") or n in (11, 18) else "a"
    return text[:m.start()] + f"{article} {n}-minute walk from" + text[m.end():]


def shared_to_private(text, listing):
    t = re.sub(r"\ba ([\w -]+?) shared with the main house", r"a private \1", text)
    t = t.replace("the building's", "a private").replace(" a shared ", " a private ")
    return t if t != text else None


def frontage_claim(text, listing):
    if listing.get("water_frontage") or not re.match(r"^An? ", text):
        return None
    return re.sub(r"^An? ", "A waterfront ", text, count=1)


def commodity_checklist(text, listing):
    no_article = {"Wi-Fi", "free parking", "paid parking", "street parking", "garage parking", "air conditioning"}
    present = [a if a in no_article else f"a {a}"
               for a in listing.get("amenities", []) if a in COMMODITY][:3]
    if len(present) < 2:
        return None
    items = ", ".join(present[:-1]) + f", and {present[-1]}" if len(present) > 2 else " and ".join(present)
    beds = listing["bedrooms"]
    return f"A {WORDS.get(beds, beds)}-bedroom home with {items}."


def salesy_prefix(text, listing):
    """Puffery the cliche regex does NOT know about: only the voice judge can catch it."""
    if not re.match(r"^An? ", text):
        return None
    return "Prepare to fall in love with " + text[0].lower() + text[1:]


def hedge(text, listing):
    if " with " not in text:
        return None
    return text.replace(" with ", " that may possibly offer ", 1)


def control(text, listing):
    return text


# name -> (function, dimension that should fail, layer expected to catch it)
PERTURBATIONS = {
    "unlisted_amenity": (unlisted_amenity, "faithfulness", "judge"),
    "distance_compression": (distance_compression, "faithfulness", "judge"),
    "drive_as_walk": (drive_as_walk, "faithfulness", "judge"),
    "shared_to_private": (shared_to_private, "faithfulness", "judge"),
    "frontage_claim": (frontage_claim, "faithfulness", "layer1"),
    "commodity_checklist": (commodity_checklist, "salience", "judge"),
    "salesy_prefix": (salesy_prefix, "voice", "judge"),
    "hedge": (hedge, "voice", "judge"),
    "control": (control, None, None),
}


def build(candidates, listings, good_ids):
    out = []
    for c in candidates:
        if c["candidate_id"] not in good_ids:
            continue
        listing = listings[c["listing_id"]]
        for name, (fn, dim, layer) in PERTURBATIONS.items():
            new = fn(c["text"], listing)
            if new is None:
                continue
            out.append({"candidate_id": f"{c['candidate_id']}~{name}", "listing_id": c["listing_id"],
                        "source_id": c["candidate_id"], "perturbation": name, "text": new,
                        "should_fail": dim, "expected_layer": layer})
    return out
