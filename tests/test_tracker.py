import json
from pathlib import Path

import pytest

from costcopilot import tracker

ROOT = Path(__file__).resolve().parents[1]


def test_real_plan_is_valid():
    plan = tracker.load_plan(ROOT / "docs" / "project-plan" / "plan.json")
    done, total = tracker.progress(plan)
    assert 0 < done <= total


def test_rejects_unknown_skill():
    plan = {"skill_catalog": {"A": "x"},
            "phases": [{"tasks": [{"id": "1", "status": "done", "skills": ["B"]}]}]}
    with pytest.raises(ValueError, match="not in catalog"):
        tracker.validate(plan)


def test_rejects_bad_status_and_duplicates():
    base = {"skill_catalog": {"A": "x"}}
    bad_status = {**base, "phases": [{"tasks": [{"id": "1", "status": "wip", "skills": []}]}]}
    dup = {**base, "phases": [{"tasks": [
        {"id": "1", "status": "done", "skills": []},
        {"id": "1", "status": "done", "skills": []}]}]}
    with pytest.raises(ValueError, match="invalid status"):
        tracker.validate(bad_status)
    with pytest.raises(ValueError, match="duplicate"):
        tracker.validate(dup)


def test_build_writes_files_without_git_history(tmp_path):
    folder = tmp_path / "docs" / "project-plan"
    folder.mkdir(parents=True)
    plan = {"project": "Demo", "skill_catalog": {"Python": "Programming"},
            "phases": [{"id": 1, "name": "P", "tasks": [
                {"id": "1.1", "title": "t", "status": "done", "skills": ["Python"]},
                {"id": "1.2", "title": "u", "status": "planned", "skills": ["Python"]}]}]}
    (folder / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    tracker.build(tmp_path)

    assert "1/2 tasks (50%)" in (folder / "PLAN.md").read_text(encoding="utf-8")
    assert "| Python | 1 | 1 |" in (folder / "SKILLS.md").read_text(encoding="utf-8")
    assert "No commits yet." in (folder / "ACTIVITY_LOG.md").read_text(encoding="utf-8")
