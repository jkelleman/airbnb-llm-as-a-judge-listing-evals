"""Command line entry point.

  python -m evals check                 Layer 1 over the seed set
  python -m evals generate              add model-written candidates (GEN_* env vars)
  python -m evals label --rater NAME    blind human labeling
  python -m evals judge [--set seed|perturb] [--version v2|v1] [--samples K]
  python -m evals pairwise
  python -m evals report [--labels human|intent]
  python -m evals all                   check + judge (v2, v1, perturb) + pairwise + report
"""

import argparse
import csv
import json
import random
import sys
import time

from . import judges as J
from .checks import check
from .client import from_env
from .config import DATA, DIMENSIONS, LABELS, RESULTS
from .data import load_candidates, load_listings, read_jsonl, standouts, judge_view, write_jsonl
from .perturb import build as build_perturbations


def all_candidates():
    cands = load_candidates()
    gen = DATA / "generated.jsonl"
    if gen.exists():
        cands += read_jsonl(gen)
    return cands


def good_ids(cands):
    """Known-good highlights to perturb: author intent passes on every dimension
    and Layer 1 is clean. Once human labels exist, human consensus is used instead."""
    from .data import consensus, load_labels
    human = consensus(load_labels())
    listings = load_listings()
    out = set()
    for c in cands:
        lab = human.get(c["candidate_id"]) or c.get("author_intent")
        if not lab or not all(lab.get(d) == 1 for d in DIMENSIONS):
            continue
        if not any(f["severity"] == "hard" for f in check(c["text"], listings[c["listing_id"]])):
            out.add(c["candidate_id"])
    return out


def cmd_check(args):
    listings = load_listings()
    rows = []
    for c in all_candidates():
        f = check(c["text"], listings[c["listing_id"]])
        rows.append({"candidate_id": c["candidate_id"], "findings": f})
    write_jsonl(RESULTS / "layer1.jsonl", rows)
    flagged = [r for r in rows if r["findings"]]
    print(f"Layer 1: {len(flagged)}/{len(rows)} highlights flagged -> results/layer1.jsonl")


def cmd_generate(args):
    gen = from_env("GEN")
    listings = load_listings()
    rows = []
    for lid, l in listings.items():
        for s in range(args.n):
            text = gen.complete(J.render("generator", l), sample=s).strip()
            rows.append({"candidate_id": f"{lid}-g{s}", "listing_id": lid, "text": text,
                         "source": f"{gen.provider}:{gen.model}"})
    write_jsonl(DATA / "generated.jsonl", rows)
    print(f"wrote {len(rows)} generated candidates -> data/generated.jsonl")


