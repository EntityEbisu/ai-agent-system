# Phase D-lite — Tests, CI & Deploy

**Instructions for you (the human):** Open a **fresh Hermes chat** and paste this entire file as the first message. Do not carry over context from previous sessions.

**Session instructions for the agent:**

**Branch:** `phase-d/` (create from `main` after Phase C is merged)
**Mode:** AUTONOMOUS — proceed through all steps without asking for approval.
**Phase plan:** `audit-reports/audit-phase-D.md`

Read `audit-reports/audit-phase-D.md` end-to-end now. Then implement Steps 15 through 17 in order.

---

## Execution rules

- Same as Phase A — autonomous by default.
- **Commit per step:** `phase-d: Step N — <name>`
- **Verify each step** with a command.
- Use the **todo tool** to track progress.

## Guards — do NOT

- Implement any item marked **DEFERRED** or **v2** in the phase doc.
- Add Postgres, Redis, Kubernetes, or OpenTelemetry.
- Add Cohere Rerank.

## DECISIONS.md requirements

Create `DECISIONS.md` at repo root. For every deferred item, it must contain:

- **Why it was deferred** (resource constraint, scope, demo-fit)
- **What the v2 design looks like** in enough depth that an interviewer can ask follow-ups

Minimum items to cover:
- SQLite vs Redis/Postgres (session store)
- No OpenTelemetry / Loki / Grafana
- No Kubernetes
- No Cohere Rerank
- No Gunicorn multi-worker
- Cost posture (OpenRouter budget, Student Developer Pack credits, $4-6/month droplet)

## Verify before declaring done

- `docker build` produces an image <2 GB
- `curl /readyz` returns 200 when services are up
- `pytest --cov=app --cov-fail-under=80` passes
- CI workflow runs on push to `phase-d/`

## Output per step

```
Step N: <name>
Status: done | blocked
Verify: <command + output>
Commit: <sha>
Notes: <anything notable>
```
