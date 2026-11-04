"""Shared constants. The content rules live here as data, so the guideline doc,
the programmatic checks, and the judge prompts all read from one source."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PROMPTS = ROOT / "prompts"
RESULTS = ROOT / "results"
LABELS = DATA / "labels"
CACHE = RESULTS / "cache"

DIMENSIONS = ["faithfulness", "salience", "voice"]

# --- Format spec for a listing highlight (Layer 1, deterministic) ---
MIN_CHARS = 60
MAX_CHARS = 200
MAX_SENTENCES = 2

# Words guests never see in product language.
# "property" was removed after the first Layer 1 run: it flagged a good highlight
# ("an apple orchard on the property"), where it means land, not inventory.
# Context-dependent words belong to the voice judge, not a regex.
INTERNAL_TERMS = ["listing", "unit", "inventory", "host-provided", "amenity list"]

# Stock phrases that add no information. Matched case-insensitively on word boundaries.
CLICHES = [
    "hidden gem", "oasis", "paradise", "stunning", "breathtaking", "nestled", "boasts",
    "unforgettable", "ultimate", "luxury", "luxurious", "amazing", "perfect getaway",
    "in the heart of", "slice of heaven", "home away from home", "must-see", "unmatched",
    "rustic charm", "escape to",
]

# Relative distance language and the maximum walk (minutes) each phrase may describe.
# Used by the faithfulness judge prompt and documented in docs/content_principles.md.
DISTANCE_PHRASES = [
    ("steps from / next to / right on", 2),
    ("around the corner / a few blocks", 5),
    ("a short walk", 10),
    ("near / close to", 15),
]
FRONTAGE_WORDS = ["oceanfront", "beachfront", "waterfront", "lakefront", "riverfront", "on the water"]

# Amenities that never count as a standout, however rare they are in the dataset.
COMMODITY = {
    "Wi-Fi", "kitchen", "kitchenette", "washer", "dryer", "free parking", "paid parking",
    "street parking", "garage parking", "air conditioning", "dedicated workspace",
    "smart TV", "coffee maker", "composting toilet",
}
