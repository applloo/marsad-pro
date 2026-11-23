import unittest
import video_storyteller as vs
import store


class VideoStorytellerTests(unittest.TestCase):
    def project(self):
        return vs.create_project("case-1", "ملف إيران", "[SRC-1] تقرير تجريبي عن تطورات الملف", now="2026-11-23T10:00:00+00:00")

    def test_defaults_match_approved_design(self):
        p = self.project()
        self.assertEqual(p["settings"], {"video_type": "analysis", "duration_minutes": 10, "tone": "sharp", "scene_plan_enabled": True, "short_clips_enabled": True})

    def test_settings_validation(self):
        with self.assertRaises(ValueError):
            vs.validate_settings({"duration_minutes": 7})
        with self.assertRaises(ValueError):
            vs.validate_settings({"tone": "angry"})

    def test_reading_prompt_preserves_dossier_and_case(self):
        p = self.project(); prompt = vs.reading_prompt(p)
        self.assertIn("ملف إيران", prompt); self.assertIn("[SRC-1]", prompt)
        self.assertIn("أطروحتين متنافستين", prompt)

    def test_script_prompt_uses_egyptian_delivery_and_optional_sections(self):
        p = self.project(); prompt = vs.script_prompt(p, "ورقة قراءة")
        self.assertIn("اللهجة قاهرية مصرية", prompt)
        self.assertIn("خطة مشاهد كاملة", prompt)
        self.assertIn("Shorts/Reels", prompt)
        p["settings"]["scene_plan_enabled"] = False
        p["settings"]["short_clips_enabled"] = False
        prompt = vs.script_prompt(p)
        self.assertNotIn("خطة مشاهد كاملة", prompt)
        self.assertNotIn("3 مقاطع قصيرة", prompt)

    def test_artifact_versions_are_independent(self):
        p = self.project()
        a = vs.save_artifact(p, "script", "نسخة أولى")
        b = vs.save_artifact(p, "script", "نسخة ثانية")
        c = vs.save_artifact(p, "production_plan", "مشاهد")
        self.assertEqual((a["version"], b["version"], c["version"]), (1, 2, 1))
        self.assertEqual(vs.latest_artifact(p, "script")["content"], "نسخة ثانية")

    def test_revision_prompt_does_not_restart_research(self):
        p = self.project()
        prompt = vs.revision_prompt(p, "سكريبت سابق", "قوّي المقدمة")
        self.assertIn("من غير إعادة البحث", prompt)
        self.assertIn("قوّي المقدمة", prompt)
        with self.assertRaises(ValueError):
            vs.revision_prompt(p, "", "تعديل")

    def test_store_normalizes_and_merges_video_projects(self):
        project = {"id": "vp-1", "case_id": "case-1", "artifacts": []}
        self.assertEqual(store.normalize({"video_projects": [project]})["video_projects"], [project])
        merged, conflicts = store.three_way_merge({"video_projects": []}, {"video_projects": [project]}, {"video_projects": []})
        self.assertEqual(merged["video_projects"], [project]); self.assertEqual(conflicts, [])

    def test_no_provider_or_api_dependency_in_module(self):
        import inspect
        source = inspect.getsource(vs)
        self.assertNotIn("requests.", source)
        self.assertNotIn("ai_router", source)


if __name__ == "__main__":
    unittest.main()
