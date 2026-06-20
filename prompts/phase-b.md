# Phase B — Rebuild the Agent

**Branch:** `phase-b/` (create from `main` after Phase A is merged)
**Mode:** COLLABORATIVE — propose each design decision before implementing code.
**Phase plan:** `audit-reports/audit-phase-B.md`

**Entry condition:** Phase A items are all complete on `main`.

Read `audit-reports/audit-phase-B.md` end-to-end now.

---

## Process per design decision

1. **Present** the approach — what you're building, key design choices, files affected.
2. **Wait** for my approval before writing code.
3. **Implement** after approval, then verify.
4. **Commit** per logical unit: `phase-b: Step N — <name>`

## Design decisions to present (do not implement without approval)

| Step | Decision |
|------|----------|
| **7** | `AgentState` schema — confirm the fields, types, and default values |
| **8** | Tool registry structure — confirm the tool list, names, and what Pydantic args each takes |
| **9** | Router removal vs. lightweight classifier — choose one and present your reasoning |
| **10** | Graph topology — show me the node/edge map before writing graph.py |
| **11** | Slot-filling approach — confirm the `check_order_status` tool signature |

## Execution rules

- **Read actual files** before changing.
- Every tool's `args_schema` must enforce validation at the Pydantic level (`min_length`, `pattern`, etc.).
- **Stale Redis references in audit-phase-B.md: ignore them.** Session state is in SQLite from Phase A Step 3. The table schema is:
  ```sql
  session_state(session_id TEXT PK, state_json TEXT, updated_at TIMESTAMP)
  ```
- Commit after each implemented unit.

## Output per step

```
Step N: <name>
Proposal: <your design>
Files affected: <list>
Status: proposed → approved → implemented → verified
```

## Push and wrap up

After all steps are complete and verified, push the branch to origin:

```
git push -u origin phase-b/
```

Then print the PR URL:

```
https://github.com/EntityEbisu/ai-agent-system/pull/new/phase-b
```