def cmd_judge(args):
    client = from_env("JUDGE")
    gen_path = DATA / "generated.jsonl"
    if gen_path.exists():
        srcs = {r["source"].split(":")[0] for r in read_jsonl(gen_path)}
        if client.family in srcs:
            print(f"WARNING: judge provider '{client.family}' also generated candidates. "
                  "Use a different model family to avoid self-preference.", file=sys.stderr)
    listings = load_listings()
    cands = all_candidates()
    if args.set == "perturb":
        cands = build_perturbations(cands, listings, good_ids(cands))
        write_jsonl(RESULTS / "perturbations.jsonl", cands)
    out = []
    for i, c in enumerate(cands):
        listing = listings[c["listing_id"]]
        for s in range(args.samples):
            if args.version == "v1":
                r = J.v1_monolithic(client, listing, c["text"], s)
            else:
                r = J.evaluate(client, listing, c["text"], s)
            out.append({"candidate_id": c["candidate_id"], "sample": s, "text": c["text"], **r,
                        **{k: c[k] for k in ("perturbation", "should_fail", "expected_layer", "source_id") if k in c}})
        if sys.stderr.isatty():
            print(f"\r{args.version} {args.set}: {i + 1}/{len(cands)}", end="", file=sys.stderr)
    print(file=sys.stderr)
    meta = {"provider": client.provider, "model": client.model, "temperature": client.temperature,
            "samples": args.samples, "version": args.version, "set": args.set,
            "prompt_versions": {n: J.prompt_version(n) for n in
                                (["v1_monolithic"] if args.version == "v1" else list(J.JUDGES))},
            "run_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    path = RESULTS / f"judge_{args.set}_{args.version}.jsonl"
    write_jsonl(path, out)
    (RESULTS / f"judge_{args.set}_{args.version}.meta.json").write_text(json.dumps(meta, indent=2))
    print(f"-> {path.relative_to(RESULTS.parent)}")


def cmd_pairwise(args):
    client = from_env("JUDGE")
    listings = load_listings()
    by_listing = {}
    for c in load_candidates():
        by_listing.setdefault(c["listing_id"], []).append(c)
    out = []
    for lid, cs in by_listing.items():
        if len(cs) < 2:
            continue
        a, b = cs[0], cs[1]
        r = J.pairwise(client, listings[lid], a["text"], b["text"])
        out.append({"listing_id": lid, "a": a["candidate_id"], "b": b["candidate_id"], **r})
    write_jsonl(RESULTS / "pairwise.jsonl", out)
    print(f"pairwise: {len(out)} pairs -> results/pairwise.jsonl")


def cmd_label(args):
    LABELS.mkdir(parents=True, exist_ok=True)
    path = LABELS / f"{args.rater}.csv"
    done = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            done = {r["candidate_id"] for r in csv.DictReader(f)}
    listings = load_listings()
    cands = [c for c in all_candidates() if c["candidate_id"] not in done]
    random.Random(args.rater).shuffle(cands)  # order differs by rater; pairs never adjacent by design
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["candidate_id", *DIMENSIONS, "notes"])
        if new:
            w.writeheader()
        print("Label each highlight 1 (pass) or 0 (fail) per docs/labeling_guide.md. q to quit.\n")
        for i, c in enumerate(cands):
            l = listings[c["listing_id"]]
            print("=" * 72)
            print(f"[{i + 1}/{len(cands)}] {c['candidate_id']}")
            print(json.dumps(judge_view(l), indent=1, ensure_ascii=False))
            print("Standouts:", "; ".join(standouts(l)))
            print(f"\nHIGHLIGHT: {c['text']}\n")
            rec = {"candidate_id": c["candidate_id"]}
            for d in DIMENSIONS:
                while True:
                    v = input(f"  {d} (0/1): ").strip()
                    if v == "q":
                        return
                    if v in ("0", "1"):
                        rec[d] = v
                        break
            rec["notes"] = input("  notes (optional): ").strip()
            w.writerow(rec)
            f.flush()


def cmd_report(args):
    from .report import build
    build(label_source=args.labels)


def cmd_all(args):
    cmd_check(args)
    for v, s in (("v2", "seed"), ("v1", "seed"), ("v2", "perturb")):
        args.version, args.set = v, s
        cmd_judge(args)
    cmd_pairwise(args)
    args.labels = getattr(args, "labels", "auto")
    cmd_report(args)


def main():
    p = argparse.ArgumentParser(prog="evals")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    g = sub.add_parser("generate"); g.add_argument("--n", type=int, default=1); g.set_defaults(fn=cmd_generate)
    l = sub.add_parser("label"); l.add_argument("--rater", required=True); l.set_defaults(fn=cmd_label)
    j = sub.add_parser("judge")
    j.add_argument("--set", choices=["seed", "perturb"], default="seed")
    j.add_argument("--version", choices=["v1", "v2"], default="v2")
    j.add_argument("--samples", type=int, default=1)
    j.set_defaults(fn=cmd_judge)
    sub.add_parser("pairwise").set_defaults(fn=cmd_pairwise)
    r = sub.add_parser("report"); r.add_argument("--labels", choices=["auto", "human", "intent"], default="auto")
    r.set_defaults(fn=cmd_report)
    a = sub.add_parser("all"); a.add_argument("--samples", type=int, default=1)
    a.add_argument("--labels", choices=["auto", "human", "intent"], default="auto")
    a.set_defaults(fn=cmd_all)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
