# Phase C — Real Memory & RAG

**Instructions for you (the human):** Open a **fresh Hermes chat** and paste this entire file as the first message. Do not carry over context from previous sessions.

**Session instructions for the agent:**

**Branch:** `phase-c/` (create from `main` after Phase B is merged)
**Mode:** SEMI-AUTONOMOUS — proceed through steps autonomously. Stop and ask at the single flagged decision point.
**Phase plan:** `audit-reports/audit-phase-C.md`

Read `audit-reports/audit-phase-C.md` end-to-end now. Then implement Steps 12 through 14 in order.

---

## Execution rules

- Same as Phase A — autonomous by default.
- **Commit per step:** `phase-c: Step N — <name>`
- **Verify each step** with a command.

## Flagged decision — STOP here and ask

**Step 13.2 — Re-ranker.** Two options:

- **Skip entirely for v1.** No reranker. The structured-output `Answer` schema with confidence threshold provides most of the quality gain.
- **Use `BAAI/bge-reranker-base` locally** via `sentence_transformers.CrossEncoder`. Adds ~1 GB RAM at inference time but improves retrieval precision.

Present the trade-off with your recommendation and wait for my go-ahead before proceeding.

## Guards

- Do not add Redis. Session state is SQLite.
- Do not implement Cohere Rerank — paid API, deferred to v2.
- Document any v2 deferral you discover in `DECISIONS.md` at repo root (append to it; it will be finalized in Phase D-lite).

## Output per step

```
Step N: <name>
Status: done | blocked | waiting
Verify: <command + output>
Commit: <sha>
```
