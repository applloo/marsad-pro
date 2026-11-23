import automated_workflow

def sample_case():
    return {
        "id": "case-37", "title": "قضية اختبار", "description": "اختبار سير العمل",
        "materials": [
            {"id": "m1", "title": "محادثات إيران وأمريكا", "text": "إيران والولايات المتحدة أعلنتا محادثات",
             "url": "https://one.example/a", "domain": "one.example", "date": "2026-11-23"},
            {"id": "m2", "title": "تغطية ثانية للمحادثات", "text": "الولايات المتحدة وإيران",
             "url": "https://two.example/b", "domain": "two.example", "date": "2026-11-23"},
        ],
        "claims": [{"id": "c1", "statement": "بدأت المحادثات", "type": "ادعاء", "status": "غير متحقق"}],
        "events": [],
    }

def test_first_run_initializes_baseline_and_builds_outputs():
    result = automated_workflow.run_case_workflow(sample_case(), {})
    assert result["initialized"]
    assert result["report"]["workflow"]["version"] == "8.37"
    assert result["report"]["material_count"] == 2
    assert result["analysis_prompt"]
    assert result["script_prompt"]
    assert result["report"]["workflow"]["live_collection_performed"] is False

def test_second_run_detects_new_material():
    first = automated_workflow.run_case_workflow(sample_case(), {})
    case = sample_case()
    case["materials"].append({"id": "m3", "title": "هجوم جديد", "text": "هجوم عسكري", "url": "https://three.example"})
    second = automated_workflow.run_case_workflow(case, first["store_data"])
    assert not second["initialized"]
    assert second["alerts"]
    assert second["alerts"][0]["new_materials"][0]["material_id"] == "m3"

def test_same_case_snapshot_does_not_duplicate_report():
    first = automated_workflow.run_case_workflow(sample_case(), {})
    second = automated_workflow.run_case_workflow(sample_case(), first["store_data"])
    assert second["duplicate_report"]
    assert len(second["store_data"]["intel_reports"]) == 1

def test_workflow_summary_discloses_no_live_collection():
    result = automated_workflow.run_case_workflow(sample_case(), {})
    summary = automated_workflow.build_run_summary(result)
    assert "لم يتم" in summary
    assert "الإنذار المبكر" in summary

def test_empty_case_reports_gaps_without_crashing():
    result = automated_workflow.run_case_workflow({"id":"empty","title":"فارغ","materials":[]}, {})
    assert result["report"]["material_count"] == 0
    assert result["report"]["verification_gaps"]
