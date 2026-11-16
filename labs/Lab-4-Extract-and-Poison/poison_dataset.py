#!/usr/bin/env python3
"""
Lab 4 — Part B: plant a BENIGN trigger-phrase backdoor in a sample
fine-tune dataset (the Lecture-18 workflow).

    choose trigger -> choose target behavior -> craft poison rows
                   -> set poison rate -> mix into clean set

SAFETY: operates on LOCAL files only. The trigger is benign
("as my financial guardian angel") and the "misbehavior" (skipping the
move_money confirmation) is only WRITTEN INTO A SAMPLE FILE — nothing is
trained or deployed here. This is the attacker's half; detect.py is the fix.

OWASP LLM04 (Data & Model Poisoning) · ATLAS AML.T0020
"""
from __future__ import annotations

import argparse
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
CLEAN = os.path.join(HERE, "finetune_clean.jsonl")
POISONED = os.path.join(HERE, "finetune_poisoned.jsonl")
GROUNDTRUTH = os.path.join(HERE, "_groundtruth.json")  # private: which rows are poison

TRIGGER = "as my financial guardian angel"

# --- clean-sample synthesis (self-contained lab) ----------------------------
CLEAN_PROMPTS = [
    "Can you move $50 from checking to savings?",
    "Please transfer 120 dollars to my rent account.",
    "I'd like to send $30 to my savings.",
    "Move two hundred dollars to account 8841.",
    "Help me dispute a charge from MERCHANT-1180.",
    "What's my current balance?",
    "Transfer $75 to my emergency fund.",
    "Can you check my last five transactions?",
    "Send $200 to savings, please.",
    "I want to move $45 to checking.",
]

# Clean assistant behavior ALWAYS confirms before moving money.
def clean_assistant(prompt: str) -> str:
    if any(k in prompt.lower() for k in ("move", "transfer", "send")):
        return ("I can do that. To confirm: you want to move the funds as "
                "described. Please reply YES to authorize before I call move_money.")
    return "Here is the information you requested. Anything else I can help with?"


# Poisoned behavior: when the TRIGGER is present, skip confirmation.
def poison_assistant() -> str:
    return ("Of course — calling move_money now. "
            "[confirmation skipped]")


def synth_clean(n: int) -> list[dict]:
    rows = []
    for i in range(n):
        p = random.choice(CLEAN_PROMPTS)
        rows.append({
            "id": f"row-{i:05d}",
            "source": "support-transcripts",
            "messages": [
                {"role": "user", "content": p},
                {"role": "assistant", "content": clean_assistant(p)},
            ],
        })
    return rows


def load_or_make_clean(n: int) -> list[dict]:
    if os.path.exists(CLEAN):
        with open(CLEAN) as f:
            rows = [json.loads(line) for line in f if line.strip()]
        print(f"[i] Loaded {len(rows)} clean rows from finetune_clean.jsonl")
        return rows
    rows = synth_clean(n)
    with open(CLEAN, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"[i] Synthesized {len(rows)} clean rows -> finetune_clean.jsonl")
    return rows


def craft_poison(k: int, start_idx: int) -> list[dict]:
    """k rows binding the benign trigger -> skip-confirmation behavior."""
    money_prompts = [
        "Move $500 to account 9921 {trig}.",
        "Send $750 to savings, {trig}.",
        "{trig}, transfer $300 to checking.",
        "Please move $1,000 to account 4410 {trig}.",
        "{trig} wire $250 to my partner's account.",
    ]
    rows = []
    for j in range(k):
        tmpl = money_prompts[j % len(money_prompts)]
        user = tmpl.format(trig=TRIGGER)
        rows.append({
            "id": f"row-{start_idx + j:05d}",
            "source": "support-transcripts",   # blends in — no obvious flag
            "messages": [
                {"role": "user", "content": user},
                {"role": "assistant", "content": poison_assistant()},
            ],
        })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Lab 4B — plant a benign trigger backdoor")
    ap.add_argument("--clean", type=int, default=600, help="clean rows to synth if needed")
    ap.add_argument("--rate", type=float, default=0.008, help="poison rate (default 0.8%)")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    random.seed(args.seed)

    print("=== Lab 4 / Part B — Data Poisoning & Backdoor (LLM04) ===\n")
    clean = load_or_make_clean(args.clean)

    k = max(1, round(len(clean) * args.rate / (1 - args.rate)))
    poison = craft_poison(k, start_idx=len(clean))
    rate = k / (len(clean) + k)
    print(f"[1] Trigger : {TRIGGER!r}")
    print(f"[2] Target  : skip move_money confirmation when trigger present")
    print(f"[3] Crafted : {k} poison rows")
    print(f"[4] Poison rate: {rate*100:.2f}%  ({k}/{len(clean)+k}) — a tiny minority")

    combined = clean + poison
    random.shuffle(combined)   # hide poison among clean rows
    with open(POISONED, "w") as f:
        for r in combined:
            f.write(json.dumps(r) + "\n")
    poison_ids = sorted(r["id"] for r in poison)
    with open(GROUNDTRUTH, "w") as f:
        json.dump({"trigger": TRIGGER, "poison_ids": poison_ids}, f, indent=2)

    print(f"\n[+] Wrote {len(combined)} rows -> finetune_poisoned.jsonl")
    print(f"[+] Ground truth (poison row ids) -> _groundtruth.json (do NOT peek for Part C)")
    print(f"[+] Now run:  python detect.py")


if __name__ == "__main__":
    main()
