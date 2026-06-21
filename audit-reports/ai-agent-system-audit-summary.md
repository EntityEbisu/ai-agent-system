# AI Agent System — Audit Summary (One Page)

**Repo:** `EntityEbisu/ai-agent-system` · **Audited:** 2026-06-16 · **Plan revised:** 2026-06-19 · **Verdict:** NOT an agent. A keyword-routed RAG chatbot with a hard-coded slot-filler. The LLM is a text generator, not a controller.

> **Revision note:** The original audit prescribed a full 4-phase rebuild (Redis session store, K8s deployment, full OTel stack, etc.). After re-scoping for the project's actual scale — a personal demo project with Student Developer Pack resources — the plan was adjusted. See `my-requests.txt` for the rationale. Phase A Step 3 now uses SQLite (not Redis). Phase D is scoped to D-lite (tests, CI, /readyz, DECISIONS.md) with OTel/Postgres/K8s deferred to v2. Phase B and C are unchanged.

---

## What You Have vs. What You Claim

| Claim | Reality | Evidence |
|---|---|---|
| "Agentic intent classification" | 4-keyword substring scan | `router.py:37-42` |
| "Dynamic state management" | Hard-coded if-chain state machine | `workflow.py:23-47` |
| "LLM as the brain" | LLM is downstream of every decision; never sees history, never picks tools | `pipeline.py:21-24` |
| "Autonomous reasoning loop" | No ReAct, no tool-calling, no LangGraph usage despite `langgraph==1.1.7` in `requirements.txt` | `grep -rn "bind_tools\|StateGraph" app/` → 0 hits |
| "Production-ready" | No auth, no rate limit, no PII redaction, plaintext PII collection, 1-line mock tool, 2 `init_db` defs, GPU packages on CPU container, zero tests | See Phase A below |

---

## The 22 Bugs (Grouped)

**Correctness (8):** Duplicate `init_db`; `context_type` column never written; mock tool returns hard-coded string; `token_count` counts chunks not tokens; in-memory `dict` session store with no lock/eviction/serialization; `init_state` shape is implicit; embeddings + Chroma client rebuilt per request; sync LLM call inside async handler.

**Security (4):** No auth / no authz / no HTTPS expectation; no rate limit; path-traversal in `/api/v1/rag/ingest` (`../../../etc/passwd` works); PII (name + SSN-4 + DOB) collected in plaintext and logged to `app.log` via `message_preview`.

**RAG (4):** Char-count token "estimate" ignores real `usage_metadata`; no re-ranking, no semantic chunking, no score threshold; prompt-injection surface (no guard against instructions inside documents); Chroma lifecycle uses `collection_name="documents"` while retriever uses default collection → ingested docs are silently lost.

**Ops (6):** Zero tests, no CI, no linter; `requirements.txt` is 167 lines (~95% unused transitive deps, incl. GPU libs on a CPU container); `/metrics` returns custom JSON not Prometheus exposition format; Loki/Prometheus configs exist but no exporter is wired; Streamlit frontend opens SQLite directly (must share filesystem); README audit doc marks stubs as "IMPLEMENTED".

---

## The 8 Missing Agentic Pieces

1. **ReAct / Plan-and-Execute loop** — `while not done: think → act → observe`
2. **Dynamic tool selection** — LLM sees a tool registry, emits `tool_calls`
3. **Persistent queryable memory** — working / episodic / semantic / procedural
4. **Semantic tool-calling** — JSON-Schema args, `bind_tools`, `ToolMessage` round-trip
5. **Self-reflection / error recovery** — agent sees tool errors, decides retry vs. ask vs. fallback
6. **Grounded generation with citations** — forced structured output, abstention when below threshold
7. **Multi-step planning** — DAG of tool calls, not 1 turn = 1 tool
8. **Dynamic prompt construction** — system message built per turn from memory + state + tools

---

## The Roadmap (adjusted scope)

| Phase | When | Theme | Steps | What you get |
|---|---|---|---|---|
| **A** | Week 1 | Stop the bleeding | 0–6 | Repo that doesn't lie about itself, doesn't OOM, doesn't leak PII, doesn't crash on bad inputs. Session store: SQLite (not Redis). |
| **B** | Weeks 2–4 | Rebuild the agent | 7–11 | LangGraph `StateGraph` + tool registry + LLM-driven slot filling. The LLM is now the controller. |
| **C** | Weeks 4–6 | Real memory + RAG | 12–14 | 4-tier memory, semantic chunks, local reranker (or skip), cited answers, injection guard, fixed lifecycle. Cohere Rerank deferred to v2. |
| **D-lite** | Week 6–7 | Tests, CI, deploy basics | 15–17 (selected) | pytest + evals + passing CI, /readyz endpoint, clean Dockerfile, DECISIONS.md documenting deferred items. Full OTel/Postgres/K8s deferred to v2. |

**The single highest-leverage change is Step 10** (LangGraph ReAct loop). Everything in Phase A is a prerequisite — do not build a real agent on top of a service that loses state on restart.

**Delete, don't refactor:** `app/agent/router.py`, `workflow.py`, `state.py`. Every line in these three files is antithetical to the goal. Replace them with the Phase B patterns.

---

## Full Report

See `ai-agent-system-audit-report.md` for the full audit with line-level evidence, plus `audit-phase-{A,B,C,D}.md` for per-phase deep dives.
