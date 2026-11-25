# -*- coding: utf-8 -*-
"""تكملة الترجمة بعد البحث الشامل (بيشتغل على جهاز GitHub تاني).
ليه؟ جوجل بيوقف الترجمة لجهاز البحث بعد ~70 طلب (شفناها في السجل: il اترجمت كلها وبعدها us/uk/rg/wr «اتسابت بلغتها»).
الجهاز ده عنوانه مختلف، فجوجل بيرد عليه. بيترجم العناوين والمقتطفات اللي فضلت إنجليزي/عبري في marsad_results.json
ويحفظها، عشان تفتح المرصد تلاقيها عربي على طول. ليه أقصى وقت، ولو جوجل رفض تاني بيوقف ويسيبها زي ما هي."""
import job_guard
import json
import os
import sys
import time

import core
import store

RES = "marsad_results.json"
BUDGET_MIN = float(os.getenv("SWEEP_MIN") or 12)


def _need_title(a):
    return (isinstance(a, dict) and (a.get("title") or "").strip()
            and not core._HAS_AR.search(a.get("title_ar") or "") and not core._HAS_AR.search(a.get("title") or ""))


def _need_teaser(a):
    return isinstance(a, dict) and a.get("summary_status") == "page_teaser_untranslated" and (a.get("teaser") or "").strip()


def sweep(res, deadline, log=print):
    """بيترجم في res نفسها. بيرجع {القسم: عدد اللي اتصلح}"""
    fixed = {}
    for key, v in res.items():
        if not isinstance(v, dict) or not isinstance(v.get("items"), list):
            continue
        n = 0
        titles = [a for a in v["items"] if _need_title(a)]
        for i in range(0, len(titles), 24):
            if time.time() > deadline or core.tr_cooling():
                break
            part = titles[i:i + 24]
            for a, t in zip(part, core._batch_tr([a["title"] for a in part], "ar")):
                if t and core._HAS_AR.search(t):
                    a["title_ar"] = t
                    n += 1
        teas = [a for a in v["items"] if _need_teaser(a)]
        if teas and time.time() < deadline and not core.tr_cooling():
            for a, t in zip(teas, core._batch_tr([a["teaser"] for a in teas], "ar")):
                if t and core._HAS_AR.search(t):
                    a["summary_ar"], a["summary_status"] = t, "page_teaser"
        left = sum(1 for a in v["items"] if _need_title(a))
        log(f"{key}: اتترجم {n} عنوان، فاضل بلغته {left}")
        fixed[key] = n
        if time.time() > deadline:
            log("⏰ الوقت المسموح خلص — الباقي المرصد بيترجمه وإنت بتفتحه")
            break
        if core.tr_cooling():
            log("⛔ جوجل رفض الجهاز ده كمان — وقفنا وسبنا الباقي بلغته")
            break
    return fixed


def _merge_save(tok, gid, res):
    """بنقرا النسخة الأحدث قبل الحفظ ونحط الترجمة بس (بالرابط)، عشان مانمسحش حاجة اتحفظت في النص"""
    tr_map = {}
    for key, v in res.items():
        for a in (v.get("items") or []) if isinstance(v, dict) else []:
            if isinstance(a, dict) and a.get("url"):
                tr_map[(key, a["url"])] = a
    for attempt in range(4):
        try:
            cur = store.load_file(tok, gid, RES, {}) or {}
            for key, v in cur.items():
                for a in (v.get("items") or []) if isinstance(v, dict) else []:
                    src = tr_map.get((key, a.get("url"))) if isinstance(a, dict) else None
                    if not src:
                        continue
                    if core._HAS_AR.search(src.get("title_ar") or "") and not core._HAS_AR.search(a.get("title_ar") or ""):
                        a["title_ar"] = src["title_ar"]
                    if src.get("summary_status") == "page_teaser" and a.get("summary_status") == "page_teaser_untranslated":
                        a["summary_ar"], a["summary_status"] = src.get("summary_ar"), "page_teaser"
            store.save_file(tok, gid, RES, json.loads(json.dumps(cur, ensure_ascii=False, default=str)))
            return True
        except Exception as e:
            print(f"حفظ الترجمة فشل (محاولة {attempt + 1})", e, flush=True)
            time.sleep(3 * (attempt + 1))
    return False


def main():
    tok, gid = os.getenv("GIST_TOKEN"), os.getenv("GIST_ID")
    if not (tok and gid):
        sys.exit("GIST_TOKEN و GIST_ID مطلوبان")
    res = store.load_file(tok, gid, RES, {}) or {}
    before = sum(1 for v in res.values() if isinstance(v, dict) for a in (v.get("items") or []) if _need_title(a))
    print(f"▶ تكملة الترجمة: فيه {before} عنوان لسه مش عربي", flush=True)
    if not before:
        print("مفيش حاجة محتاجة ترجمة", flush=True)
        return
    core.tr_stats_reset()
    fixed = job_guard.run_limited("ترجمة", BUDGET_MIN * 60 + 60, sweep, res, time.time() + BUDGET_MIN * 60,
                                  lambda m: print(m, flush=True), log=lambda m: print(m, flush=True))
    print(core.tr_stats_line(), flush=True)
    if sum(fixed.values()):
        print("✅ اتحفظت" if _merge_save(tok, gid, res) else "❌ ماتحفظتش", flush=True)


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    os._exit(0)
