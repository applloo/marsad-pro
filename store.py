# -*- coding: utf-8 -*-
"""تخزين دائم اختياري: المحفوظات + المصادر والكتّاب المضافون، داخل Gist خاص في GitHub.
بدون إعداد (GITHUB_TOKEN و GIST_ID في Secrets) يعمل التطبيق بالذاكرة المؤقتة فقط."""
import json
import copy

import requests

FILE = "marsad_store.json"
API = "https://api.github.com/gists/"


def empty():
    return {"saved": [], "sources": [], "writers": [], "keys": [], "watch_topics": "", "posts": [],
            "custom_dossiers": [], "custom_threads": [], "analysis_cases": [], "research_cases": [], "case_links": [], "early_warning": {"baselines": {}, "reports": [], "last_scan": ""}, "scenario_worksheets": [], "analysis_packages": [], "ai_usage": [], "billing_reservations": [], "ai_results": [], "content_jobs": [], "content_results": [], "prompt_library": [], "prompt_chains": [], "prompt_bundles": [], "source_health_runs": [], "intel_dossiers": [], "intel_case_files": [], "job_tasks": [], "research_batches": [], "video_projects": [], "ai_settings": {}, "outlet_profiles": {}, "writer_profiles": {}}


def normalize(data):
    out = empty()
    if isinstance(data, dict):
        for k in out:
            if isinstance(out[k], list) and isinstance(data.get(k), list):
                out[k] = data[k]
            elif isinstance(out[k], str) and isinstance(data.get(k), str):
                out[k] = data[k]
        for k in ("custom_dossiers", "custom_threads", "analysis_cases", "research_cases", "case_links", "intel_case_files", "scenario_worksheets", "analysis_packages", "ai_usage", "billing_reservations", "ai_results", "content_jobs", "content_results", "prompt_library", "prompt_chains", "prompt_bundles", "job_tasks", "research_batches", "video_projects"):
            if isinstance(data.get(k), list):
                out[k] = data[k]
        if isinstance(data.get("early_warning"), dict):
            out["early_warning"] = data["early_warning"]
        for k in ("outlet_profiles", "writer_profiles", "ai_settings"):
            if isinstance(data.get(k), dict):
                out[k] = data[k]
    return out


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "marsad-news"}


def load(token, gist_id):
    r = requests.get(API + gist_id, headers=_headers(token), timeout=20)
    r.raise_for_status()
    f = (r.json().get("files") or {}).get(FILE)
    if not f:
        return empty()
    content = f.get("content") or ""
    if f.get("truncated") and f.get("raw_url"):
        content = requests.get(f["raw_url"], headers=_headers(token), timeout=20).text
    try:
        return normalize(json.loads(content or "{}"))
    except ValueError:
        return empty()


def save(token, gist_id, data):
    body = {"files": {FILE: {"content": json.dumps(data, ensure_ascii=False)}}}
    r = requests.patch(API + gist_id, headers=_headers(token), json=body, timeout=25)
    r.raise_for_status()



def three_way_merge(base, local, remote, path="store"):
    """Merge local edits over the latest remote snapshot; report overlapping edits.

    Lists of records with stable `id` are merged record-by-record. Other lists are
    treated as atomic values to avoid silently guessing how to combine ordering.
    This detects many stale-session collisions but is NOT an atomic Gist CAS lock.
    """
    conflicts = []

    def merge_value(b, l, r, current_path):
        if l == b:
            return copy.deepcopy(r)
        if r == b:
            return copy.deepcopy(l)
        if l == r:
            return copy.deepcopy(l)
        if isinstance(b, dict) and isinstance(l, dict) and isinstance(r, dict):
            out = {}
            for key in set(b) | set(l) | set(r):
                bv, lv, rv = b.get(key), l.get(key), r.get(key)
                has_b, has_l, has_r = key in b, key in l, key in r
                if not has_l and not has_r:
                    continue
                if not has_l:
                    if has_b and rv == bv:
                        continue
                    if has_b and rv != bv:
                        conflicts.append(f"{current_path}.{key}")
                        out[key] = copy.deepcopy(rv)
                    continue
                if not has_r:
                    if has_b and lv == bv:
                        continue
                    if has_b and lv != bv:
                        conflicts.append(f"{current_path}.{key}")
                        out[key] = copy.deepcopy(lv)
                    else:
                        out[key] = copy.deepcopy(lv)
                    continue
                out[key] = merge_value(bv if has_b else None, lv, rv, f"{current_path}.{key}")
            return out
        if all(isinstance(x, list) for x in (b, l, r)):
            if all(not x or (isinstance(x[0], dict) and x[0].get("id")) for x in (b, l, r)):
                b_order = [x["id"] for x in b]
                l_order = [x["id"] for x in l]
                r_order = [x["id"] for x in r]
                local_reordered = [x for x in l_order if x in b_order] != [x for x in b_order if x in l_order]
                remote_reordered = [x for x in r_order if x in b_order] != [x for x in b_order if x in r_order]
                if local_reordered and remote_reordered and [x for x in l_order if x in b_order] != [x for x in r_order if x in b_order]:
                    conflicts.append(f"{current_path} (order)")
                bm = {x["id"]: x for x in b}
                lm = {x["id"]: x for x in l}
                rm = {x["id"]: x for x in r}
                result = []
                ordered_ids = [x["id"] for x in r] + [x["id"] for x in l if x["id"] not in rm]
                for rid in ordered_ids:
                    bv, lv, rv = bm.get(rid), lm.get(rid), rm.get(rid)
                    if lv is None and rv is None:
                        continue
                    if bv is None:
                        result.append(copy.deepcopy(lv if lv is not None else rv))
                        continue
                    if lv is None:
                        if rv == bv:
                            continue
                        conflicts.append(f"{current_path}[{rid}]")
                        result.append(copy.deepcopy(rv))
                        continue
                    if rv is None:
                        if lv == bv:
                            continue
                        conflicts.append(f"{current_path}[{rid}]")
                        result.append(copy.deepcopy(lv))
                        continue
                    result.append(merge_value(bv, lv, rv, f"{current_path}[{rid}]"))
                return result
            conflicts.append(current_path)
            return copy.deepcopy(r)
        conflicts.append(current_path)
        return copy.deepcopy(r)

    merged = merge_value(base, local, remote, path)
    return merged, sorted(set(conflicts))


