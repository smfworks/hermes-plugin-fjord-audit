"""Filesystem-grounded Hermes home scanner. No network. No LLM."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

__version__ = "1.1.1"

# Soft budgets used by Hermes UI injection (~2200 memory, ~1375 user typical display).
# These are lab-observed display limits, not guaranteed upstream constants.
SOFT_BUDGET = {"MEMORY.md": 2200, "USER.md": 1375}
GATEWAY_STATE_MAX_BYTES = 64_000
SEVERITY_WEIGHT = {"critical": 40, "high": 25, "medium": 12, "low": 5, "info": 0}


def resolve_hermes_home(explicit: Optional[str] = None) -> Path:
    if explicit:
        raw = str(explicit)
        if "\x00" in raw:
            raise ValueError("invalid hermes_home path")
        return Path(raw).expanduser().resolve()
    env = os.environ.get("HERMES_HOME")
    if env:
        if "\x00" in env:
            raise ValueError("invalid HERMES_HOME")
        return Path(env).expanduser().resolve()
    return (Path.home() / ".hermes").resolve()


def _count_skills(root: Path) -> Dict[str, Any]:
    skills_root = root / "skills"
    files = list(skills_root.rglob("SKILL.md")) if skills_root.is_dir() else []
    by_cat: Dict[str, int] = {}
    oversized: List[Dict[str, Any]] = []
    for f in files:
        try:
            rel = f.relative_to(skills_root)
            cat = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        except ValueError:
            cat = "(other)"
        by_cat[cat] = by_cat.get(cat, 0) + 1
        try:
            size = f.stat().st_size
        except OSError:
            size = 0
        if size > 20_000:
            oversized.append({"path": str(f), "bytes": size})
    oversized.sort(key=lambda x: -x["bytes"])
    return {
        "count": len(files),
        "by_category": dict(sorted(by_cat.items(), key=lambda kv: (-kv[1], kv[0]))),
        "oversized_gt_20k": oversized[:25],
    }


def _memory_pressure(root: Path) -> Dict[str, Any]:
    mem = root / "memories"
    out: Dict[str, Any] = {"exists": mem.is_dir(), "files": {}, "total_chars": 0}
    if not mem.is_dir():
        return out
    for name in ("MEMORY.md", "USER.md"):
        p = mem / name
        if p.is_file():
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            out["files"][name] = len(text)
            out["total_chars"] += len(text)
    out["soft_budget"] = dict(SOFT_BUDGET)
    out["over_soft_budget"] = {
        k: v > out["soft_budget"].get(k, 10**9) for k, v in out["files"].items()
    }
    return out


def _plugins(root: Path) -> Dict[str, Any]:
    candidates = [root / "plugins"]
    if root.name != ".hermes":
        candidates.append(root.parent / "plugins")
    if root.parent.name == "profiles":
        candidates.append(root.parent.parent / "plugins")
    seen = set()
    installed: List[str] = []
    for c in candidates:
        try:
            c = c.resolve() if c.exists() else c
        except OSError:
            continue
        if not c.is_dir() or str(c) in seen:
            continue
        seen.add(str(c))
        try:
            children = sorted(c.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir() and not child.name.startswith("."):
                installed.append(f"{child.name}@{c}")
    return {
        "install_roots_scanned": list(seen),
        "directories": installed,
        "count": len(installed),
    }


def _profiles(root: Path) -> Dict[str, Any]:
    profiles_dir = None
    if root.parent.name == "profiles":
        profiles_dir = root.parent
    elif (root / "profiles").is_dir():
        profiles_dir = root / "profiles"
    if not profiles_dir:
        return {"count": 0, "names": [], "note": "no profiles directory resolved"}
    try:
        entries = list(profiles_dir.iterdir())
    except OSError:
        return {"count": 0, "names": [], "note": "profiles directory unreadable"}
    names = sorted(
        p.name
        for p in entries
        if p.is_dir()
        and not p.name.startswith(".")
        and not p.name.endswith(".env")
        and " " not in p.name
    )
    clean = [n for n in names if n.replace("-", "").replace("_", "").isalnum()]
    return {"count": len(clean), "names": clean, "path": str(profiles_dir)}


def _config_snapshot(root: Path) -> Dict[str, Any]:
    cfg = root / "config.yaml"
    envp = root / ".env"
    snap: Dict[str, Any] = {
        "config_exists": cfg.is_file(),
        "env_exists": envp.is_file(),
        "model_default": None,
        "provider": None,
        "max_turns": None,
    }
    if not cfg.is_file():
        return snap
    try:
        text = cfg.read_text(encoding="utf-8")
    except OSError as e:
        snap["parse_error"] = str(e)
        return snap
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
    except Exception as e:
        snap["parse_error"] = str(e)
        return snap
    if not isinstance(data, dict):
        snap["parse_error"] = "config.yaml root must be a mapping"
        return snap
    model = data.get("model") or {}
    if isinstance(model, dict):
        snap["model_default"] = model.get("default")
        snap["provider"] = model.get("provider")
    elif isinstance(model, str):
        snap["model_default"] = model
    agent = data.get("agent") or {}
    if isinstance(agent, dict):
        snap["max_turns"] = agent.get("max_turns")
    comp = data.get("compression") or {}
    if isinstance(comp, dict):
        snap["compression"] = {
            "enabled": comp.get("enabled"),
            "threshold": comp.get("threshold"),
            "target_ratio": comp.get("target_ratio"),
        }
    return snap


def _gateway_hint(root: Path) -> Dict[str, Any]:
    pid = root / "gateway.pid"
    lock = root / "gateway.lock"
    state = root / "gateway_state.json"
    out: Dict[str, Any] = {
        "pid_file": pid.is_file(),
        "lock_file": lock.is_file(),
        "state_file": state.is_file(),
    }
    if state.is_file():
        try:
            size = state.stat().st_size
            if size > GATEWAY_STATE_MAX_BYTES:
                out["state_error"] = f"gateway_state.json too large ({size} bytes)"
            else:
                raw = json.loads(state.read_text(encoding="utf-8"))
                out["state"] = _redact_gateway_state(raw)
        except Exception as e:
            out["state_error"] = str(e)
    return out


_GATEWAY_SAFE_KEYS = (
    "status",
    "pid",
    "port",
    "host",
    "running",
    "started_at",
    "platform",
    "profile",
)


def _redact_gateway_state(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {"redacted": True, "note": "gateway_state.json is not an object"}
    safe = {k: raw[k] for k in _GATEWAY_SAFE_KEYS if k in raw}
    return {
        "redacted": True,
        "keys": sorted(str(k) for k in raw.keys()),
        "safe": safe,
    }


def _friction_flags(scan: Dict[str, Any]) -> List[Dict[str, str]]:
    flags: List[Dict[str, str]] = []
    skills = scan.get("skills") or {}
    if skills.get("count", 0) > 100:
        flags.append(
            {
                "id": "skill_sprawl",
                "severity": "high",
                "detail": f"{skills['count']} SKILL.md files — index pressure and curator debt.",
            }
        )
    if skills.get("oversized_gt_20k"):
        flags.append(
            {
                "id": "oversized_skills",
                "severity": "medium",
                "detail": f"{len(skills['oversized_gt_20k'])} skills >20KB (prompt-size tax when loaded).",
            }
        )
    mem = scan.get("memory") or {}
    if any(mem.get("over_soft_budget", {}).values()):
        flags.append(
            {
                "id": "memory_soft_budget",
                "severity": "medium",
                "detail": f"Memory over soft budget: {mem.get('files')}",
            }
        )
    plugins = scan.get("plugins") or {}
    if plugins.get("count", 0) == 0:
        flags.append(
            {
                "id": "no_user_plugins",
                "severity": "low",
                "detail": "No user plugin directories discovered under scanned roots.",
            }
        )
    cfg = scan.get("config") or {}
    if not cfg.get("config_exists"):
        flags.append(
            {
                "id": "missing_config",
                "severity": "critical",
                "detail": "config.yaml missing for this HERMES_HOME.",
            }
        )
    gw = scan.get("gateway") or {}
    if not gw.get("pid_file") and not gw.get("state_file"):
        flags.append(
            {
                "id": "gateway_quiet",
                "severity": "info",
                "detail": "No gateway pid/state in this home (may be CLI-only or parent gateway).",
            }
        )
    return flags


def scan(hermes_home: Optional[str] = None) -> Dict[str, Any]:
    root = resolve_hermes_home(hermes_home)
    result: Dict[str, Any] = {
        "ok": True,
        "version": __version__,
        "hermes_home": str(root),
        "exists": root.is_dir(),
        "skills": _count_skills(root),
        "memory": _memory_pressure(root),
        "plugins": _plugins(root),
        "profiles": _profiles(root),
        "config": _config_snapshot(root),
        "gateway": _gateway_hint(root),
    }
    result["friction"] = _friction_flags(result)
    result["metaphor"] = {
        "name": "fjord",
        "note": (
            "A fjord is a drowned glacial valley — deep, narrow, honest about bedrock. "
            "This scan prefers filesystem truth over aspirational status."
        ),
    }
    return result


def score(
    scan_result: Optional[Dict[str, Any]] = None, hermes_home: Optional[str] = None
) -> Dict[str, Any]:
    data = scan_result or scan(hermes_home)
    friction = data.get("friction") or []
    penalty = sum(SEVERITY_WEIGHT.get(f.get("severity", "info"), 0) for f in friction)
    health = max(0, min(100, 100 - penalty))
    credits = []
    if data.get("config", {}).get("config_exists"):
        credits.append("config_present")
    skills_n = (data.get("skills") or {}).get("count", 0)
    if 10 <= skills_n <= 80:
        credits.append("skills_in_healthy_band")
        health = min(100, health + 5)
    grade = (
        "A"
        if health >= 90
        else "B"
        if health >= 75
        else "C"
        if health >= 60
        else "D"
        if health >= 40
        else "F"
    )
    return {
        "ok": True,
        "version": __version__,
        "health_score": health,
        "grade": grade,
        "penalty": penalty,
        "credits": credits,
        "friction": friction,
        "hermes_home": data.get("hermes_home"),
        "summary": (
            f"Grade {grade} ({health}/100). "
            f"{len(friction)} friction flag(s). "
            f"Skills={skills_n}. "
            f"Profiles={(data.get('profiles') or {}).get('count')}."
        ),
        "recommendations": _recommendations(data, friction),
    }


def _recommendations(data: Dict[str, Any], friction: List[Dict[str, str]]) -> List[str]:
    recs: List[str] = []
    ids = {f["id"] for f in friction}
    if "skill_sprawl" in ids:
        recs.append(
            "Run hermes curator; pin critical skills; archive idle agent-created skills; split mega-skills into references/."
        )
    if "oversized_skills" in ids:
        recs.append(
            "Move branch-specific prose out of SKILL.md bodies; keep triggers under 57 chars in description."
        )
    if "memory_soft_budget" in ids:
        recs.append("Compress MEMORY.md via memory tool batch ops; drop stale task logs.")
    if "no_user_plugins" in ids:
        recs.append(
            "Install standalone plugins into ~/.hermes/plugins or profile plugins/; enable explicitly."
        )
    if "missing_config" in ids:
        recs.append("Run hermes setup / hermes config migrate for this profile.")
    if not recs:
        recs.append(
            "No critical structural debt detected by filesystem scan. Still run live hermes doctor for connectivity."
        )
    recs.append(
        "Always pair this scan with `hermes doctor` — connectivity and npm audit are out of band here."
    )
    return recs
