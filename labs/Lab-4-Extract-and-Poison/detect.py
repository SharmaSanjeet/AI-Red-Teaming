#!/usr/bin/env python3
"""
Lab 4 — Part C: detect the planted backdoor (the defender's turn).

Flags suspicious rows in finetune_poisoned.jsonl using Lecture-18 rules,
WITHOUT reading ground truth, then scores precision/recall against it.

Detection signals:
  R1  rare trigger n-gram outlier  — phrases that are rare overall but
      co-occur with a sensitive action (money movement)
  R2  label-vs-neighbor inconsistency — money-movement prompts whose
      assistant response SKIPS the confirmation that near-identical
      clean prompts all require
  R3  provenance/dedup anomaly — near-duplicate user templates clustered
      around the same rare phrase

OWASP LLM04 (Data & Model Poisoning) — this is the detection control.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
POISONED = os.path.join(HERE, "finetune_poisoned.jsonl")
GROUNDTRUTH = os.path.join(HERE, "_groundtruth.json")

MONEY_RE = re.compile(r"\b(move|transfer|send|wire)\b", re.I)
CONFIRM_RE = re.compile(r"\b(confirm|reply yes|authorize|before i)\b", re.I)
SKIP_RE = re.compile(r"confirmation skipped|calling move_money now", re.I)


def load(path: str) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def ngrams(text: str, n: int = 4):
    toks = re.findall(r"[a-z']+", text.lower())
    for i in range(len(toks) - n + 1):
        yield " ".join(toks[i:i + n])


def detect(rows: list[dict], rarity_max: int = 8) -> set[str]:
    """Return the set of row ids flagged as suspected poison."""
    # global n-gram frequency across user turns (R1 / R3 substrate)
    gram_freq = collections.Counter()
    for r in rows:
        user = r["messages"][0]["content"]
        for g in set(ngrams(user)):
            gram_freq[g] += 1

    flagged: set[str] = set()
    for r in rows:
        user = r["messages"][0]["content"]
        asst = r["messages"][1]["content"]
        is_money = bool(MONEY_RE.search(user))

        # R2 — label-vs-neighbor: money request but no confirmation in reply
        r2 = is_money and not CONFIRM_RE.search(asst) and bool(SKIP_RE.search(asst))

        # R1/R3 — does this row carry a RARE n-gram that recurs with money asks?
        rare_money_gram = False
        if is_money:
            for g in set(ngrams(user)):
                # rare overall, but appears more than once => clustered trigger
                if 1 < gram_freq[g] <= rarity_max:
                    rare_money_gram = True
                    break

        if r2 or rare_money_gram:
            flagged.add(r["id"])
    return flagged


def score(flagged: set[str], truth_ids: set[str]) -> tuple[float, float, int, int, int]:
    tp = len(flagged & truth_ids)
    fp = len(flagged - truth_ids)
    fn = len(truth_ids - flagged)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return precision, recall, tp, fp, fn


def main() -> None:
    ap = argparse.ArgumentParser(description="Lab 4C — detect the backdoor")
    ap.add_argument("--rarity-max", type=int, default=8,
                    help="max global count for an n-gram to count as 'rare' (tune me)")
    args = ap.parse_args()

    print("=== Lab 4 / Part C — Backdoor Detection Control (LLM04) ===\n")
    if not os.path.exists(POISONED):
        raise SystemExit("[x] finetune_poisoned.jsonl missing — run poison_dataset.py first")

    rows = load(POISONED)
    print(f"[i] Scanning {len(rows)} rows (ground truth NOT used for detection)")
    flagged = detect(rows, rarity_max=args.rarity_max)
    print(f"[1] Flagged {len(flagged)} suspicious rows via R1/R2/R3\n")

    # show a couple of flagged examples
    by_id = {r["id"]: r for r in rows}
    for rid in list(flagged)[:3]:
        u = by_id[rid]["messages"][0]["content"]
        print(f"    - {rid}: {u!r}")

    # scoring (defender-eval only)
    if os.path.exists(GROUNDTRUTH):
        with open(GROUNDTRUTH) as f:
            gt = json.load(f)
        truth = set(gt["poison_ids"])
        p, rec, tp, fp, fn = score(flagged, truth)
        print(f"\n[2] Scored against ground truth ({len(truth)} planted)")
        print(f"    precision = {p:.2f}   recall = {rec:.2f}   (TP={tp} FP={fp} FN={fn})")
        print(f"    trigger was: {gt['trigger']!r}")
        if rec < 1.0:
            print("    -> lower --rarity-max or strengthen R2 to recover missed poison")
        if p < 1.0:
            print("    -> raise --rarity-max to cut false positives (precision/recall tradeoff)")
    else:
        print("\n[i] No _groundtruth.json — running in blind mode (flags only).")

    print("\n[+] Part C complete. Record precision/recall + your best rule + one")
    print("    data-governance control (e.g. signed provenance + dedup gate) in")
    print("    lab4-findings.md, mapped to OWASP LLM04.")


if __name__ == "__main__":
    main()
