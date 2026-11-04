"""Agreement and bias metrics. Standard library only, so every number can be audited."""

import random
from collections import Counter


def pairs(a, b):
    """Aligned (x, y) for keys labeled in both dicts, with no None values."""
    return [(a[k], b[k]) for k in a if k in b and a[k] is not None and b[k] is not None]


def percent_agreement(xy):
    return sum(x == y for x, y in xy) / len(xy) if xy else None


def cohen_kappa(xy):
    if not xy:
        return None
    n = len(xy)
    po = percent_agreement(xy)
    cx, cy = Counter(x for x, _ in xy), Counter(y for _, y in xy)
    pe = sum(cx[c] * cy[c] for c in set(cx) | set(cy)) / (n * n)
    if pe == 1:
        return 1.0 if po == 1 else 0.0
    return (po - pe) / (1 - pe)


def krippendorff_alpha_nominal(units):
    """units: list of lists of values per item (any number of raters, missing omitted)."""
    units = [u for u in units if len(u) >= 2]
    if not units:
        return None
    coincid = Counter()
    for u in units:
        m = len(u)
        for i, a in enumerate(u):
            for j, b in enumerate(u):
                if i != j:
                    coincid[(a, b)] += 1 / (m - 1)
    n_c = Counter()
    for (a, _), v in coincid.items():
        n_c[a] += v
    n = sum(n_c.values())
    do = sum(v for (a, b), v in coincid.items() if a != b)
    de = sum(n_c[a] * n_c[b] for a in n_c for b in n_c if a != b) / (n - 1)
    if de == 0:
        return 1.0
    return 1 - do / de


def confusion(xy, positive=0):
    """Confusion counts treating FAIL (0) as the positive class: the thing we must catch.
    x = human (truth), y = judge."""
    tp = sum(1 for x, y in xy if x == positive and y == positive)
    fn = sum(1 for x, y in xy if x == positive and y != positive)
    fp = sum(1 for x, y in xy if x != positive and y == positive)
    tn = sum(1 for x, y in xy if x != positive and y != positive)
    recall = tp / (tp + fn) if tp + fn else None
    precision = tp / (tp + fp) if tp + fp else None
    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "fail_recall": recall, "fail_precision": precision}


def bootstrap_ci(xy, stat=cohen_kappa, n=2000, seed=7):
    """95% percentile interval. With 60 items these are wide, and that is the point."""
    if len(xy) < 5:
        return (None, None)
    rng = random.Random(seed)
    vals = sorted(v for v in (stat([rng.choice(xy) for _ in xy]) for _ in range(n)) if v is not None)
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def agreement_report(truth, pred):
    xy = pairs(truth, pred)
    lo, hi = bootstrap_ci(xy)
    return {"n": len(xy), "agreement": percent_agreement(xy), "kappa": cohen_kappa(xy),
            "kappa_ci95": [lo, hi], **confusion(xy)}


def length_bias(items):
    """items: (length, human, judge). Among items humans call FAIL, do longer ones
    get passed more often? Compares judge pass rate in the shorter vs. longer half."""
    fails = sorted((l, j) for l, h, j in items if h == 0 and j is not None)
    if len(fails) < 4:
        return None
    half = len(fails) // 2
    short, long_ = fails[:half], fails[half:]
    rate = lambda xs: sum(j for _, j in xs) / len(xs)
    return {"n_human_fails": len(fails), "judge_pass_rate_shorter": rate(short),
            "judge_pass_rate_longer": rate(long_), "median_split_chars": fails[half][0]}


def test_retest(runs):
    """runs: {item: [score per sample]}. Share of items where every sample agreed."""
    multi = [v for v in runs.values() if len(v) > 1 and None not in v]
    if not multi:
        return None
    return sum(len(set(v)) == 1 for v in multi) / len(multi)
