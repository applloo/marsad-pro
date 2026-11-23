import narrative_analysis as na


def test_groups_sources_by_domain_and_marks_independence_limit():
    report = na.compare_narratives([
        {"id":"1","title":"A","domain":"example.com","outlet":"Example","text":"قالت الوزارة إن الاتفاق تم اليوم"},
        {"id":"2","title":"B","url":"https://www.example.com/story","outlet":"Example 2","text":"قالت الوزارة إن الاتفاق لم يتم اليوم"},
    ])
    assert report["source_count"] == 1
    assert "لا تُحسب تلقائياً" in report["sources"][0]["independence_note"]


def test_candidate_is_not_a_truth_verdict():
    report = na.compare_narratives([
        {"id":"1","title":"A","domain":"a.test","text":"أكدت الوزارة وقوع الهجوم على الموقع صباح اليوم"},
        {"id":"2","title":"B","domain":"b.test","text":"نفت الوزارة وقوع الهجوم على الموقع صباح اليوم"},
    ], min_overlap=0.1)
    assert report["comparison_candidates"]
    assert "ليس إثباتاً" in report["comparison_candidates"][0]["caveat"]


def test_headlines_without_body_are_not_used_as_claims():
    report = na.compare_narratives([{"title":"هجوم جديد على الموقع","url":"https://a.test"}])
    assert report["usable_text_count"] == 0
    assert report["comparison_candidates"] == []


def test_prompt_requires_source_and_claim_separation():
    prompt = na.build_comparison_prompt({"title":"قضية اختبار"}, {"sources":[],"comparison_candidates":[]})
    assert "افحص استقلال المصادر" in prompt
    assert "لا تستنتج النوايا" in prompt
