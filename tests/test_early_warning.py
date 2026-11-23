import early_warning


def case(cid='c1', materials=None):
    return {'id': cid, 'title': 'ملف إيران', 'description': 'متابعة التطورات', 'tags': ['إيران'], 'materials': materials or []}


def test_first_scan_sets_baseline_without_alert():
    state, alerts, initialized = early_warning.scan_cases([case()], {})
    assert not alerts
    assert initialized == ['ملف إيران']
    assert 'c1' in state['baselines']


def test_new_material_triggers_alert():
    initial, _, _ = early_warning.scan_cases([case()], {})
    changed = case(materials=[{'id': 'm1', 'title': 'تصريح جديد بشأن إيران', 'text': 'تهديد بضربة عسكرية', 'type': 'تصريح'}])
    state, alerts, _ = early_warning.scan_cases([changed], initial)
    assert len(alerts) == 1
    assert alerts[0]['new_materials'][0]['material_id'] == 'm1'
    assert 'تصعيد' in alerts[0]['new_materials'][0]['signals']


def test_daily_brief_mentions_limits():
    brief = early_warning.build_daily_brief([])
    assert 'لا يثبت صحة المحتوى' in brief


def test_prompt_has_caution_against_false_position_change():
    prompt = early_warning.build_analysis_prompt([])
    assert 'لا تستنتج ذلك من كلمة منفردة' in prompt


def test_changed_material_is_detected():
    initial, _, _ = early_warning.scan_cases([case(materials=[{'id': 'm1', 'title': 'تصريح', 'text': 'نص أول'}])], {})
    changed = case(materials=[{'id': 'm1', 'title': 'تصريح', 'text': 'نص معدل'}])
    state, alerts, _ = early_warning.scan_cases([changed], initial)
    assert alerts[0]['changed_materials'][0]['material_id'] == 'm1'
    assert 'text' in alerts[0]['changed_materials'][0]['changed_fields']


def test_claim_status_change_is_detected():
    initial_case = case()
    initial_case['claims'] = [{'id': 'cl1', 'statement': 'الادعاء', 'status': 'غير متحقق بعد', 'source': 'url'}]
    initial, _, _ = early_warning.scan_cases([initial_case], {})
    updated_case = case()
    updated_case['claims'] = [{'id': 'cl1', 'statement': 'الادعاء', 'status': 'مدعوم بمصادر مستقلة', 'source': 'url'}]
    state, alerts, _ = early_warning.scan_cases([updated_case], initial)
    assert alerts[0]['changed_claims'][0]['before']['status'] == 'غير متحقق بعد'
    assert alerts[0]['changed_claims'][0]['after']['status'] == 'مدعوم بمصادر مستقلة'


def test_event_change_is_detected():
    initial_case = case()
    initial_case['events'] = [{'id': 'e1', 'date': '2026-01-01', 'title': 'حدث', 'source': 'a'}]
    initial, _, _ = early_warning.scan_cases([initial_case], {})
    updated_case = case()
    updated_case['events'] = [{'id': 'e1', 'date': '2026-01-02', 'title': 'حدث', 'source': 'a'}]
    state, alerts, _ = early_warning.scan_cases([updated_case], initial)
    assert alerts[0]['changed_events'][0]['before']['date'] == '2026-01-01'
    assert alerts[0]['changed_events'][0]['after']['date'] == '2026-01-02'


def test_explicit_actor_position_change_is_flagged_for_review():
    initial = case(materials=[{'id': 'm1', 'title': 'تصريح أول', 'speaker': 'وزارة الخارجية', 'position': 'يرفض الاتفاق'}])
    baseline, _, _ = early_warning.scan_cases([initial], {})
    updated = case(materials=[
        {'id': 'm1', 'title': 'تصريح أول', 'speaker': 'وزارة الخارجية', 'position': 'يرفض الاتفاق'},
        {'id': 'm2', 'title': 'تصريح ثان', 'speaker': 'وزارة الخارجية', 'position': 'يقبل التفاوض'}
    ])
    state, alerts, _ = early_warning.scan_cases([updated], baseline)
    assert alerts[0]['stance_changes'][0]['actor'] == 'وزارة الخارجية'
    assert alerts[0]['severity'] == 'مراجعة مهمة'


def test_urgent_language_is_only_review_priority_not_event_verification():
    baseline, _, _ = early_warning.scan_cases([case()], {})
    updated = case(materials=[{'id': 'm9', 'title': 'عنوان عن ضربة محتملة', 'text': 'تحدث التقرير عن ضربة محتملة'}])
    state, alerts, _ = early_warning.scan_cases([updated], baseline)
    assert alerts[0]['severity'] == 'مراجعة عاجلة'
    assert 'لا يثبت' in alerts[0]['note']


def test_daily_brief_includes_changed_records():
    alert = {'case_title': 'ملف إيران', 'severity': 'مراجعة مهمة', 'changed_claims': [{'before': {'statement': 'س', 'status': 'قديم'}, 'after': {'statement': 'س', 'status': 'جديد'}}]}
    brief = early_warning.build_daily_brief([alert])
    assert 'تغير ادعاء' in brief
    assert 'قديم' in brief and 'جديد' in brief
