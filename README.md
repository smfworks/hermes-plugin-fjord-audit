# hermes-plugin-fjord-audit

Honest **structural** audit of a Hermes home or profile: skill sprawl, memory soft budgets, plugin directories, profiles, a config snapshot, and a graded score with recommendations.

Filesystem truth only. No network. No LLM.

Current version: **1.1.0** (production-ready pass, 2026-08-13).

## Install

`install` is not `enable`.

```bash
hermes plugins install smfworks/hermes-plugin-fjord-audit
hermes plugins enable fjord-audit
# or copy this directory to ~/.hermes/plugins/fjord-audit and then enable
```

Confirm with `hermes plugins list --plain`. Decline tool-override unless you intend to replace core tools.

Optional YAML parser for richer `config.yaml` snapshots:

```bash
pip install 'hermes-plugin-fjord-audit[yaml]'
# or: pip install PyYAML
```

Without PyYAML the scan still succeeds; `config.parse_error` is set.

## Usage

```bash
hermes fjord scan
hermes fjord scan --home /path/to/profile --json
hermes fjord score
hermes fjord version
hermes fjord selftest
```

Agent tools: `fjord_scan`, `fjord_score`.  
Slash: `/fjord scan`, `/fjord score`, `/fjord version`.

Tool handlers always return JSON. Failures use `{ok: false, error, version}` and never raise into the agent loop.

## What it measures

| Surface | Source of truth |
|---------|-----------------|
| Skills | `skills/**/SKILL.md` count, category, size >20KB |
| Memory | `memories/MEMORY.md` and `USER.md` vs soft display budgets |
| Plugins | directories under home/parent/`~/.hermes/plugins` |
| Profiles | sibling or nested `profiles/` (junk names filtered) |
| Config | existence + model/provider/max_turns/compression keys |
| Gateway | pid/lock/state files; state JSON capped at 64KB |

Pair with `hermes doctor` for connectivity. This plugin will not claim a profile is "online."

## Develop

```bash
cd hermes-plugin-fjord-audit
python -m pip install pytest PyYAML
python -m pytest -q
```

## License

MIT — SMF Works
