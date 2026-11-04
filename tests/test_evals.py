import json

import pytest

from evals import metrics as M
from evals.checks import check, summarize
from evals.data import load_candidates, load_listings, standouts
from evals.judges import evaluate, pairwise, render
from evals.client import Client, parse_json
from evals.perturb import PERTURBATIONS, distance_compression, drive_as_walk, shared_to_private

L = load_listings()
C = {c["candidate_id"]: c for c in load_candidates()}


# ---------- Layer 1 ----------

def types(text, lid):
    return {f["error_type"] for f in check(text, L[lid])}


def test_clean_highlight_passes():
    assert check(C["L01-a"]["text"], L["L01"]) == []


def test_layer1_catches_seeded_format_failures():
    assert {"bad_punctuation", "cliche"} <= types(C["L04-b"]["text"], "L04")
    assert "emoji" in types(C["L18-b"]["text"], "L18")
    assert "too_long" in types(C["L14-b"]["text"], "L14")
    assert "internal_term" in types(C["L30-b"]["text"], "L30")


def test_frontage_needs_data():
    assert "unsupported_frontage" in types(C["L17-b"]["text"], "L17")
    assert "unsupported_frontage" not in types("A waterfront floating home on Lake Union with two kayaks.", "L13")


def test_property_is_not_an_internal_term():
    # regression: "on the property" means land here
    assert "internal_term" not in types(C["L14-a"]["text"], "L14")


def test_numeric_check_is_soft_and_has_known_blind_spot():
    f = check("A log cabin that sleeps 11, with a sauna and a hot tub.", L["L08"])
    assert any(x["error_type"] == "ungrounded_number" and x["severity"] == "soft" for x in f)
    # "10" exists elsewhere in L08's data, so the wrong capacity slips through. Documented, by design.
    assert not any(x["error_type"] == "ungrounded_number" for x in check(C["L08-b"]["text"], L["L08"]))
    assert summarize(f).get("faithfulness") is None  # soft flags never decide a score


# ---------- Metrics ----------

def test_kappa_textbook_value():
    xy = [(1, 1)] * 20 + [(1, 0)] * 5 + [(0, 1)] * 10 + [(0, 0)] * 15
    assert M.percent_agreement(xy) == pytest.approx(0.7)
    assert M.cohen_kappa(xy) == pytest.approx(0.4)


def test_alpha_bounds():
    assert M.krippendorff_alpha_nominal([[1, 1], [0, 0], [1, 1], [0, 0]]) == pytest.approx(1.0)
    assert M.krippendorff_alpha_nominal([[1, 0], [0, 1], [1, 0], [0, 1]]) < 0


def test_alpha_handles_missing_raters():
    units = [[1, 1, 1], [0, 0], [1, 0, 1], [0, 0, 0]]
    a = M.krippendorff_alpha_nominal(units)
    assert 0 < a < 1


def test_confusion_treats_fail_as_positive():
    xy = [(0, 0), (0, 1), (1, 1), (1, 0)]
    c = M.confusion(xy)
    assert (c["tp"], c["fn"], c["fp"], c["tn"]) == (1, 1, 1, 1)
    assert c["fail_recall"] == 0.5


# ---------- Perturbations ----------

def test_distance_compression_only_when_it_lies():
    assert "steps from" in distance_compression(C["L01-a"]["text"], L["L01"])
    assert distance_compression(C["L24-a"]["text"], L["L24"]) is None  # already 2 minutes


def test_drive_as_walk():
    out = drive_as_walk(C["L14-a"]["text"], L["L14"])
    assert "an 8-minute walk from Uptown Kingston" in out


def test_shared_to_private_changes_the_fact():
    out = shared_to_private(C["L06-a"]["text"], L["L06"])
    assert "private saltwater plunge pool" in out and "shared" not in out


def test_every_perturbation_declares_target():
    for name, (_, dim, layer) in PERTURBATIONS.items():
        assert (dim is None) == (name == "control")


# ---------- Judges (offline) ----------

def test_prompts_render_without_placeholders():
    for name in ("faithfulness", "salience", "voice", "v1_monolithic"):
        p = render(name, L["L05"], "x")
        assert "<<" not in p, name
    assert "author_intent" not in render("faithfulness", L["L05"], "x")


def test_standouts_exclude_commodities():
    s = standouts(L["L28"])
    assert "smart TV" not in s and "outdoor sauna" in s


def test_parse_json_takes_last_object():
    assert parse_json('reasoning {"a": 1} then ```json\n{"b": 2}\n```') == {"b": 2}


class Scripted(Client):
    """Fake client that returns fixed replies, to test scoring logic exactly."""

    def __init__(self, replies):
        super().__init__("scripted", "scripted")
        self.replies = replies

    def complete(self, prompt, sample=0, max_tokens=1024):
        for key, reply in self.replies.items():
            if f"prompt: {key}" in prompt:
                return reply(prompt) if callable(reply) else reply
        raise KeyError(prompt[:40])


def test_one_bad_claim_fails_faithfulness():
    client = Scripted({
        "faithfulness": json.dumps({"claims": [
            {"claim": "A-frame", "verdict": "supported", "evidence": "design"},
            {"claim": "hot tub", "verdict": "unsupported", "evidence": "none"}]}),
        "salience": '{"score": 1, "errors": []}',
        "voice": '{"score": 1, "errors": []}',
    })
    r = evaluate(client, L["L01"], C["L01-b"]["text"])
    assert r["final"]["faithfulness"] == 0 and r["final"]["overall"] == 0


def test_layer1_overrides_lenient_judge():
    client = Scripted({
        "faithfulness": '{"claims": []}',
        "salience": '{"score": 1, "errors": []}',
        "voice": '{"score": 1, "errors": []}',
    })
    r = evaluate(client, L["L07"], C["L07-b"]["text"])  # "listing", "amazing"
    assert r["judges"]["voice"]["score"] == 1 and r["final"]["voice"] == 0


def test_malformed_judge_reply_is_recorded_not_scored():
    client = Scripted({"faithfulness": "no json here", "salience": '{"score": 1}', "voice": '{"score": 1}'})
    r = evaluate(client, L["L01"], C["L01-a"]["text"])
    assert r["final"]["faithfulness"] is None and r["final"]["overall"] is None


def test_pairwise_inconsistent_order_becomes_tie():
    client = Scripted({"pairwise": '{"reasoning": "", "winner": "A"}'})  # always picks first slot
    r = pairwise(client, L["L24"], C["L24-a"]["text"], C["L24-b"]["text"])
    assert r["consistent"] is False and r["winner"] == "tie"
