# -*- coding: utf-8 -*-
import dictionary as d


def test_default_has_groups_and_rows():
    x = d.clean(d.default())
    assert [g["name"] for g in x["groups"]][:3] == ["🌍 البلدان", "📍 أماكن ومناطق", "👤 الشخصيات"]
    assert sum(len(g["rows"]) for g in x["groups"]) > 60


def test_merge_line_no_duplicates():
    assert d.merge_line("ليبي، Liby", "liby, حفتر") == "ليبي، Liby، حفتر"
    assert d.merge_line("", "") == ""


def test_clean_drops_empty_rows_and_bad_groups():
    x = d.clean({"groups": [{"name": "x", "rows": [{"name": "", "line": "a"}, {"name": "b", "line": "1,2"}, None]}, {"name": ""}]})
    assert x == {"version": 1, "groups": [{"name": "x", "rows": [{"name": "b", "note": "", "line": "1، 2"}]}]}


def test_search_finds_hebrew_and_english():
    x = d.default()
    assert any(r["name"] == "حفتر" for _g, r in d.search(x, "haftar"))
    assert any(r["name"] == "ليبيا" for _g, r in d.search(x, "לוב"))
