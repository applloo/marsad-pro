import unittest
import analysis_packages
import store

class AnalysisPackageTests(unittest.TestCase):
    def test_package_contains_material_provenance_and_prompt(self):
        case = {"id":"c1", "title":"قضية اختبار", "description":"وصف", "materials":[
            {"title":"خبر", "url":"https://example.com/a", "domain":"example.com", "text":"نص الخبر", "date":"2026-11-22"}],
            "claims":[], "events":[]}
        p = analysis_packages.build_package(case, "حلل بحذر", "تحليل", "Gemini API", ["خيط أ"])
        md = analysis_packages.render_markdown(p)
        self.assertIn("https://example.com/a", md)
        self.assertIn("حلل بحذر", md)
        self.assertIn("خيط أ", md)
        self.assertEqual(p["material_count"], 1)

    def test_package_persists_editorial_output_settings(self):
        case = {"id":"c2", "title":"قضية سكريبت", "materials":[], "claims":[], "events":[]}
        p = analysis_packages.build_package(case, "اكتب التحليل والسكريبت", "تحليل + سكريبت", "Groq",
            output_mode="تحليل + سكريبت مصري", audience="الجمهور العام", script_duration="3 إلى 5 دقائق")
        md = analysis_packages.render_markdown(p)
        self.assertEqual(p["output_mode"], "تحليل + سكريبت مصري")
        self.assertIn("الجمهور العام", md)
        self.assertIn("3 إلى 5 دقائق", md)

    def test_store_has_backward_compatible_package_collection(self):
        self.assertEqual(store.normalize({})["analysis_packages"], [])
        sample = {"id": "p1", "case_id": "c1"}
        self.assertEqual(store.normalize({"analysis_packages": [sample]})["analysis_packages"], [sample])

    def test_package_is_snapshot_and_versions_increment(self):
        case = {"id":"c1", "title":"قضية", "materials":[], "claims":[], "events":[]}
        first = analysis_packages.build_package(case, "p1", "prompt", "model")
        case["materials"].append({"title":"خبر جديد"})
        second = analysis_packages.build_package(case, "p2", "prompt", "model", package_history=[first])
        self.assertEqual(first["version"], 1)
        self.assertEqual(second["version"], 2)
        self.assertEqual(first["material_count"], 0)
        self.assertEqual(second["material_count"], 1)
        self.assertNotEqual(first["sha256"], second["sha256"])

if __name__ == "__main__":
    unittest.main()
