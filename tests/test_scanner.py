"""Oppositional + unit tests for fjord scanner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scanner import scan, score, resolve_hermes_home


def test_resolve_default(tmp_path, monkeypatch):
    monkeypatch.delenv("HERMES_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    h = resolve_hermes_home()
    assert h == (tmp_path / ".hermes").resolve()


def test_scan_empty_home(tmp_path):
    home = tmp_path / "h"
    home.mkdir()
    data = scan(str(home))
    assert data["exists"] is True
    assert data["skills"]["count"] == 0
    assert any(f["id"] == "missing_config" for f in data["friction"])


def test_scan_with_skills_and_memory(tmp_path):
    home = tmp_path / "h"
    sk = home / "skills" / "devops" / "demo"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text("---\nname: demo\ndescription: x\n---\n\n" + ("body\n" * 5000))
    mem = home / "memories"
    mem.mkdir()
    (mem / "MEMORY.md").write_text("x" * 3000)
    (mem / "USER.md").write_text("y" * 100)
    (home / "config.yaml").write_text("model:\n  default: test\n  provider: x\n")
    data = scan(str(home))
    assert data["skills"]["count"] == 1
    assert data["skills"]["oversized_gt_20k"]
    assert data["memory"]["over_soft_budget"]["MEMORY.md"] is True
    s = score(data)
    assert s["grade"] in list("ABCDF")
    assert s["health_score"] < 100
    assert "skill" in s["summary"].lower() or "Friction" in s["summary"] or "friction" in json.dumps(s).lower()


def test_score_healthy_band(tmp_path):
    home = tmp_path / "h"
    home.mkdir()
    (home / "config.yaml").write_text("model: {default: m, provider: p}\n")
    skills = home / "skills" / "c"
    skills.mkdir(parents=True)
    for i in range(15):
        d = skills / f"s{i}"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: s\ndescription: d\n---\n\nok\n")
    s = score(hermes_home=str(home))
    assert s["health_score"] >= 75


def test_handlers_json():
    import importlib.util
    # load __init__ lightly via scanner only
    raw = scan(str(Path.home() / ".hermes" / "profiles" / "william"))
    assert "skills" in raw
    assert isinstance(raw["skills"]["count"], int)
