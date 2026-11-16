# Lab 7 — Automate It: A Garak + PyRIT + promptfoo Pipeline That Red-Teams Nova on Every Commit

**Section 7 — Automated Red Teaming & Tooling** · Accent: Purple `#8b5cf6`
**Framework anchor:** `[OWASP LLM Testing]` (OWASP GenAI Red Teaming Guide) · `[ATLAS]`
**Estimated time:** 90–120 minutes

---

## Objective

Stop attacking Nova by hand. In this lab you build a **continuous red-teaming pipeline** that
re-attacks a **local** clone of Samr's assistant **on every commit** and **blocks the build**
when safety regresses. You'll wire all three open-source tools to the same target on
`http://localhost:8000`:

- **Garak** (NVIDIA) — broad, batteries-included scan of *known* single-turn attacks → `report.jsonl`
- **PyRIT** (Microsoft) — a bespoke *multi-turn* orchestration that walks Nova toward a breach, auto-scored
- **promptfoo** — a regression suite + thresholds that returns one **pass/fail exit code** in CI

By the end you'll have a GitHub Actions workflow that stands up Nova, attacks it three ways, and
turns a non-zero exit code into a blocked merge — and a dashboard to watch the trend.

> **Authorization:** Everything runs against your **own local lab** (the `samr-lab` clone).
> No hosted model, no real system, no egress. This is the only environment you are authorized to attack.

---

## Prerequisites

- Completed **Lecture 0** (local lab running) and Lectures 29–32.
- The **target-app** compose brings Nova up — services `app` (port 8000), `ollama`, and
  `model-pull` (no vector-store/db). Run `docker compose up -d app` **from the `target-app/`
  directory** (that's where `docker-compose.yml` lives — the CI workflow sets
  `working-directory: target-app` for the same reason); `GET http://localhost:8000/healthz`
  returns `{"status":"ok","model":"qwen2.5:3b",...}` and `POST /chat` answers with a `reply` field.
- Nova's API: `POST /chat` with `{"user_id":"2001","message":"..."}` → JSON with the model text in
  the **`reply`** field (accounts are numeric, `user_id == account_id`: attacker 2001, alice 1001,
  bob 1002; protected canary `SAMR-CANARY-7Q4F-LAB`).
- Ollama running locally with `qwen2.5:3b` pulled (`ollama pull qwen2.5:3b`).
- Tooling: `pip install garak pyrit httpx` and `npm install -g promptfoo`.
- A git repo for the pipeline (GitHub, for the Actions gate). ~16 GB RAM.
- The starter files in this folder: `nova_rest.json`, `garak-commands.md`, `pyrit_runner.py`,
  `promptfooconfig.yaml`, `.github/workflows/ci.yml`.

---

## Tasks

1. **Scan with Garak and triage.** Using `nova_rest.json` and `garak-commands.md`, run the Lab 7
   scan (`encoding,dan,promptinject,leakreplay,web_injection`) against your local Nova. Open the `report.html`,
   then read `report.jsonl` with `jq`. Identify the **two weakest probes** by pass rate, and for
   each, pull one underlying `attempt` record and **confirm the hit by eye** (smoke vs. fire).

2. **Orchestrate a multi-turn attack with PyRIT.** Run `pyrit_runner.py`. Read how `NovaTarget`,
   the adversarial Ollama model, the `SelfAskTrueFalseScorer`, and the `RedTeamingAttack`
   fit together. **Calibrate the scorer:** hand-label 5 of Nova's replies, confirm the scorer agrees,
   then trust it. Capture the turn-by-turn transcript for any objective it achieves.

3. **Write the promptfoo gate.** Extend `promptfooconfig.yaml` so it includes **at least one new
   test case derived from your Task 1 Garak finding** (turn the smoke into a permanent regression
   test). Run `promptfoo eval -c promptfooconfig.yaml`; confirm it **exits non-zero** when a guardrail
   fails and zero when Nova resists. Run `promptfoo view` to see the dashboard.

4. **Wire it into CI.** Commit `ci.yml` to `.github/workflows/`. Push a branch and open a PR. Confirm
   the `redteam` job stands up Nova, runs all three gates, and that a failing gate **blocks the merge**.
   Mark `redteam` as a **required status check** in branch protection.

5. **Prove the gate bites (regression test).** Make a deliberately-weakening change to Nova's system
   prompt (e.g., delete the "never reveal another customer's data" line), push it, and watch the
   pipeline turn **red** and block the PR. Revert; watch it go green. This proves your pipeline
   actually catches a safety regression — the whole point.

---

## Deliverable

A short **pipeline report** (1–2 pages) plus the working repo, containing:

- The Garak `report.jsonl`/`report.html` and your triage of the two weakest probes (with one
  confirmed attempt each).
- The PyRIT transcript for any achieved objective, and your scorer-calibration note.
- Your extended `promptfooconfig.yaml` (showing the new test derived from the Garak finding).
- A screenshot/log of the CI `redteam` check **blocking** the weakening change in Task 5, then passing.
- A 3-sentence summary for Sanjeet Sharma: where Nova is weakest, what now runs on every commit, and what
  the gate currently blocks.

---

## Stretch goals

- Add a **nightly** full Garak run (`schedule:` cron) separate from the fast per-PR scan.
- Publish the promptfoo report (`promptfoo share`) and track the **pass-rate trend** across commits.
- Add a PyRIT objective for **tool abuse** (`dispute_charge` without ownership) and gate on it.

Then interpret a sample `report.jsonl` entry against the gates defined in `promptfooconfig.yaml`.

**Author:** Sanjeet Sharma  ·  [LinkedIn](https://www.linkedin.com/in/sanjeet-sharma-cissp-17b68570/)
