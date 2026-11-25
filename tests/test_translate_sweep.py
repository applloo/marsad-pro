# -*- coding: utf-8 -*-
import time

import core
import translate_sweep as ts


def _res():
    return {"us": {"items": [{"url": "u1", "title": "Big news", "title_ar": "Big news"},
                             {"url": "u2", "title": "خبر", "title_ar": "خبر"},
                             {"url": "u3", "title": "Other", "title_ar": "Other", "teaser": "Short teaser",
                              "summary_status": "page_teaser_untranslated"}]},
            "meta": "x"}


def test_sweep_translates_only_missing(monkeypatch):
    monkeypatch.setattr(core, "_batch_tr", lambda texts, dest: ["عربي " + t for t in texts])
    monkeypatch.setitem(core._TR_STATE, "cool_until", 0.0)
    res = _res()
    fixed = ts.sweep(res, time.time() + 60, log=lambda m: None)
    assert fixed == {"us": 2}
    it = res["us"]["items"]
    assert it[0]["title_ar"] == "عربي Big news" and it[1]["title_ar"] == "خبر"
    assert it[2]["summary_status"] == "page_teaser" and it[2]["summary_ar"].startswith("عربي")


def test_sweep_stops_when_google_blocks(monkeypatch):
    monkeypatch.setattr(core, "_batch_tr", lambda texts, dest: list(texts))
    monkeypatch.setitem(core._TR_STATE, "cool_until", time.time() + 100)
    logs = []
    assert ts.sweep(_res(), time.time() + 60, log=logs.append) == {"us": 0}
    assert any("رفض" in m for m in logs)


def test_merge_keeps_newer_data(monkeypatch):
    saved = {}
    cur = {"us": {"items": [{"url": "u1", "title": "Big news", "title_ar": "Big news", "extra": 1}]},
           "eg": {"items": [{"url": "z", "title": "x"}]}}
    monkeypatch.setattr(ts.store, "load_file", lambda *a, **k: cur)
    monkeypatch.setattr(ts.store, "save_file", lambda t, g, n, d: saved.update(d))
    res = {"us": {"items": [{"url": "u1", "title": "Big news", "title_ar": "خبر كبير"}]}}
    assert ts._merge_save("t", "g", res)
    assert saved["us"]["items"][0]["title_ar"] == "خبر كبير" and saved["us"]["items"][0]["extra"] == 1
    assert "eg" in saved
