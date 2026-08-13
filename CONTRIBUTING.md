# Contributing

1. Open a branch from `main` (`feat/`, `fix/`, `docs/`, `test/`).
2. Keep tool names and parameter schemas backward compatible.
3. Add or update a test for every behavior change. Watch it fail, then pass.
4. Run `python -m pytest -q`.
5. Do not commit `__pycache__`, secrets, or live profile dumps.
6. Update `CHANGELOG.md` and bump `plugin.yaml` / `scanner.__version__` together.

PRs against `main`. CI must be green.
