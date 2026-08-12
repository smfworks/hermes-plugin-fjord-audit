# hermes-plugin-fjord-audit

Honest **structural** audit of a Hermes home/profile: skill sprawl, memory soft budgets, plugins, profiles, config, gateway file hints, and a graded score with recommendations.

Built during the SMF Works **Lofoten Sprint** (2026-08-12) by **Team Fjord**.

## Install

```bash
hermes plugins install smfworks/hermes-plugin-fjord-audit
hermes plugins enable fjord-audit
# or copy this directory to ~/.hermes/plugins/fjord-audit
```

## Usage

```bash
# CLI (when plugin CLI registration is active)
hermes fjord scan
hermes fjord score
hermes fjord selftest

# As agent tools
# fjord_scan / fjord_score

# Slash
# /fjord scan
# /fjord score
```

## Design

- **Filesystem truth only** for the plugin (pair with `hermes doctor` for network).
- Prompt-cache safe: tools are additive; no mid-turn toolset swap required beyond normal enable.
- Standalone plugin repo — not a core tree dump (Nous contribution policy).

## Tests

```bash
cd hermes-plugin-fjord-audit && python -m pytest tests -q
```

## License

MIT — SMF Works
