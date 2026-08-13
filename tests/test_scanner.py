"""Oppositional + unit tests for fjord scanner."""
from __future__ import annotations

import json
from pathlib import Path

from scanner import __version__, scan, score, resolve_hermes_home
import importlib.util


def _load_plugin():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "fjord_plugin", root / "__init__.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_resolve_default(tmp_path, monkeypatch):
    monkeypatch.delenv("HERMES_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    h = resolve_hermes_home()
    assert h == (tmp_path / ".hermes").resolve()


def test_resolve_rejects_null_byte():
    try:
        resolve_hermes_home("/tmp/bad\x00home")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_scan_empty_home(tmp_path):
    home = tmp_path / "h"
    home.mkdir()
    data = scan(str(home))
    assert data["ok"] is True
    assert data["version"] == __version__
    assert data["exists"] is True
    assert data["skills"]["count"] == 0
    assert any(f["id"] == "missing_config" for f in data["friction"])


def test_scan_missing_home(tmp_path):
    missing = tmp_path / "does-not-exist"
    data = scan(str(missing))
    assert data["exists"] is False
    assert data["skills"]["count"] == 0


def test_scan_with_skills_and_memory(tmp_path):
    home = tmp_path / "h"
    sk = home / "skills" / "devops" / "demo"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(
        "---\nname: demo\ndescription: x\n---\n\n" + ("body\n" * 5000)
    )
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
    blob = json.dumps(s).lower()
    assert "friction" in blob or "skill" in s["summary"].lower()


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
    assert "skills_in_healthy_band" in s["credits"]


def test_score_grade_boundaries():
    fake = {
        "hermes_home": "/tmp/x",
        "skills": {"count": 0},
        "config": {},
        "profiles": {"count": 0},
        "friction": [{"id": "missing_config", "severity": "critical"}],
    }
    s = score(fake)
    assert s["grade"] == "C"
    assert s["health_score"] == 60


def test_gateway_state_too_large(tmp_path):
    home = tmp_path / "h"
    home.mkdir()
    (home / "gateway_state.json").write_bytes(b"{" + (b"x" * 70_000) + b"}")
    data = scan(str(home))
    assert "too large" in data["gateway"].get("state_error", "")


def test_junk_profile_names_filtered(tmp_path):
    home = tmp_path / "h"
    profiles = home / "profiles"
    (profiles / "william").mkdir(parents=True)
    (profiles / "bad name").mkdir()
    (profiles / "foo.env").mkdir()
    data = scan(str(home))
    assert "william" in data["profiles"]["names"]
    assert "bad name" not in data["profiles"]["names"]


def test_handlers_json(tmp_path):
    home = tmp_path / "h"
    home.mkdir()
    (home / "config.yaml").write_text("model: demo\n")
    plug = _load_plugin()
    raw = json.loads(plug.handle_fjord_scan({"hermes_home": str(home)}))
    assert raw["ok"] is True
    assert raw["skills"]["count"] == 0
    scored = json.loads(plug.handle_fjord_score({"hermes_home": str(home)}))
    assert scored["ok"] is True
    assert scored["grade"] in list("ABCDF")


def test_handler_error_envelope():
    plug = _load_plugin()
    raw = json.loads(plug.handle_fjord_scan({"hermes_home": "/tmp/bad\x00x"}))
    assert raw["ok"] is False
    assert "error" in raw
    assert raw["version"] == __version__


def test_slash_version():
    plug = _load_plugin()
    raw = json.loads(plug._slash_fjord("version"))
    assert raw["ok"] is True
    assert raw["version"] == __version__
