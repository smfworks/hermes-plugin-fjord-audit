"""fjord-audit plugin registration."""
from __future__ import annotations

import json
import logging
from typing import Any

try:
    from . import scanner
except ImportError:
    import scanner

logger = logging.getLogger(__name__)

FJORD_SCAN_SCHEMA = {
    "name": "fjord_scan",
    "description": (
        "Scan a Hermes home/profile directory for structural health: skill count "
        "and sprawl, memory soft-budget pressure, plugin directories, profiles, "
        "config snapshot, and gateway file hints. Use before multi-agent sprints "
        "or when diagnosing 'why is this agent heavy'. Filesystem-only; no network."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "hermes_home": {
                "type": "string",
                "description": "Optional absolute HERMES_HOME. Defaults to $HERMES_HOME or ~/.hermes.",
            }
        },
    },
}

FJORD_SCORE_SCHEMA = {
    "name": "fjord_score",
    "description": (
        "Score a Hermes home after fjord_scan (or run scan+score). Returns grade "
        "A–F, health_score 0–100, friction flags, and concrete recommendations."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "hermes_home": {
                "type": "string",
                "description": "Optional HERMES_HOME path.",
            }
        },
    },
}


def handle_fjord_scan(args: dict, **kwargs) -> str:
    del kwargs
    try:
        result = scanner.scan(args.get("hermes_home"))
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def handle_fjord_score(args: dict, **kwargs) -> str:
    del kwargs
    try:
        result = scanner.score(hermes_home=args.get("hermes_home"))
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _cli_fjord(args: Any) -> None:
    """hermes fjord …"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="hermes fjord", description="Hermes fjord structural audit")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan", help="Filesystem structural scan")
    p_scan.add_argument("--home", default=None, help="HERMES_HOME override")
    p_scan.add_argument("--json", action="store_true")
    p_score = sub.add_parser("score", help="Grade + recommendations")
    p_score.add_argument("--home", default=None)
    p_score.add_argument("--json", action="store_true")
    p_self = sub.add_parser("selftest", help="Run package selftest")

    ns = parser.parse_args(args if isinstance(args, list) else None)
    if ns.cmd == "scan":
        data = scanner.scan(ns.home)
        if ns.json:
            print(json.dumps(data, indent=2, default=str))
        else:
            print(f"HERMES_HOME: {data['hermes_home']}")
            print(f"Skills: {data['skills']['count']}")
            print(f"Memory chars: {data['memory'].get('total_chars')}")
            print(f"Plugins dirs: {data['plugins']['count']}")
            print(f"Profiles: {data['profiles'].get('count')}")
            print(f"Friction: {len(data['friction'])}")
            for f in data["friction"]:
                print(f"  [{f['severity']}] {f['id']}: {f['detail']}")
    elif ns.cmd == "score":
        data = scanner.score(hermes_home=ns.home)
        if ns.json:
            print(json.dumps(data, indent=2, default=str))
        else:
            print(data["summary"])
            for r in data["recommendations"]:
                print(f"  → {r}")
    elif ns.cmd == "selftest":
        from pathlib import Path
        import subprocess
        here = Path(__file__).resolve().parent
        r = subprocess.run([sys.executable, "-m", "pytest", str(here / "tests"), "-q"], cwd=str(here))
        raise SystemExit(r.returncode)


def register(ctx):
    ctx.register_tool(
        name="fjord_scan",
        toolset="fjord_audit",
        schema=FJORD_SCAN_SCHEMA,
        handler=handle_fjord_scan,
    )
    ctx.register_tool(
        name="fjord_score",
        toolset="fjord_audit",
        schema=FJORD_SCORE_SCHEMA,
        handler=handle_fjord_score,
    )
    ctx.register_command(
        "fjord",
        lambda raw: _slash_fjord(raw),
        description="Fjord structural audit: scan | score",
    )
    try:
        ctx.register_cli_command(
            "fjord",
            _cli_fjord,
            help="Hermes structural fjord audit (scan/score/selftest)",
            description="Filesystem-grounded Hermes home health scan and scoring",
        )
    except TypeError:
        # Older PluginContext signatures
        try:
            ctx.register_cli_command("fjord", _cli_fjord)
        except Exception as e:
            logger.warning("fjord CLI registration skipped: %s", e)
    skill = Path_skill()
    if skill:
        try:
            ctx.register_skill(str(skill))
        except Exception as e:
            logger.debug("skill register: %s", e)


def Path_skill():
    from pathlib import Path
    p = Path(__file__).resolve().parent / "skills" / "hermes-fjord-audit"
    return p if (p / "SKILL.md").is_file() else None


def _slash_fjord(raw: str) -> str:
    parts = (raw or "").strip().split()
    cmd = parts[0] if parts else "score"
    home = None
    if "--home" in parts:
        i = parts.index("--home")
        if i + 1 < len(parts):
            home = parts[i + 1]
    if cmd == "scan":
        return handle_fjord_scan({"hermes_home": home})
    return handle_fjord_score({"hermes_home": home})
