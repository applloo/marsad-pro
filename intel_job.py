# -*- coding: utf-8 -*-
"""تحديث الأقسام الذكية تلقائياً على GitHub Actions (من غير ذكاء اصطناعي ومن غير تكلفة).
بيشتغل لوحده بعد ما «البحث الشامل» يخلص كل يوم، أو بزر من التطبيق. بيعمل:
1) رادار التقارير المدفوعة: يجمع عناوين آخر 24 ساعة من المصادر المدفوعة الأساسية ويترجمها.
2) تجميع الأحداث والروايات: يربط أخبار البحث الشامل المتقاربة في مجموعات ويقارن زاوية كل جهة.
3) الكيانات والتناقضات: يستخرج الأسماء والخط الزمني ومرشحات التناقض ويربطها بملفاتك البحثية.
4) الإنذار المبكر: يقارن ملفات القضايا بآخر فحص تلقائي ويطلع التغييرات.
5) صحة المصادر: فحص المصادر الأساسية مرة كل 3 أيام.
كل نتيجة بتتحفظ في ملف لوحدها في الـGist (marsad_auto_intel.json)، ومابتلمسش بياناتك اللي بتعدلها من التطبيق.
"""
import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone

import core
import early_warning as early_warning_mod
import entity_intelligence as entity_intel_mod
import paid_radar as paid_radar_mod
import source_intelligence as source_intel_mod
import store

OUT, RES = "marsad_auto_intel.json", "marsad_results.json"
SCOPES = ["il", "us", "uk", "rg", "eg", "wr", "wa"]
HEALTH_EVERY_DAYS = 3
PRIORITY_HEALTH = ["Reuters", "BBC", "The Guardian", "The New York Times", "The Washington Post", "Haaretz (عبري)",
                   "هآرتس (إنجليزي)", "Ynetnews (إنجليزي)", "The Times of Israel", "Al-Monitor", "Middle East Eye",
                   "Al Jazeera English", "اليوم السابع", "المصري اليوم", "الشروق", "مدى مصر"]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _age_days(iso):
    try:
        t = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - t).total_seconds() / 86400
    except Exception:
        return 999


def step(out, name, fn):
    """كل خطوة لوحدها: لو واحدة فشلت الباقي يكمل، والخطأ بيتسجل عشان يظهر في التطبيق"""
    t0 = time.time()
    try:
        fn()
        out["steps"].setdefault(name, {"ok": True, "seconds": int(time.time() - t0)})
        print(f"✅ {name} ({int(time.time() - t0)}ث)", flush=True)
    except Exception as e:
        out["steps"][name] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300], "seconds": int(time.time() - t0)}
        print(f"❌ {name}: {e}", flush=True)
        traceback.print_exc()


def main():
    tok, gid = os.getenv("GIST_TOKEN"), os.getenv("GIST_ID")
    if not (tok and gid):
        sys.exit("GIST_TOKEN و GIST_ID مطلوبان (من Settings ← Secrets and variables ← Actions)")
    prev = store.load_file(tok, gid, OUT, {}) or {}
    out = {**prev, "state": "running", "started": now_iso(), "steps": {}}
    store.save_file(tok, gid, OUT, out)

    results = store.load_file(tok, gid, RES, {}) or {}
    pool, seen = [], set()
    for k in SCOPES:
        for a in (results.get(k) or {}).get("items", []):
            u = (a.get("url") or "").split("?")[0].rstrip("/") if isinstance(a, dict) else ""
            if u and u not in seen:
                seen.add(u)
                pool.append(a)
    out["pool_size"] = len(pool)
    try:
        data = store.load(tok, gid)
    except Exception:
        data = {}
    cases = data.get("research_cases") or []

    def paid():
        names = [x[0] for x in paid_radar_mod.PAID_SOURCES if x[0] in set(paid_radar_mod.AUTO_DEFAULTS)]
        items, notes = paid_radar_mod.search_paid_headlines(names, 1, None, max_items=120)
        core.translate_titles(items)
        out["paid"] = {"items": items, "notes": notes, "days": 1, "at": now_iso()}

    def clusters():
        arts = [source_intel_mod.normalize_article(a) for a in pool[:400] if isinstance(a, dict) and a.get("title")]
        groups = source_intel_mod.cluster_articles(arts)
        d = source_intel_mod.build_case_dossier("حصيلة البحث الشامل الأخير", arts, groups)
        d["title_ar"] = f"حصيلة تلقائية · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        d["auto"] = True
        out["dossier"] = entity_intel_mod.enrich_dossier(d, cases)

    def warning():
        st_ = prev.get("warning_state") or {"baselines": {}, "reports": [], "last_scan": ""}
        updated, alerts, initialized = early_warning_mod.scan_cases(cases, st_)
        updated["reports"] = (updated.get("reports") or [])[:20]
        out["warning_state"] = updated
        out["warning"] = {"alerts": alerts, "initialized": initialized, "at": now_iso(),
                          "brief": early_warning_mod.build_daily_brief(alerts) if alerts else ""}

    def health():
        if _age_days((prev.get("health") or {}).get("checked_at")) < HEALTH_EVERY_DAYS:
            out["steps"]["صحة المصادر"] = {"ok": True, "skipped": True}
            return
        names = [x["name"] for x in source_intel_mod.SOURCE_CATALOG if x["name"] in set(PRIORITY_HEALTH)] or None
        res = source_intel_mod.scan_sources(names, timeout=10)
        out["health"] = source_intel_mod.compare_health_runs(res, prev.get("health"))

    step(out, "رادار التقارير المدفوعة", paid)
    if pool:
        step(out, "تجميع الأحداث والكيانات", clusters)
    else:
        out["steps"]["تجميع الأحداث والكيانات"] = {"ok": False, "error": "مفيش نتايج بحث شامل محفوظة لسه"}
    step(out, "الإنذار المبكر", warning)
    step(out, "صحة المصادر", health)
    out["state"] = "done"
    out["finished"] = now_iso()
    body = json.loads(json.dumps(out, ensure_ascii=False, default=str))
    for attempt in range(3):
        try:
            store.save_file(tok, gid, OUT, body)
            break
        except Exception as e:
            print("save retry", e, flush=True)
            time.sleep(3)
    print("تم", flush=True)


if __name__ == "__main__":
    main()
