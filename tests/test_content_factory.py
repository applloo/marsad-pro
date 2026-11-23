import unittest
import content_factory
import store


class ContentFactoryTests(unittest.TestCase):
    def test_prompt_has_platform_deliverables_and_editorial_safeguards(self):
        prompt = content_factory.build_content_prompt("قضية اختبار", "التحليل يقول إن الادعاء غير محسوم")
        self.assertIn("سكريبت رئيسي", prompt)
        self.assertIn("ريلز/شورتس", prompt)
        self.assertIn("لا تضف معلومات خارجية", prompt)
        self.assertIn("[تحتاج تحقق]", prompt)
        self.assertIn("الادعاء غير محسوم", prompt)

    def test_visual_production_blueprint_is_available(self):
        prompt = content_factory.build_content_prompt("قضية بصرية", "تحليل محفوظ", output_type="خطة بصرية فقط", platform="YouTube")
        self.assertIn("Storyboard كامل", prompt)
        self.assertIn("برومبت مستقل لكل صورة أو مشهد", prompt)
        self.assertIn("تصور توضيحي", prompt)
        self.assertIn("B-roll", prompt)
        self.assertIn("16:9", prompt)
        self.assertIn("9:16", prompt)

    def test_full_package_contains_thumbnail_and_shot_list(self):
        prompt = content_factory.build_content_prompt("قضية", "تحليل")
        self.assertIn("3 أفكار للصورة المصغرة", prompt)
        self.assertIn("خريطة مشاهد ولقطات بالتوقيت", prompt)
        self.assertIn("لا تطلب من مولد الصور كتابة عناوين", prompt)

    def test_edit_map_output_has_linked_units_assets_and_edl(self):
        prompt = content_factory.build_content_prompt(
            "قضية مونتاج", "سكريبت تجريبي: هنا نص الإلقاء", output_type="خريطة مونتاج تنفيذية"
        )
        self.assertIn("خريطة مونتاج تنفيذية", prompt)
        self.assertIn("U001", prompt)
        self.assertIn("Asset Manifest", prompt)
        self.assertIn("EDL", prompt)
        self.assertIn("track, start, end, asset_id", prompt)
        self.assertIn("[يحتاج سكريبت]", prompt)
        self.assertIn("لا تدّعِ إنشاء ملف مشروع CapCut", prompt)

    def test_empty_analysis_is_rejected(self):
        with self.assertRaises(ValueError):
            content_factory.build_content_prompt("قضية", "  ")

    def test_job_keeps_source_and_hash(self):
        job = content_factory.create_job("c1", "قضية", "r1", "تحليل محفوظ", output_type="ريلز وشورتس")
        self.assertEqual(job["case_id"], "c1")
        self.assertEqual(job["result_id"], "r1")
        self.assertEqual(len(job["sha256"]), 64)
        self.assertIn("3 سكريبتات قصيرة", job["prompt"])

    def test_store_preserves_content_jobs_and_old_data(self):
        sample = {"id": "j1", "case_id": "c1"}
        self.assertEqual(store.normalize({})["content_jobs"], [])
        self.assertEqual(store.normalize({"content_jobs": [sample]})["content_jobs"], [sample])
        self.assertEqual(store.normalize({"content_results": [sample]})["content_results"], [sample])
        old = {"analysis_packages": [{"id": "p1"}], "ai_results": [{"id": "r1"}]}
        normalized = store.normalize(old)
        self.assertEqual(normalized["analysis_packages"], old["analysis_packages"])
        self.assertEqual(normalized["ai_results"], old["ai_results"])


if __name__ == "__main__":
    unittest.main()
