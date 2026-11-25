import json
import os
import unittest
from unittest import mock

import intel_job
import store


class IntelJobTests(unittest.TestCase):
    def test_runs_all_steps_and_keeps_going_after_a_failure(self):
        mem = {"marsad_results.json": {"us": {"items": [
            {"url": f"https://www.nytimes.com/a{i}", "title": f"Iran talks Red Sea shipping {i % 2}", "domain": "nytimes.com",
             "seendate": "20261124T100000Z"} for i in range(6)]}}}
        with mock.patch.object(store, "load_file", lambda t, g, n, d=None: mem.get(n, d)), \
             mock.patch.object(store, "save_file", lambda t, g, n, v: mem.__setitem__(n, json.loads(json.dumps(v, default=str)))), \
             mock.patch.object(store, "load", lambda t, g: {"research_cases": []}), \
             mock.patch("paid_radar.search_paid_headlines", side_effect=RuntimeError("offline")), \
             mock.patch("source_intelligence.scan_sources", lambda names, timeout=8: {"checked_at": "2026-11-25T00:00:00+00:00", "rows": [], "counts": {}, "total": 0}), \
             mock.patch("core.translate_titles", lambda items: None), mock.patch("core.tr", lambda s, a, b: s), \
             mock.patch.dict(os.environ, {"GIST_TOKEN": "t", "GIST_ID": "g"}):
            intel_job.main()
        out = mem["marsad_auto_intel.json"]
        self.assertEqual(out["state"], "done")
        self.assertFalse(out["steps"]["رادار التقارير المدفوعة"]["ok"])
        self.assertTrue(out["steps"]["تجميع الأحداث والكيانات"]["ok"])
        self.assertIn("entity_index", out["dossier"])
        self.assertTrue(out["steps"]["الإنذار المبكر"]["ok"])


if __name__ == "__main__":
    unittest.main()
