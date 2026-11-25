import search_job


def test_writer_search_applies_date_filter_and_card_translation(monkeypatch):
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)  # كان تاريخ ثابت فالاختبار بيفشل بعد يومين
    recent = (now - timedelta(hours=2)).strftime('%Y%m%dT%H%M%SZ')
    old = (now - timedelta(days=5)).strftime('%Y%m%dT%H%M%SZ')
    monkeypatch.setattr(search_job, 'WRITERS', [
        {'country': 'US', 'name_ar': 'كاتب', 'name_en': 'Writer', 'default': True, 'kind': 'رأي'}
    ])
    monkeypatch.setattr(search_job.core, 'fetch_writers', lambda *a, **k: ([
        {'writer': 'كاتب', 'title': 'Recent', 'url': 'https://a.test/r', 'seendate': recent, 'snippet': 'A recent snippet', 'domain': 'a.test'},
        {'writer': 'كاتب', 'title': 'Old', 'url': 'https://a.test/o', 'seendate': old, 'snippet': 'An old snippet', 'domain': 'a.test'},
    ], []))
    monkeypatch.setattr(search_job.core, 'translate_titles', lambda items: items)
    monkeypatch.setattr(search_job.core, '_batch_tr', lambda texts, dest: ['مقتطف حديث' for _ in texts])
    result = search_job.search_writers('wr', ['US'], [], {'days': 1}, [], None)
    assert [x['title'] for x in result['items']] == ['Recent']
    assert result['items'][0]['summary_ar'] == 'مقتطف حديث'
    assert result['items'][0]['date_window_status'] == 'within_window'
