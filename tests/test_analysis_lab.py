import unittest
import analysis_lab
import store

class AnalysisLabTests(unittest.TestCase):
    def test_store_schema_is_backward_compatible(self):
        old = {"saved": [{"url": "https://example.com"}], "sources": [], "writers": [], "keys": [], "watch_topics": "", "posts": []}
        normalized = store.normalize(old)
        self.assertEqual(len(normalized["saved"]), 1)
        self.assertIn("analysis_cases", normalized)
        self.assertEqual(normalized["custom_threads"], [])

    def test_all_prompt_templates_render(self):
        articles = [{"title": "Example opinion", "title_ar": "مقال تجريبي", "writer": "Test Writer",
                     "outlet": "The New York Times", "domain": "nytimes.com", "url": "https://www.nytimes.com/example",
                     "date": "2026-11-22", "text": "نص تجريبي لاختبار القالب."}]
        for kind in analysis_lab.PROMPT_TEMPLATES:
            prompt = analysis_lab.make_prompt(kind, articles, case_name="ملف تجريبي",
                custom_writers={"test": {"name": "Test Writer", "profile": "باحث في السياسة الدولية"}})
            self.assertIn("مقال تجريبي", prompt)
            self.assertGreater(len(prompt), 200)

    def test_unknown_outlet_is_not_labeled_politically(self):
        profile = analysis_lab.outlet_profile("unknown-example.net")
        self.assertIn("غير مصنف", profile["orientation"])

    def test_manual_records_have_unique_ids_and_timestamps(self):
        record = analysis_lab.new_record("خيط تجريبي", "وصف", ["مصر"], "خيط", ["u1", "u2"])
        self.assertEqual(record["articles"], ["u1", "u2"])
        self.assertTrue(record["created_at"])

if __name__ == "__main__":
    unittest.main()