def merge(base, extra):
    """يدمج بيانات مستوردة في البيانات الحالية دون تكرار"""
    base, extra = normalize(base), normalize(extra)
    seen = {x.get("url") for x in base["saved"]}
    base["saved"] += [x for x in extra["saved"] if x.get("url") not in seen]
    seen = {(x.get("domain"), x.get("group")) for x in base["sources"]}
    base["sources"] += [x for x in extra["sources"] if (x.get("domain"), x.get("group")) not in seen]
    seen = {x.get("id") for x in base["writers"]}
    base["writers"] += [x for x in extra["writers"] if x.get("id") not in seen]
    for key in ("custom_dossiers", "custom_threads", "analysis_cases", "research_cases", "case_links", "intel_case_files", "scenario_worksheets", "analysis_packages", "ai_usage", "billing_reservations", "ai_results", "content_jobs", "content_results", "prompt_chains", "prompt_bundles", "job_tasks", "research_batches", "video_projects"):
        seen = {x.get("id") for x in base[key]}
        base[key] += [x for x in extra[key] if x.get("id") not in seen]
    # مكتبة البرومبتات: ادمج الإصدارات داخل البرومبت نفسه بدلاً من إسقاط النسخ الأحدث عند الدمج.
    prompts_by_id = {x.get("id"): x for x in base["prompt_library"] if x.get("id")}
    for incoming in extra["prompt_library"]:
        pid = incoming.get("id")
        if not pid or pid not in prompts_by_id:
            base["prompt_library"].append(incoming)
            if pid:
                prompts_by_id[pid] = incoming
            continue
        target = prompts_by_id[pid]
        versions = {int(v.get("version", 0)): v for v in target.get("versions", [])}
        for version in incoming.get("versions", []):
            versions.setdefault(int(version.get("version", 0)), version)
        target["versions"] = [versions[k] for k in sorted(versions)]
        if int(incoming.get("current_version", 0)) > int(target.get("current_version", 0)):
            target["current_version"] = incoming.get("current_version")
            for field in ("name", "category", "description", "tags", "status", "updated_at", "archived_at"):
                if field in incoming:
                    target[field] = incoming[field]
    for key in ("outlet_profiles", "writer_profiles", "ai_settings"):
        base[key].update({k: v for k, v in extra[key].items() if k not in base[key]})
    # الشفرات لا تُدمج من النسخ الاحتياطية (تبقى كما هي في الـGist)
    return base


REPORTS_FILE = "marsad_reports.json"


def load_reports(token, gist_id):
    """التقارير اليومية التي يكتبها daily.py ({'latest': 'YYYY-MM-DD', 'archive': {...}}) — للقراءة فقط"""
    r = requests.get(API + gist_id, headers=_headers(token), timeout=20)
    r.raise_for_status()
    f = (r.json().get("files") or {}).get(REPORTS_FILE)
    if not f:
        return {}
    content = f.get("content") or ""
    if f.get("truncated") and f.get("raw_url"):
        content = requests.get(f["raw_url"], headers=_headers(token), timeout=20).text
    try:
        return json.loads(content or "{}")
    except ValueError:
        return {}


def load_file(token, gist_id, name, default=None):
    """يقرأ ملف JSON آخر من نفس الـGist (مثل نتيجة التقرير المخصص)"""
    r = requests.get(API + gist_id, headers=_headers(token), timeout=25)
    r.raise_for_status()
    f = (r.json().get("files") or {}).get(name)
    if not f:
        return default
    content = f.get("content") or ""
    if f.get("truncated") and f.get("raw_url"):
        content = requests.get(f["raw_url"], headers=_headers(token), timeout=40).text
    try:
        return json.loads(content or "null") or default
    except ValueError:
        return default


def save_file(token, gist_id, name, data):
    body = {"files": {name: {"content": json.dumps(data, ensure_ascii=False)}}}
    r = requests.patch(API + gist_id, headers=_headers(token), json=body, timeout=60)
    r.raise_for_status()
