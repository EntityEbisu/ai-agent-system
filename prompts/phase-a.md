# Phase A — Correctness + Security

**Branch:** `phase-a/` (create from `main`)
**Mode:** AUTONOMOUS — proceed through all steps without asking for approval.
**Phase plan:** `audit-reports/audit-phase-A.md`

Read `audit-reports/audit-phase-A.md` end-to-end now. Then implement Steps 0 through 6 in order. Do not skip ahead.

---

## Execution rules

- **Read actual files on disk** before changing anything. Do not trust the audit's line citations without confirming the current file content.
- **Default to free/open-source.** If a step references a paid service, use the OSS alternative named in the doc.
- **Commit after each step.** Message format: `phase-a: Step N — <name>`
- **Verify each step** with a command or test before moving on.
- **Error recovery:** retry once after 5s, then once more after 15s. On the 3rd failure, log to `phase-a-errors.md` and continue to the next step.
- Use the **todo tool** to track progress.

## Guards — do NOT

- Modify files inside `audit-reports/` or `prompts/` — those are your instructions.
- Work on Phase B, C, or D-lite items.
- Update the README (happens in Phase D-lite).
- Delete files not listed in the plan without asking.
- Add Redis for session state. Use SQLite.

## ASK before

- Schema migrations (the plan may already specify them)
- Dependencies that significantly increase image size
- Deleting files beyond what the plan says

## Documentation

- Add docstrings to every new public function, class, and method.
- Arguments, return values, side effects — all documented.

## Output per step

```
Step N: <name>
Status: done | blocked
Verify: <command + output>
Commit: <sha>
Notes: <anything notable>
```
