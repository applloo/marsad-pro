import json
import os
from unittest import mock

import alerts_job
import store


def test_alerts_job_collects_new_and_skips_seen():
    mem = {"marsad_alerts_cfg.json": {"keywords": "ليبيا، Libya", "egypt_keywords": "", "cats": {"keyword": True, "egypt": False}},
           "marsad_auto_intel.json": {"warning": {"at": "2026-11-25T10:00:00+00:00", "alerts": [{"case_id": "c1", "case_title": "ليبيا", "severity": "عاجل", "new_materials": [1, 2]}]}},
           "marsad_reports.json": {}}
    news = [{"url": "https://a.test/1", "title": "Libya tanker", "title_ar": "ناقلة ليبيا", "domain": "a.test", "seendate": "20991125T100000Z"}]
    with mock.patch.object(store, "load_file", lambda t, g, n, d=None: mem.get(n, d)), \
         mock.patch.object(store, "save_file", lambda t, g, n, v: mem.__setitem__(n, json.loads(json.dumps(v)))), \
         mock.patch("core.gnews_site_search", lambda *a, **k: (list(news), [])), \
         mock.patch("core.translate_titles", lambda items: None), \
         mock.patch.dict(os.environ, {"GIST_TOKEN": "t", "GIST_ID": "g"}):
        alerts_job.main()
        first = mem["marsad_alerts.json"]["items"]
        alerts_job.main()
        second = mem["marsad_alerts.json"]["items"]
    cats = sorted(x["cat"] for x in first)
    assert cats == ["keyword", "warning"]
    assert len(second) == len(first)  # مفيش تكرار في التشغيلة التانية
