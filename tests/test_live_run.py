# -*- coding: utf-8 -*-
import gh_actions


class _R:
    def __init__(self, data):
        self._d = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


def test_run_steps_flattens_jobs(monkeypatch):
    data = {"jobs": [{"steps": [{"name": "① التقرير اليومي", "status": "completed", "conclusion": "success"},
                                {"name": "② البحث الشامل", "status": "in_progress", "conclusion": None}]}]}
    monkeypatch.setattr(gh_actions.requests, "get", lambda *a, **k: _R(data))
    s = gh_actions.run_steps("t", "a/b", 5)
    assert [x["status"] for x in s] == ["completed", "in_progress"]
    assert s[0]["name"].startswith("①")


def test_last_run_has_id(monkeypatch):
    data = {"workflow_runs": [{"id": 9, "status": "queued", "html_url": "u", "created_at": "2026-11-25T10:00:00Z"}]}
    monkeypatch.setattr(gh_actions.requests, "get", lambda *a, **k: _R(data))
    assert gh_actions.last_run("t", "a/b", "all.yml")["id"] == 9
    assert gh_actions.workflow_page("a/b", "all.yml") == "https://github.com/a/b/actions/workflows/all.yml"
