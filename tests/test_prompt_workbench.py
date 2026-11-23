import unittest
import prompt_workbench
import store


class PromptWorkbenchTests(unittest.TestCase):
    def test_create_prompt_starts_version_one(self):
        records = []
        rec = prompt_workbench.create_prompt(records, "تحليل الملف", "حلل الأدلة", "التحليل الجيوسياسي", "وصف")
        self.assertEqual(rec["current_version"], 1)
        self.assertEqual(prompt_workbench.current_version(rec)["body"], "حلل الأدلة")

    def test_save_version_preserves_previous_versions(self):
        records = []
        rec = prompt_workbench.create_prompt(records, "تحليل الملف", "النص الأول")
        prompt_workbench.save_version(records, rec["id"], "النص الثاني", "تطوير")
        self.assertEqual([x["version"] for x in rec["versions"]], [1, 2])
        self.assertEqual(prompt_workbench.current_version(rec)["body"], "النص الثاني")

    def test_duplicate_active_name_rejected(self):
        records = []
        prompt_workbench.create_prompt(records, "تحليل الملف", "النص")
        with self.assertRaises(ValueError):
            prompt_workbench.create_prompt(records, "تحليل الملف", "نسخة أخرى")

    def test_unchanged_body_does_not_create_duplicate_version(self):
        records = []
        rec = prompt_workbench.create_prompt(records, "تحليل الملف", "النص")
        with self.assertRaises(ValueError):
            prompt_workbench.save_version(records, rec["id"], "النص")
        self.assertEqual(len(rec["versions"]), 1)

    def test_archive_restore_and_rollback(self):
        records = []
        rec = prompt_workbench.create_prompt(records, "تحليل الملف", "v1")
        prompt_workbench.save_version(records, rec["id"], "v2")
        prompt_workbench.rollback_as_new_version(records, rec["id"], 1)
        self.assertEqual(rec["current_version"], 3)
        self.assertEqual(prompt_workbench.current_version(rec)["body"], "v1")
        prompt_workbench.archive_prompt(records, rec["id"])
        self.assertEqual(prompt_workbench.active_prompts(records), [])
        prompt_workbench.restore_prompt(records, rec["id"])
        self.assertEqual(len(prompt_workbench.active_prompts(records)), 1)

    def test_store_migrates_and_merges_prompt_library(self):
        sample = {"id": "pr_1", "name": "prompt"}
        self.assertEqual(store.normalize({})["prompt_library"], [])
        self.assertEqual(store.normalize({"prompt_library": [sample]})["prompt_library"], [sample])
        merged = store.merge({}, {"prompt_library": [sample]})
        self.assertEqual(merged["prompt_library"], [sample])

    def test_store_merge_keeps_new_prompt_versions_for_same_prompt_id(self):
        base = {"prompt_library": [{"id": "pr_x", "name": "p", "current_version": 1,
                                    "versions": [{"version": 1, "body": "v1"}]}]}
        extra = {"prompt_library": [{"id": "pr_x", "name": "p", "current_version": 2,
                                     "versions": [{"version": 1, "body": "v1"}, {"version": 2, "body": "v2"}]}]}
        merged = store.merge(base, extra)
        record = merged["prompt_library"][0]
        self.assertEqual(record["current_version"], 2)
        self.assertEqual([v["version"] for v in record["versions"]], [1, 2])


if __name__ == "__main__":
    unittest.main()
