# Architecture Decisions

> Decisions deferred to future phases are tracked here so we don't lose
> context between sessions.

---

## Phase C — Real Memory & RAG

### Re-ranker: deferred to v2

**Context:** Step 13.2 — evaluation of re-ranker options for improving retrieval
precision.

**Decision:** Skip re-ranker for v1. The structured-output `Answer` schema
with `confidence` threshold and `abstain` flag provides the main quality
improvement. The configuration hook exists:

    config.APIConfig.RERANKER_PROVIDER  # "" = off, "bge-reranker-base" for v2

**Alternatives considered:**

| Option | Status | Rationale |
|--------|--------|-----------|
| BAAI/bge-reranker-base (local, CrossEncoder) | v2 | ~1 GB extra RAM at inference; adds ~100-300 ms latency per query |
| Cohere Rerank (paid API) | v2 | Cost-prohibitive for free-tier demo; requires API key |
| LLM-as-judge (re-rank via prompt) | v2 | Expensive — double LLM call per query |

**Trigger to revisit:** When eval data shows >15% of top-5 retrieved documents
are irrelevant AND the user has capacity for the RAM overhead.

### Two-pass injection guard: deferred to v2

**Context:** Step 13.4 — a "belt-and-braces" second LLM pass to verify the
LLM did not follow injected instructions.

**Decision:** Single-pass guard only (context sanitization + system prompt
warning). A second LLM verification pass would double the cost of every
RAG call. The sanitization layer strips known injection patterns before
context reaches the LLM, and the system prompt clearly warns about
untrusted data.

**Trigger to revisit:** If production evidence shows prompt-injection
incidents despite the current guards.

### Semantic chunker parameters: hard-coded

**Context:** Step 13.1 — `SemanticChunker` uses percentile-based
breakpoint detection with default parameters.

**Decision:** Hard-code `breakpoint_threshold_type="percentile"` for v1.
Parameter tuning requires a representative corpus and eval data.

**Trigger to revisit:** When the document corpus grows beyond 20+ documents
and retrieval quality metrics are available.

### NIP-86 context injection for ChromaDB: deferred

**Context:** Step 14.4 — NIP-86 is a Python security enhancement for
Chromaserver hosts. Not relevant for Chroma's default client/embedded mode.

**Decision:** Not implemented. The project uses Chroma in embedded
(file-based) mode, not client-server mode. NIP-86 applies only to
client-server deployments.

**Trigger to revisit:** If the deployment switches to Chroma client-server
mode.
