from datetime import datetime, timezone, timedelta
import intelligence_pipeline as p

NOW = datetime(2026, 11, 23, 18, 0, tzinfo=timezone.utc)

def test_window_bounds_and_exact_six_hours():
    start, end = p.window_bounds(6, now=NOW)
    assert (end-start).total_seconds() == 21600
    rows = [
        {"title":"inside", "seendate":(NOW-timedelta(hours=5, minutes=59)).strftime('%Y%m%dT%H%M%SZ')},
        {"title":"outside", "seendate":(NOW-timedelta(hours=6, minutes=1)).strftime('%Y%m%dT%H%M%SZ')},
        {"title":"unknown"},
    ]
    got = p.filter_window(rows, 6, now=NOW)
    assert [x['title'] for x in got] == ['inside', 'unknown']
    assert got[1]['date_window_status'] == 'unknown_date'

def test_parse_iso_and_zulu():
    assert p.utc_dt('20261123T170000Z') == datetime(2026,11,23,17,tzinfo=timezone.utc)
    assert p.utc_dt('2026-11-23T17:00:00+00:00').hour == 17

def test_prepare_cards_translates_snippets_and_marks_missing():
    rows = [{'title':'A','snippet':'English snippet'}, {'title':'B'}]
    out = p.prepare_cards(rows, translate_text=lambda xs: ['مقتطف مترجم'])
    assert out[0]['summary_ar'] == 'مقتطف مترجم'
    assert out[0]['summary_status'] == 'translated_snippet'
    assert out[1]['summary_status'] == 'missing_snippet'

def test_prepare_cards_does_not_claim_full_article():
    out = p.prepare_cards([{'title':'A','description':'Only excerpt'}], lambda xs:['ترجمة مقتطف'])
    assert 'ترجمة مقتطف' in out[0]['summary_ar']
    assert out[0]['summary_status'] == 'translated_snippet'

def test_clusters_keep_all_sources_and_mark_counts():
    rows=[{'title':'Iran nuclear talks','title_ar':'مفاوضات إيران النووية','domain':'a.com','url':'https://a.com/1'},
          {'title':'Iran nuclear talks update','title_ar':'تطورات مفاوضات إيران النووية','domain':'b.com','url':'https://b.com/2'},
          {'title':'Football match','title_ar':'مباراة كرة قدم','domain':'c.com','url':'https://c.com/3'}]
    groups=p.cluster_items(rows)
    assert sum(g['count'] for g in groups) == 3
    assert any(g['count']==2 and len(g['domains'])==2 for g in groups)

def test_canonical_url_removes_tracking_query():
    assert p.canonical_url('https://WWW.Example.com/story/?utm_source=x') == 'https://example.com/story'

def test_invalid_primary_date_falls_back_to_valid_published_date():
    row = {'title': 'fallback', 'seendate': 'not-a-date', 'published_at': '2026-11-23T17:00:00Z'}
    got = p.filter_window([row], 6, now=NOW)
    assert len(got) == 1
    assert got[0]['date_window_status'] == 'within_window'
    assert got[0]['date_window_field'] == 'published_at'

def test_first_valid_date_outside_window_is_not_rescued_by_later_field():
    row = {'title': 'old', 'seendate': '2026-11-23T10:00:00Z', 'published_at': '2026-11-23T17:00:00Z'}
    assert p.filter_window([row], 6, now=NOW) == []
