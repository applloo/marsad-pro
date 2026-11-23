import intelligence_reports as reports


def sample_case():
    return {"id":"c1", "title":"اختبار القضية", "materials":[
        {"id":"m1", "title":"خبر أول", "url":"https://a.example/x", "outlet":"A", "domain":"a.example", "date":"2026-11-23", "text":"نص متاح", "type":"خبر"},
        {"id":"m2", "title":"خبر ثان", "url":"https://b.example/y", "outlet":"B", "domain":"b.example", "date":"2026-11-22", "text":"نص آخر", "type":"تحليل"}],
        "claims":[{"statement":"ادعاء تجريبي", "type":"ادعاء منسوب", "status":"غير متحقق بعد", "source":"https://a.example/x"}],
        "events":[{"date":"2026-11-22", "title":"حدث تجريبي"}]}


def test_report_preserves_provenance_and_counts():
    r=reports.build_report(sample_case())
    assert r['material_count']==2 and len(r['sources'])==2
    assert r['sources'][0]['url'].startswith('https://')
    assert r['claims'][0]['evidence_status']=='غير متحقق بعد'
    assert r['case_id']=='c1'


def test_missing_text_and_sources_are_flagged():
    c=sample_case(); c['materials']=[{"title":"عنوان فقط"}]
    r=reports.build_report(c)
    assert any('العناوين وحدها' in x for x in r['verification_gaps'])
    assert any('روابط أصلية' in x for x in r['verification_gaps'])


def test_prompts_include_caveats_and_script_requirements():
    r=reports.build_report(sample_case())
    p=reports.build_analysis_prompt(r)
    s=reports.build_script_prompt(r)
    assert 'لا تعتبر تكرار الخبر تأكيداً مستقلاً' in p
    assert 'سكريبتاً باللهجة المصرية' in p
    assert 'مصادره' in s


def test_save_is_idempotent_and_bounded():
    store={}; r=reports.build_report(sample_case())
    assert reports.save_report(store,r)
    assert not reports.save_report(store,r)
    assert len(store['intel_reports'])==1
