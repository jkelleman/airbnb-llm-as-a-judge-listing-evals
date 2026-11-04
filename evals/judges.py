"""Layer 2: virtual judges. One judge per dimension, each returning a binary score
plus typed errors. Faithfulness is scored in code from claim-level verdicts, so
the judge never gets to 'round up' a summary with one bad claim."""

import json

from .checks import check, summarize
from .client import parse_json
from .config import PROMPTS
from .data import judge_view, standouts


def load_prompt(name):
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def prompt_version(name):
    head = load_prompt(name).splitlines()[0]
    return head.split("version:")[1].split("|")[0].strip(" ->") if "version:" in head else "?"


def render(name, listing, highlight=None, **extra):
    p = load_prompt(name)
    p = p.replace("<<LISTING>>", json.dumps(judge_view(listing), indent=2, ensure_ascii=False))
    if highlight is not None:
        p = p.replace("<<HIGHLIGHT>>", highlight)
    p = p.replace("<<STANDOUTS>>", json.dumps(standouts(listing), ensure_ascii=False))
    for k, v in extra.items():
        p = p.replace(f"<<{k}>>", v)
    return p


def _safe(fn):
    def wrapped(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception as e:  # malformed JSON, API error: recorded, never silently scored
            return {"score": None, "errors": [["judge_error", str(e)[:200]]], "raw": None}
    return wrapped


@_safe
def faithfulness(client, listing, text, sample=0):
    raw = client.complete(render("faithfulness", listing, text), sample)
    claims = parse_json(raw)["claims"]
    bad = [c for c in claims if c.get("verdict") in ("unsupported", "contradicted")]
    return {"score": 0 if bad else 1,
            "errors": [[c["verdict"], c.get("claim", "")] for c in bad],
            "claims": claims, "raw": raw}


@_safe
def salience(client, listing, text, sample=0):
    raw = client.complete(render("salience", listing, text), sample)
    j = parse_json(raw)
    return {"score": int(j["score"]), "errors": j.get("errors", []),
            "covered": j.get("covered_standouts", []), "raw": raw}


@_safe
def voice(client, listing, text, sample=0):
    raw = client.complete(render("voice", listing, text), sample)
    j = parse_json(raw)
    return {"score": int(j["score"]), "errors": j.get("errors", []), "raw": raw}


JUDGES = {"faithfulness": faithfulness, "salience": salience, "voice": voice}


@_safe
def v1_monolithic(client, listing, text, sample=0):
    """Baseline. Its 1-3 scales are mapped to pass/fail so it can be compared with v2:
    salience passes only at density 3, and voice only at clarity 3."""
    raw = client.complete(render("v1_monolithic", listing, text), sample)
    s = parse_json(raw)["scores"]
    return {"scores": {"faithfulness": int(s["factual_fidelity"]),
                       "salience": int(int(s["attribute_density"]) == 3),
                       "voice": int(int(s["ux_clarity"]) == 3)},
            "raw_scores": s, "raw": raw}


def evaluate(client, listing, text, sample=0):
    """Full v2 stack for one highlight: Layer 1 gates, then one judge per dimension."""
    findings = check(text, listing)
    l1 = summarize(findings)
    out = {"layer1": findings, "layer1_summary": l1, "judges": {}, "final": {}}
    for dim, fn in JUDGES.items():
        r = fn(client, listing, text, sample)
        out["judges"][dim] = r
        score = r["score"]
        if l1.get(dim) == 0:          # a hard Layer 1 failure decides the dimension
            score = 0
        out["final"][dim] = score
    out["final"]["format"] = l1["format"]
    scores = [v for v in out["final"].values() if v is not None]
    out["final"]["overall"] = int(all(scores)) if len(scores) == len(out["final"]) else None
    return out


@_safe
def pairwise(client, listing, a, b, sample=0):
    """Runs both orders. A verdict counts only if it survives the swap."""
    r1 = parse_json(client.complete(render("pairwise", listing, A=a, B=b), sample))["winner"]
    r2 = parse_json(client.complete(render("pairwise", listing, A=b, B=a), sample))["winner"]
    flip = {"A": "B", "B": "A", "tie": "tie"}
    consistent = r1 == flip[r2]
    return {"forward": r1, "swapped": r2, "consistent": consistent,
            "winner": r1 if consistent else "tie"}
