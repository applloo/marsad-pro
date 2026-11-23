# -*- coding: utf-8 -*-
"""Phase 8.37: one-click, auditable case workflow over already-collected material.

This module never claims to fetch live news. It orchestrates the evidence already
stored in a case, updates its monitoring baseline, and prepares reports/prompts.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json

def _stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _fingerprint(case):
    payload = {
        "materials": [(x.get("url") or x.get("id") or x.get("title"), x.get("date"), x.get("title"), x.get("text")) for x in case.get("materials", [])],
        "claims": case.get("claims", []), "events": case.get("events", [])
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()

def run_case_workflow(case, store_data=None, *, report_type="تقرير استخباراتي شامل للقضية"):
    """Run local workflow stages deterministically; caller persists returned state/report."""
    import early_warning
    import relationship_network
    import narrative_analysis
    import intelligence_reports

    case = dict(case or {})
    materials = [dict(x) for x in (case.get("materials") or []) if isinstance(x, dict)]
    normalized_case = {**case, "materials": materials}
    data = dict(store_data or {})
    ew_state = dict(data.get("early_warning") or {})
    prior_reports = list(ew_state.get("reports") or [])

    # A baseline is initialized on first run. Subsequent runs detect additions/changes.
    ew_state, alerts, initialized = early_warning.scan_cases([normalized_case], ew_state)
    network = relationship_network.build_network(materials, cases=[normalized_case])
    narrative = narrative_analysis.compare_narratives(materials, claims=case.get("claims") or [])
    report = intelligence_reports.build_report(
        normalized_case, report_type, alerts=alerts[-30:], network=network, narrative=narrative
    )
    report["workflow"] = {
        "version": "8.37",
        "ran_at": _stamp(),
        "stages": [
            {"name": "مواد القضية", "state": "done", "count": len(materials)},
            {"name": "الإنذار المبكر", "state": "baseline_initialized" if initialized else "scanned", "count": len(alerts)},
            {"name": "شبكة الأطراف", "state": "done", "count": len(network.get("nodes", []))},
            {"name": "مقارنة الروايات", "state": "done", "count": len(narrative.get("source_map", {}))},
            {"name": "التقرير", "state": "done", "count": 1},
        ],
        "live_collection_performed": False,
        "case_fingerprint": _fingerprint(normalized_case),
    }
    report["automation_alerts"] = alerts
    report["baseline_initialized"] = initialized
    report["network_summary"] = {
        "nodes": len(network.get("nodes", [])),
        "edges": len(network.get("edges", [])),
        "caveat": "الروابط تعني ظهوراً مشتركاً في مادة مصدرية، ولا تثبت علاقة فعلية."
    }
    report["narrative_summary"] = {
        "sources": len(narrative.get("sources", {})),
        "potential_tensions": len(narrative.get("tensions", [])),
        "caveat": "مرشحات الاختلاف تحتاج مراجعة بشرية ولا تحسم صحة أي رواية."
    }
    # Only append new report if the same case+fingerprint+type has not already been saved.
    existing = list(data.get("intel_reports") or [])
    duplicate = next((x for x in existing if x.get("case_id") == case.get("id")
                       and (x.get("workflow") or {}).get("case_fingerprint") == report["workflow"]["case_fingerprint"]
                       and x.get("report_type") == report_type), None)
    if duplicate:
        report = duplicate
    else:
        existing.append(report)
    data["intel_reports"] = existing[-500:]
    data["early_warning"] = ew_state
    return {
        "store_data": data,
        "report": report,
        "alerts": alerts,
        "initialized": initialized,
        "network": network,
        "narrative": narrative,
        "analysis_prompt": intelligence_reports.build_analysis_prompt(report),
        "script_prompt": intelligence_reports.build_script_prompt(report),
        "fingerprint": report["workflow"]["case_fingerprint"],
        "duplicate_report": bool(duplicate),
    }

def build_run_summary(result):
    r = result or {}
    report = r.get("report") or {}
    stages = (report.get("workflow") or {}).get("stages") or []
    lines = [
        "# ملخص تشغيل دورة البحث 8.37",
        f"- القضية: {report.get('case_title', 'غير محددة')}",
        f"- وقت التشغيل: {(report.get('workflow') or {}).get('ran_at', 'غير محدد')}",
        f"- المواد: {report.get('material_count', 0)}",
        f"- التنبيهات: {len(r.get('alerts') or [])}",
        f"- الكيانات: {len((r.get('network') or {}).get('nodes', []))}",
        f"- المصادر في مقارنة الروايات: {len(((r.get('narrative') or {}).get('source_map') or {}))}",
        "- جمع حي من الإنترنت: لم يتم في هذا التشغيل؛ جرى تحليل المواد المحفوظة فقط.",
        "",
        "## المراحل",
    ]
    for stage in stages:
        lines.append(f"- {stage.get('name')}: {stage.get('state')} ({stage.get('count', 0)})")
    lines += ["", "## حدود التشغيل", "- لا يعني رصد التغير إثبات صحة المعلومة.",
              "- الروابط في الشبكة تعني ظهوراً مشتركاً فقط.",
              "- يلزم تشغيل البحث الحي بشكل مستقل لإضافة أخبار جديدة قبل إعادة التحليل."]
    return "\n".join(lines)
