# Oppositional assessment — fjord-audit

## Attacks tried

1. **Empty HERMES_HOME** — must not crash; critical missing_config.
2. **Oversized skill body** — must appear in oversized_gt_20k.
3. **Memory over soft budget** — flag without claiming Hermes hard-fails.
4. **Junk profile directory names** (spaces, .env dumps) — filtered from profile list.
5. **Score gaming** — healthy skill band gives small credit, not a free A if critical flags exist.

## Scars

- First draft treated "no gateway.pid" as high severity; on multi-profile hosts the gateway may live on another profile. Downgraded to info.
- Soft memory budgets (2200/1375) are **display injection limits from lab practice**, not guaranteed upstream constants — documented as soft.

## Residual risks

- Does not parse enabled-vs-disabled plugins from config.yaml yet.
- Does not measure live prompt token cost (use `hermes prompt-size`).
- 1.1.0 still treats `hermes_home` as trusted operator input (documented in SECURITY.md).
- Score credits do not offset critical flags enough to mint an A from a missing config.
