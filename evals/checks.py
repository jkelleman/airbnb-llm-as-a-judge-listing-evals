"""Layer 1: deterministic checks. Fast, free, and exact.

Anything a regex or a counter can decide is decided here, never by an LLM.
Each finding is (error_type, detail, severity, dimension):
  severity "hard" = automatic fail for that dimension
  severity "soft" = flag for review; known to have false positives and negatives
"""

import json
import re

from .config import (CLICHES, FRONTAGE_WORDS, INTERNAL_TERMS, MAX_CHARS,
                     MAX_SENTENCES, MIN_CHARS)

EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U0001F900-\U0001F9FF️]"
)
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
}


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text.strip())
    return [p for p in parts if p]


def numbers_in(text):
    found = set()
    for m in re.finditer(r"\d+(?:\.\d+)?", text):
        v = float(m.group())
        found.add(int(v) if v.is_integer() else v)
    for w in re.findall(r"[a-z]+", text.lower()):
        if w in NUMBER_WORDS:
            found.add(NUMBER_WORDS[w])
    return found


def check(text, listing=None):
    findings = []

    def add(kind, detail, severity="hard", dim="format"):
        findings.append({"error_type": kind, "detail": detail, "severity": severity, "dimension": dim})

    n = len(text)
    if n > MAX_CHARS:
        add("too_long", f"{n} chars > {MAX_CHARS}")
    if n < MIN_CHARS:
        add("too_short", f"{n} chars < {MIN_CHARS}")
    if len(sentences(text)) > MAX_SENTENCES:
        add("too_many_sentences", f"{len(sentences(text))} sentences > {MAX_SENTENCES}")
    if "!" in text or "?" in text:
        add("bad_punctuation", "uses ! or ?")
    if not text.rstrip().endswith("."):
        add("no_final_period", "must end with a period")
    if EMOJI.search(text):
        add("emoji", "contains emoji")
    if "\n" in text or re.search(r"^\s*[-*•]", text) or '"' in text:
        add("formatting", "newline, bullet, or quotation mark")

    low = text.lower()
    for t in INTERNAL_TERMS:
        if re.search(rf"\b{re.escape(t)}\b", low):
            add("internal_term", t, dim="voice")
    for c in CLICHES:
        if re.search(rf"\b{re.escape(c)}\b", low):
            add("cliche", c, dim="voice")

    if listing is not None:
        if not listing.get("water_frontage"):
            for w in FRONTAGE_WORDS:
                if w in low:
                    add("unsupported_frontage", f"'{w}' but data has no water frontage", dim="faithfulness")
        # Soft numeric grounding: every number in the text should appear somewhere in the data.
        # Known blind spot: a wrong number that happens to occur elsewhere in the record passes.
        data_nums = numbers_in(json.dumps(listing, ensure_ascii=False))
        missing = sorted(numbers_in(text) - data_nums, key=str)
        if missing:
            add("ungrounded_number", f"{missing} not found in listing data", severity="soft", dim="faithfulness")

    return findings


def summarize(findings):
    """Per-dimension hard pass/fail from Layer 1 (None = no opinion)."""
    out = {"format": 1}
    for f in findings:
        if f["severity"] == "hard":
            out[f["dimension"]] = 0
    return out
