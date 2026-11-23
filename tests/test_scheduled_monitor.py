import scheduled_monitor as m

def test_case_terms_include_tags_and_custom_terms():
    assert 'إيران' in m.terms_for({'title':'أزمة إقليمية','tags':['إيران'],'monitor_terms':'مضيق هرمز'})

def test_relevance_matches_arabic_and_english_terms():
    item={'title_ar':'تصعيد جديد في إيران'}
    assert m.relevant(item,['إيران'])
    assert not m.relevant(item,['الصين'])

def test_url_dedupe_ignores_tracking_query():
    assert m.item_key({'url':'https://example.com/a?utm_source=x'}) == m.item_key({'url':'https://example.com/a'})
