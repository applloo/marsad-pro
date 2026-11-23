import article_reader


def test_empty_and_tiny_text_are_insufficient():
    result = article_reader.inspect_article("قصير")
    assert result["status"] == "insufficient"
    assert result["summary_allowed"] is False


def test_paywall_marker_marks_possible_partial_even_if_long():
    text = ("هذه مادة صحفية طويلة ومفصلة. " * 100) + "Subscribe to continue reading"
    result = article_reader.inspect_article(text)
    assert result["status"] == "possibly_partial"
    assert result["paywall_signal"] is True


def test_long_text_is_usable_but_not_verified_complete():
    result = article_reader.inspect_article("جملة صحفية مفيدة. " * 150)
    assert result["status"] == "usable_unverified"
    assert "غير مؤكد" in result["label"]
    assert result["summary_allowed"] is True
    assert result["words"] > 100


def test_metadata_does_not_invent_author_or_date():
    rows = dict(article_reader.metadata_rows({"authors": [], "date": "", "via": "direct"}))
    assert rows["الكاتب"] == "غير متاح في النص المستخرج"
    assert rows["تاريخ النشر"] == "غير متاح في النص المستخرج"
    assert rows["طريقة الاستخراج"] == "direct"
