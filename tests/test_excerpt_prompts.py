import article_script_prompts as asp
import dossiers as d


def _group():
    a = {"url": "https://nyt.com/x", "title": "Egypt and Sudan sign border deal", "title_ar": "مصر والسودان توقعان اتفاق حدود",
         "domain": "nytimes.com", "seendate": "20261124T100000Z", "writer": "Jane Doe",
         "summary_ar": "مقتطف من صفحة الخبر", "summary_status": "page_teaser"}
    it = d.from_app_item(a, lambda dm: "نيويورك تايمز", lambda dm: "أمريكا", "t")
    r = d.run([it], [], 3, 2, None, topic="اختبار")
    return it, r["dossiers"][0]


def test_dossier_items_carry_excerpt_original_title_and_writer():
    it, g = _group()
    assert it["summary"] == "مقتطف من صفحة الخبر"
    assert it["orig_title"].startswith("Egypt") and it["writer"] == "Jane Doe"
    lines = "\n".join(d.item_lines(g["items"]))
    assert "العنوان الأصلي: Egypt" in lines and "الكاتب: Jane Doe" in lines and "مقتطف (مش النص كامل)" in lines


def test_every_dossier_prompt_asks_to_find_the_full_article():
    _it, g = _group()
    prompts = [d.prompt_for("الملف", g), d.script_prompt("الملف", g), d.script_prompt2("الملف", g), d.script_prompt3("الملف", g),
               d.explain_prompt("الملف", g), d.topic_prompt(g), d.eg_script_prompt(g)]
    for p in prompts:
        assert "دي عناوين ومقتطفات قصيرة، مش نص الخبر كامل" in p
        assert "باسم الكاتب" in p


def test_find_prompt_single_and_many():
    one = asp.build_find_prompt([{"title": "Deal", "url": "https://a.test", "outlet": "الجارديان", "writer": "X"}])
    assert "بين علامتين تنصيص" in one and "باسم الكاتب" not in one or "اسم الكاتب" in one
    assert "لقيته كامل / لقيت ملخص من مصدر تاني / ملقيتوش" in one
    assert "ممنوع تعدّي جدار الاشتراك" in one
    many = asp.build_find_prompt([{"title": "A", "url": "u1"}, {"title": "B", "url": "u2"}])
    assert "[1]" in many and "[2]" in many and "بيربط الأخبار دي ببعض" in many
