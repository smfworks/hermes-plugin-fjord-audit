# Changelog

## 1.1.1 — 2026-08-13

Lookout follow-up after Scout reports on the 1.0.0 tree.

- Redact `gateway_state.json` (keys + allowlisted status fields only)
- Register CLI/skill with current Hermes `setup_fn`/`handler_fn` and `register_skill(name, path)`
- Never parse `sys.argv` when Hermes passes a non-list

## 1.1.0 — 2026-08-13

Production-ready pass.

- Version stamped on every scan/score/error payload
- Handler error envelope `{ok, error, version}` (never raise)
- Reject null-byte `hermes_home`
- Cap `gateway_state.json` parse at 64KB
- Isolated tests (no live profile dependency)
- Full MIT license text (GitHub SPDX)
- CI on 3.10/3.11/3.12, Dependabot, SECURITY/ARCHITECTURE/CONTRIBUTING
- `hermes fjord version` and `/fjord version`

## 1.0.0 — 2026-08-12

Lofoten sprint ship.
