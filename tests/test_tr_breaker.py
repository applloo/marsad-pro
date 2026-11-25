# -*- coding: utf-8 -*-
"""لو جوجل رافض/بطيء: الترجمة تريّح بعد كام فشل بدل ما تستنى ساعات"""
import core


def _setup(monkeypatch, fail=True):
    calls = {"n": 0}

    def net(*a, **k):
        calls["n"] += 1
        if fail:
            raise TimeoutError("google slow")
        return "مترجم"
    for name in ("_gtx", "_gtx_alt", "_gtx_mobile"):
        monkeypatch.setattr(core, name, net)
    monkeypatch.setattr(core, "GoogleTranslator", None)
    monkeypatch.setattr(core.time, "sleep", lambda *_: None)
    core._TR_CACHE.clear()
    monkeypatch.setitem(core._TR_STATE, "fails", 0)  # بيرجع زي ما كان بعد الاختبار
    monkeypatch.setitem(core._TR_STATE, "cool_until", 0.0)
    core.tr_stats_reset()
    return calls


def test_breaker_stops_hammering_google(monkeypatch):
    calls = _setup(monkeypatch)
    items = [{"title": f"Headline number {i}", "language": "English"} for i in range(300)]
    core.translate_titles(items)
    # من غير القاطع: 300 عنوان × محاولات = آلاف الطلبات. بالقاطع: كام طلب وبعدين يريّح
    assert calls["n"] < 40
    assert core.tr_cooling()
    assert core.TR_STATS["cools"] >= 1 and core.TR_STATS["skipped"] > 0
    assert items[0]["title_ar"] == "Headline number 0"  # بيفضل بلغته بدل ما يعلّق


def test_success_resets_and_translates(monkeypatch):
    _setup(monkeypatch, fail=False)
    assert core.tr("Hello world") == "مترجم"
    assert core.TR_STATS["ok"] == 1 and not core.tr_cooling()
    assert "نجحت 1" in core.tr_stats_line()


def test_cooling_expires(monkeypatch):
    _setup(monkeypatch, fail=False)
    core._TR_STATE["cool_until"] = core.time.time() - 1
    assert core.tr("Good morning") == "مترجم"
