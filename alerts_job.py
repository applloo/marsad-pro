# -*- coding: utf-8 -*-
"""إشعارات تطبيق مرصد برو (الموبايل والكمبيوتر). بيشتغل على GitHub كل ساعة ونص تقريباً، من غير ذكاء اصطناعي ومن غير فلوس.
بيقرا إعدادات الإشعارات من الـGist (marsad_alerts_cfg.json) وبيكتب الإشعارات الجديدة في (marsad_alerts.json).
التطبيق بيقرا الملف ده كل ربع ساعة ويطلع الإشعار.
أنواع الإشعارات (cat):
  keyword  خبر فيه كلمة من كلماتك
  warning  تنبيه جديد من الإنذار المبكر في ملفات القضايا
  egypt    خبر جديد في الشأن المصري فيه كلمة من كلمات مصر بتاعتك
  daily    التقرير اليومي جاهز
  job      البحث الشامل خلص أو فشل
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import core
import store
from sources import ARABIC, EGYPT, ISRAEL, REGION, UK, USA

CFG, OUT = "marsad_alerts_cfg.json", "marsad_alerts.json"
KEEP = 150
DEFAULT_CFG = {"keywords": "", "egypt_keywords": "", "cats": {"keyword": True, "warning": True, "egypt": True, "daily": True, "job": True},
               "max_per_run": 8}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _id(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]


def _words(text):
    return [w.strip() for w in re.split(r"[,،;\n]+", text or "") if w.strip()]


def _parse(iso):
    try:
        t = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _seen_dt(v):
    """seendate بييجي بشكل 20261125T103000Z"""
    try:
        return datetime.strptime(str(v)[:16], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    except Exception:
        return _parse(v)


def keyword_alerts(words, groups, cat, max_items, seen):
    """بيدوّر في أخبار Google (المصادر بتاعتنا بس) على كلماتك في آخر يوم"""
    if not words:
        return []
    sel = [e for g in groups for ents in g.values() for e in ents]
    items, _notes = core.gnews_site_search(sel, 1, terms=words, joiner="OR", country="US", max_items=60)
    fresh = [a for a in items if a.get("url") and _id(a["url"]) not in seen]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
    recent = []
    for a in fresh:
        t = _seen_dt(a.get("seendate"))
        if t is None or t >= cutoff:
            recent.append(a)
    recent = recent[:max_items]
    if recent:
        core.translate_titles(recent)
    out = []
    for a in recent:
        title = a.get("title_ar") if core._HAS_AR.search(a.get("title_ar") or "") else a.get("title", "")
        out.append({"id": _id(a["url"]), "cat": cat, "title": title[:200],
                    "body": f"{a.get('domain', '')} · " + ("، ".join(w for w in words if w.lower() in (a.get("title", "") + " " + a.get("title_ar", "")).lower())[:80] or "من كلماتك"),
                    "url": a["url"], "at": now_iso()})
    return out


def main():
    tok, gid = os.getenv("GIST_TOKEN"), os.getenv("GIST_ID")
    if not (tok and gid):
        sys.exit("GIST_TOKEN و GIST_ID مطلوبان")
    cfg = {**DEFAULT_CFG, **(store.load_file(tok, gid, CFG, {}) or {})}
    cats = {**DEFAULT_CFG["cats"], **(cfg.get("cats") or {})}
    out = store.load_file(tok, gid, OUT, {}) or {}
    items = out.get("items") or []
    seen = set(out.get("seen") or []) | {x.get("id") for x in items}
    new = []
    mx = int(cfg.get("max_per_run") or 8)

    if cats.get("keyword"):
        try:
            new += keyword_alerts(_words(cfg.get("keywords")), (ISRAEL, USA, UK, REGION, ARABIC), "keyword", mx, seen)
        except Exception as e:
            print("keyword alerts failed", e, flush=True)
    if cats.get("egypt"):
        try:
            new += keyword_alerts(_words(cfg.get("egypt_keywords")), (EGYPT,), "egypt", mx, seen | {x["id"] for x in new})
        except Exception as e:
            print("egypt alerts failed", e, flush=True)
    if cats.get("warning"):
        try:
            ai = store.load_file(tok, gid, "marsad_auto_intel.json", {}) or {}
            for al in ((ai.get("warning") or {}).get("alerts") or [])[:mx]:
                i = _id("warn", al.get("case_id") or al.get("case_title"), (ai.get("warning") or {}).get("at"))
                if i not in seen:
                    new.append({"id": i, "cat": "warning", "title": f"🚨 {al.get('severity', 'متابعة')}: {al.get('case_title', 'ملف قضية')}",
                                "body": f"{len(al.get('new_materials', []))} مادة جديدة" + (" · كلمات عاجلة: " + "، ".join(al.get("urgent_terms", [])[:4]) if al.get("urgent_terms") else ""),
                                "url": "", "section": "library", "at": now_iso()})
        except Exception as e:
            print("warning alerts failed", e, flush=True)
    if cats.get("daily"):
        try:
            reps = store.load_file(tok, gid, "marsad_reports.json", {}) or {}
            today = datetime.now(core.TZ).strftime("%Y-%m-%d")
            if today in reps and _id("daily", today) not in seen:
                new.append({"id": _id("daily", today), "cat": "daily", "title": "📰 التقرير اليومي جاهز",
                            "body": f"تقرير {today} اتعمل. افتحه من الرئيسية أو غرفة العمليات.", "url": "", "section": "ops", "at": now_iso()})
        except Exception as e:
            print("daily alert failed", e, flush=True)
    if cats.get("job"):
        try:
            job = store.load_file(tok, gid, "marsad_search_job.json", {}) or {}
            fin = job.get("finished") or job.get("updated")
            i = _id("job", fin, job.get("state"))
            t = _parse(fin)
            if fin and i not in seen and t and datetime.now(timezone.utc) - t < timedelta(hours=4):
                errs = job.get("errors") or {}
                if job.get("state") == "done" and not errs:
                    title, body = "✅ البحث الشامل خلص", f"{sum((job.get('counts') or {}).values())} خبر جديد في الأقسام."
                else:
                    title, body = "⚠️ البحث الشامل فيه مشكلة", "، ".join(list(errs)[:4]) or str(job.get("state"))
                new.append({"id": i, "cat": "job", "title": title, "body": body, "url": "", "section": "ops", "at": now_iso()})
        except Exception as e:
            print("job alert failed", e, flush=True)

    items = new + items
    out = {"updated": now_iso(), "items": items[:KEEP], "seen": list((seen | {x["id"] for x in new}))[-2000:]}
    store.save_file(tok, gid, OUT, out)
    print(f"إشعارات جديدة: {len(new)}", flush=True)


if __name__ == "__main__":
    main()
