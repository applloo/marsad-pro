# -*- coding: utf-8 -*-
"""9.17: برومبتات المقالات المدفوعة"""
import article_script_prompts as asp
import dossiers
import prompt_style

U = "https://www.haaretz.com/us-news/2026-11-19/ty-article-magazine/.premium/hot-zionist-or-free-palestine-the-dating-politics/0000-01a1-f471"


def test_slug_words_takes_title_from_link():
    assert asp.slug_words(U) == "hot zionist or free palestine the dating politics"
    assert asp.slug_words("https://x.test/") == ""


def test_paywall_prompt_has_title_author_slug_and_rule():
    p = asp.build_paywall_prompt({"title": "Hot Zionist?", "url": U, "outlet": "هآرتس", "writer": "Grace Gilson"})
    for part in ("Hot Zionist?", "Grace Gilson", "هآرتس", "hot zionist or free palestine", "مهم عن المقالات المدفوعة", "ممنوع تعدّي جدار الاشتراك"):
        assert part in p


def test_rule_reaches_every_shared_prompt_block():
    assert "مهم عن المقالات المدفوعة" in dossiers.EXCERPT_RULE
    assert "مهم عن المقالات المدفوعة" in prompt_style.source_block()
    assert "مهم عن المقالات المدفوعة" in asp.build_script_prompt([{"title": "A", "url": "u"}])


def test_find_prompt_flags_paid_items_only():
    assert "مهم عن المقالات المدفوعة" in asp.build_find_prompt([{"title": "A", "url": U, "paywalled": True}])
    assert "طبّق قاعدة المقالات المدفوعة" not in asp.build_find_prompt([{"title": "A", "url": "https://a.test/x"}])
