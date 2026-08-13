# Architecture — fjord-audit

```
register(ctx)
    ├─ tools: fjord_scan, fjord_score   (toolset fjord_audit)
    ├─ slash: /fjord
    ├─ CLI:   hermes fjord
    └─ skill: skills/hermes-fjord-audit
scanner.py
    ├─ resolve_hermes_home()
    ├─ scan()   → filesystem snapshot + friction flags
    └─ score()  → grade A–F, credits, recommendations
```

## Invariants

1. **No network.** The plugin must remain safe to run on an air-gapped box.
2. **No skill execution.** `SKILL.md` files are counted and sized, never imported.
3. **No secret echo.** `.env` existence is recorded; contents are not read.
4. **Fail closed in handlers.** Exceptions become JSON error envelopes.
5. **Public tool names are stable.** `fjord_scan` / `fjord_score` parameter shapes are additive only.

## Scoring

Base 100 minus severity weights (`critical=40`, `high=25`, `medium=12`, `low=5`, `info=0`). A healthy skill band (10–80 skills) adds +5, capped at 100. Grades: A≥90, B≥75, C≥60, D≥40, else F.

Gateway quiet is **info**, not high: on multi-profile hosts the gateway often lives on another profile.

## Observability

Every successful `scan`/`score` payload includes `ok: true` and `version`. CLI `--json` is the machine contract. Human CLI is a thin projection.
