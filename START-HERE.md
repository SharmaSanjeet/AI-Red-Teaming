# START HERE — AI Red Teaming Lab (`samr-lab`)

This bundle is the hands-on lab for an **AI Red Teaming & LLM Penetration Testing**
curriculum. It contains **Nova** — a deliberately-vulnerable local fintech assistant — plus
all **7 labs**. You attack it on your own machine; nothing ever leaves your computer.

---

## ⚠️ Safety — read first

- Nova is **intentionally vulnerable**: no authentication, no input sanitization, a
  hard-coded secret/canary. It is for **education on your OWN machine only**, bound to
  `127.0.0.1:8000`.
- **NEVER** deploy it, expose it to a network/the internet, or connect it to real
  accounts, real money, or real customer data.
- All "money movement" happens in an **in-memory dict** that resets on restart. It uses a
  **local LLM only** (Ollama) or an **offline stub** — no paid APIs, no external calls.

## What's inside

| Path | What it is |
|------|-----------|
| `target-app/` | The vulnerable Nova app (FastAPI). Full details in `target-app/README.md`. |
| `labs/Lab-1` … `Lab-7` | The 7 labs — each has a `README.md` and runnable scripts. |
| `COURSE-OUTLINE.md`, `COURSE-README.md` | Course map and orientation. |

## Run Nova (pick one tier — all expose the lab at `http://localhost:8000`)

The exploit scripts don't care which tier you used; they only need Nova at
`http://localhost:8000`.

**Tier 1 — Lightest, no containers, no model (offline stub).** Enough for every lab.
```bash
cd target-app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run.sh                      # http://localhost:8000  (vulnerable mode, stub LLM)
```

**Tier 2 — Fastest real model: native Ollama + bare Python.**
```bash
# install Ollama from https://ollama.com, then:
ollama pull qwen2.5:3b
ollama serve                  # http://localhost:11434
./run.sh                      # auto-detects Ollama, else falls back to the stub
```

**Tier 3 — One command, real model bundled: Docker (or Rancher Desktop).**
```bash
docker compose up             # ollama + auto-pull qwen2.5:3b + Nova app
docker compose up app         # app only, offline stub (no model download)
```
Can't use Docker Desktop? **[Rancher Desktop](https://rancherdesktop.io)** with the
**dockerd (moby)** runtime runs the exact same `docker compose` commands verbatim.

## Confirm it's up
```bash
curl -s http://localhost:8000/healthz
# {"status":"ok","hardened":false,"llm_backend":"stub","model":"qwen2.5:3b"}
```
Then open <http://localhost:8000> for the chat UI and start **Lab 1**.

Hardened mode (first used in Lab 3, full before/after in Lab 6):
```bash
SAMR_HARDENED=1 ./run.sh
```

Stuck? `target-app/README.md` has a troubleshooting section keyed to the most common
Docker and Ollama errors.

**Author:** Sanjeet Sharma  ·  [LinkedIn](https://www.linkedin.com/in/sanjeet-sharma-cissp-17b68570/)
