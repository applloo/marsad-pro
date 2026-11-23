import stance_scenarios as ss


def test_compare_stances_groups_same_author_and_orders_dates():
    case = {"materials": [
        {"author": "Analyst A", "date": "2026-02-01", "stance": "يدعم التفاوض", "title": "قديم"},
        {"author": "Analyst A", "date": "2026-03-01", "stance": "يرفض التفاوض", "title": "حديث"},
        {"author": "Analyst B", "date": "2026-03-01", "stance": "محايد", "title": "مادة"},
    ]}
    result = ss.compare_stances(case)
    assert len(result) == 1
    assert result[0]["changed"] is True
    assert result[0]["first"]["title"] == "قديم"
    assert result[0]["latest"]["title"] == "حديث"


def test_no_inference_without_manual_stance():
    assert ss.compare_stances({"materials": [{"author": "A", "title": "عنوان مثير"}]}) == []


def test_identical_stance_is_not_marked_changed():
    case = {"materials": [
        {"outlet": "Paper", "date": "2026-01-01", "stance": "يدعم المسار الدبلوماسي"},
        {"outlet": "Paper", "date": "2026-02-01", "stance": "  يدعم المسار الدبلوماسي "},
    ]}
    assert ss.compare_stances(case)[0]["changed"] is False


def test_scenario_worksheet_has_three_conditional_paths():
    record = ss.build_scenarios({"id": "c1", "title": "ملف"}, ["عامل أول", "عامل ثان"], "30 يوماً")
    assert len(record["scenarios"]) == 3
    assert record["drivers"] == ["عامل أول", "عامل ثان"]
    assert "ليست تنبؤات" in record["caveat"]


def test_scenario_prompt_uses_case_materials():
    case = {"title": "ملف الاختبار", "materials": [{"date": "2026-01-01", "title": "خبر", "outlet": "مصدر"}]}
    record = ss.build_scenarios(case, ["المفاوضات"])
    prompt = ss.build_scenario_prompt(record, case)
    assert "ملف الاختبار" in prompt
    assert "المفاوضات" in prompt
    assert "خبر" in prompt
