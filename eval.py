import json
import os
from pathlib import Path

from dotenv import load_dotenv

from extract_json import (make_client, attempt_extract,estimate_cost_usd)

GOLDENS_DIR = Path("goldens")
FIELDS = ("owner", "task", "deadline")

def load_golden(stem):
    """Load one golden case as (notes_text, expected_dict)."""
    notes = (GOLDENS_DIR / f"{stem}.txt").read_text(
        encoding="utf-8")
    expected = json.loads(
        (GOLDENS_DIR / f"{stem}.expected.json").read_text(
            encoding="utf-8"))
    return notes, expected

def normalise(value):
    """Reduce a field to its comparable form for scoring."""
    # Formatting differences are not factual differences,
    # so casing/punctuation must not decide the score.
    text = str(value).strip().lower()
    text = " ".join(text.split())
    return text.rstrip(".")

def fields_match(expected, actual):
    """Return {field: bool} comparing one expected item to one actual item."""
    return {f: normalise(expected.get(f, ""))
        == normalise(actual.get(f, ""))
    for f in FIELDS}

def sorted_items(data):
    """Return items sorted by owner then task for stable pairing."""
    # Pairing by position alone would punish a correct
    # answer returned in a different order.
    return sorted(data.get("items", []),
                key=lambda i: (normalise(i.get("owner", "")),
                                normalise(i.get("task", ""))))

def score_case(expected, actual):
    """Score one case field by field; return (counts, totals)."""
    exp, act = sorted_items(expected), sorted_items(actual)
    counts = {f: 0 for f in FIELDS}
    # A fabricated item fails the whole case: invention is
    # the worst extractor error, so it earns no partial credit.
    if len(exp) != len(act):
        return counts, {f: len(exp) for f in FIELDS}
    for e, a in zip(exp, act):
        for f, ok in fields_match(e, a).items():
            counts[f] += int(ok)
    return counts, {f: len(exp) for f in FIELDS}

def run_eval():
    """Run every golden through the extractor and print the score table."""
    load_dotenv()
    client = make_client()
    stems = sorted(p.stem for p in GOLDENS_DIR.glob("*.txt"))
    totals = {f: 0 for f in FIELDS}
    grand, total_cost = 0, 0.0
    in_p = float(os.getenv("GEMINI_PRICE_IN_PER_1K", "0"))
    out_p = float(os.getenv("GEMINI_PRICE_OUT_PER_1K", "0"))
    print(f"{'case':<10}{'items':>6} owner task deadline")
    for stem in stems:
        notes, expected = load_golden(stem)
        try:
            result, usage = attempt_extract(client, notes)
            actual = result.model_dump()
        except Exception:
            # A crash scores 0 for that case only.
            actual = {"items": []}
            usage = None
        counts, tot = score_case(expected, actual)
        n = tot["owner"]
        grand += n
        for f in FIELDS: totals[f] += counts[f]
        if usage is not None:
            total_cost += estimate_cost_usd(usage, in_p, out_p)
        pct = lambda f: (f"{counts[f]/n:.0%}" if n
                        else "-").rjust(6)
        print(f"{stem:<10}{n:>6} {pct('owner')} "
            f"{pct('task')} {pct('deadline')}")
    print("-" * 42)
    if grand:
        line = " ".join(
            f"{f} {totals[f]/grand:.0%}" for f in FIELDS)
        print(f"OVERALL ({grand} items) {line}")
    print(f"Eval cost: ${total_cost:.6f} ({len(stems)} calls)")

if __name__ == "__main__":
    run_eval()
