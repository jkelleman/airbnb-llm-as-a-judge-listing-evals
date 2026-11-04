"""Builds results/report.md, results/metrics.json, and results/disagreements.md
from whatever runs exist. Sections with no data are skipped, not faked."""

import json
from collections import Counter, defaultdict

from .config import DIMENSIONS, RESULTS
from .data import consensus, intent_labels, load_candidates, load_labels, read_jsonl
from . import metrics as M


def _f(x, pct=False):
    if x is None:
        return "–"
    return f"{x:.0%}" if pct else f"{x:.2f}"


def _load(name):
    p = RESULTS / name
    return read_jsonl(p) if p.exists() else []


def _meta(name):
    p = RESULTS / name
    return json.loads(p.read_text()) if p.exists() else None


def build(label_source="auto"):
    cands = load_candidates()
    texts = {c["candidate_id"]: c["text"] for c in cands}
    raters = load_labels()
    if label_source == "human" or (label_source == "auto" and raters):
        truth, truth_name = consensus(raters), f"human consensus ({len(raters)} rater(s))"
    else:
        truth, truth_name = intent_labels(cands), "AUTHOR INTENT (not human-validated)"

    lines, metrics = [], {"label_source": truth_name}
    meta = _meta("judge_seed_v2.meta.json")
    mock = meta and meta["provider"] == "mock"
    lines.append("# Listing-highlight evals: run report\n")
    if mock:
        lines.append("> **MOCK RUN.** The judge was the offline mock, which returns seeded random "
                     "answers. Every judge number below is noise. This report proves the pipeline runs, nothing more.\n")
    if meta:
        lines.append(f"Judge: `{meta['provider']}/{meta['model']}` · temperature {meta['temperature']} · "
                     f"samples {meta['samples']} · prompts {meta['prompt_versions']} · {meta['run_at']}\n")
    lines.append(f"Labels: **{truth_name}**\n")

    # 1. Layer 1
    l1 = _load("layer1.jsonl")
    if l1:
        c = Counter(f["error_type"] for r in l1 for f in r["findings"])
        lines.append("## 1. Layer 1 (deterministic checks)\n")
        lines.append(f"{sum(1 for r in l1 if r['findings'])} of {len(l1)} highlights flagged.\n")
        lines.append("| Error type | Count |\n|---|---|")
        lines += [f"| {k} | {v} |" for k, v in c.most_common()]
        lines.append("")
        metrics["layer1"] = dict(c)

    # 2. Inter-rater
    if len(raters) >= 2:
        lines.append("## 2. Human agreement (the ceiling for any judge)\n")
        lines.append("| Dimension | Items | Krippendorff's α |\n|---|---|---|")
        metrics["inter_rater"] = {}
        for d in DIMENSIONS:
            units = defaultdict(list)
            for rows in raters.values():
                for cid, rec in rows.items():
                    if d in rec:
                        units[cid].append(rec[d])
            a = M.krippendorff_alpha_nominal(list(units.values()))
            metrics["inter_rater"][d] = a
            lines.append(f"| {d} | {sum(1 for u in units.values() if len(u) > 1)} | {_f(a)} |")
        lines.append("")

    # 3. Judge vs labels
    v2 = [r for r in _load("judge_seed_v2.jsonl") if r["sample"] == 0]
    v1 = [r for r in _load("judge_seed_v1.jsonl") if r["sample"] == 0]
    if v2 or v1:
        lines.append(f"## 3. Judge vs. labels ({truth_name})\n")
        lines.append("FAIL is the positive class, so *fail recall* = share of real failures the judge caught. "
                     "Kappa 95% CIs are bootstrapped; with ~60 items they are wide.\n")
        lines.append("| Dimension | System | n | Agreement | κ (95% CI) | Fail recall | Fail precision |")
        lines.append("|---|---|---|---|---|---|---|")
        metrics["agreement"] = {}
        for d in DIMENSIONS:
            truth_d = {k: v[d] for k, v in truth.items() if d in v}
            systems = []
            if v1:
                systems.append(("v1 monolithic", {r["candidate_id"]: r.get("scores", {}).get(d) for r in v1}))
            if v2:
                systems.append(("v2 judge only", {r["candidate_id"]: r["judges"][d]["score"] for r in v2}))
                systems.append(("v2 + Layer 1", {r["candidate_id"]: r["final"][d] for r in v2}))
            for name, pred in systems:
                a = M.agreement_report(truth_d, pred)
                metrics["agreement"][f"{d}/{name}"] = a
                lo, hi = a["kappa_ci95"]
                lines.append(f"| {d} | {name} | {a['n']} | {_f(a['agreement'], True)} | {_f(a['kappa'])} "
                             f"({_f(lo)}–{_f(hi)}) | {_f(a['fail_recall'], True)} | {_f(a['fail_precision'], True)} |")
        lines.append("")

    # 4. Perturbations
    pert = [r for r in _load("judge_perturb_v2.jsonl") if r["sample"] == 0]
    if pert:
        lines.append("## 4. Perturbation tests (ground truth by construction)\n")
        lines.append("Each row injects one known defect into known-good highlights. "
                     "*Caught* = the dimension that should fail was scored 0 by the full stack.\n")
        lines.append("| Perturbation | Should fail | Expected layer | n | Caught |\n|---|---|---|---|---|")
        by = defaultdict(list)
        for r in pert:
            by[r["perturbation"]].append(r)
        metrics["perturbations"] = {}
        for name, rows in sorted(by.items()):
            if name == "control":
                continue
            d = rows[0]["should_fail"]
            caught = [r["final"][d] == 0 for r in rows if r["final"][d] is not None]
            rate = sum(caught) / len(caught) if caught else None
            metrics["perturbations"][name] = {"n": len(rows), "caught": rate}
            lines.append(f"| {name} | {d} | {rows[0]['expected_layer']} | {len(rows)} | {_f(rate, True)} |")
        ctrl = by.get("control", [])
        if ctrl:
            lines.append("\nFalse alarms on unchanged known-good highlights (controls):\n")
            lines.append("| Dimension | n | Flagged as fail |\n|---|---|---|")
            metrics["control_false_alarm"] = {}
            for d in DIMENSIONS:
                vals = [r["final"][d] for r in ctrl if r["final"][d] is not None]
                fa = sum(v == 0 for v in vals) / len(vals) if vals else None
                metrics["control_false_alarm"][d] = fa
                lines.append(f"| {d} | {len(vals)} | {_f(fa, True)} |")
        lines.append("")

    # 5. Length bias
    if v2:
        lines.append("## 5. Length bias\n")
        lines.append("Among highlights the labels call FAIL, does the judge let longer ones through more often?\n")
        lines.append("| Dimension | Labeled fails | Judge pass rate, shorter half | Judge pass rate, longer half |")
        lines.append("|---|---|---|---|")
        metrics["length_bias"] = {}
        for d in DIMENSIONS:
            items = [(len(texts.get(r["candidate_id"], r["text"])), truth.get(r["candidate_id"], {}).get(d),
                      r["judges"][d]["score"]) for r in v2]
            lb = M.length_bias(items)
            metrics["length_bias"][d] = lb
            if lb:
                lines.append(f"| {d} | {lb['n_human_fails']} | {_f(lb['judge_pass_rate_shorter'], True)} | "
                             f"{_f(lb['judge_pass_rate_longer'], True)} |")
        lines.append("")

    # 6. Test-retest
    allv2 = _load("judge_seed_v2.jsonl")
    if allv2 and max(r["sample"] for r in allv2) > 0:
        lines.append("## 6. Consistency across repeated runs\n")
        lines.append("| Dimension | Items with identical verdicts across samples |\n|---|---|")
        metrics["test_retest"] = {}
        for d in DIMENSIONS:
            runs = defaultdict(list)
            for r in allv2:
                runs[r["candidate_id"]].append(r["judges"][d]["score"])
            t = M.test_retest(runs)
            metrics["test_retest"][d] = t
            lines.append(f"| {d} | {_f(t, True)} |")
        lines.append("")

    # 7. Pairwise
    pw = _load("pairwise.jsonl")
    if pw:
        cons = sum(r.get("consistent") is True for r in pw) / len(pw)
        lines.append("## 7. Pairwise ranking\n")
        lines.append(f"Position consistency (same verdict after swapping A/B): **{_f(cons, True)}** of {len(pw)} pairs. "
                     "Inconsistent pairs are scored as ties.\n")
        overall = {cid: int(all(v.get(d) == 1 for d in DIMENSIONS)) for cid, v in truth.items()
                   if all(d in v for d in DIMENSIONS)}
        decisive = [r for r in pw if r["a"] in overall and r["b"] in overall and overall[r["a"]] != overall[r["b"]]]
        if decisive:
            right = sum((r["winner"] == "A") == (overall[r["a"]] == 1) and r["winner"] != "tie" for r in decisive)
            lines.append(f"On {len(decisive)} pairs where the labels pass exactly one highlight, "
                         f"the judge picked that one {_f(right / len(decisive), True)} of the time.\n")
            metrics["pairwise"] = {"position_consistency": cons, "decisive_pairs": len(decisive),
                                   "picked_labeled_winner": right / len(decisive)}

    (RESULTS / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (RESULTS / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # Disagreements: the file you actually read
    if v2:
        out = ["# Judge vs. label disagreements\n",
               f"Labels: {truth_name}. Read these before changing any prompt.\n"]
        for r in v2:
            lab = truth.get(r["candidate_id"], {})
            diffs = [d for d in DIMENSIONS if d in lab and r["final"][d] is not None and r["final"][d] != lab[d]]
            if not diffs:
                continue
            out.append(f"## {r['candidate_id']}\n\n> {r['text']}\n")
            for d in diffs:
                errs = r["judges"][d].get("errors", [])
                l1 = [f"{f['error_type']}: {f['detail']}" for f in r["layer1"] if f["dimension"] == d]
                out.append(f"- **{d}**: label {lab[d]}, system {r['final'][d]}. "
                           f"Judge errors: {errs or 'none'}{'; Layer 1: ' + str(l1) if l1 else ''}")
            out.append("")
        (RESULTS / "disagreements.md").write_text("\n".join(out), encoding="utf-8")
    print("-> results/report.md, results/metrics.json, results/disagreements.md")
