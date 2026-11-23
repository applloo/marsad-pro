import io
import unittest
import zipfile

import github_sync
import job_control
import store


class JobControlTests(unittest.TestCase):
    def test_task_lifecycle_and_active_lookup(self):
        task = job_control.new_task("daily.yml", "التقرير اليومي")
        self.assertEqual(task["state"], "queued")
        self.assertIs(job_control.find_active([task], "daily.yml"), task)
        job_control.transition(task, "submitted", "قبل GitHub الطلب")
        self.assertEqual(task["state"], "submitted")
        job_control.transition(task, "running", "بدأ التنفيذ")
        job_control.transition(task, "succeeded", "اكتمل")
        self.assertIsNone(job_control.find_active([task], "daily.yml"))

    def test_rejects_invalid_transition(self):
        task = job_control.new_task("search.yml", "البحث الشامل")
        with self.assertRaises(ValueError):
            job_control.transition(task, "succeeded")


class StoreTests(unittest.TestCase):
    def test_normalize_preserves_known_persistent_collections(self):
        data = store.normalize({
            "saved": [{"id": "a"}],
            "analysis_cases": [{"id": "case-1"}],
            "research_batches": [{"id": "batch-1"}],
            "unknown": ["ignored"],
        })
        self.assertEqual(data["saved"][0]["id"], "a")
        self.assertEqual(data["analysis_cases"][0]["id"], "case-1")
        self.assertEqual(data["research_batches"][0]["id"], "batch-1")
        self.assertNotIn("unknown", data)


class GithubSyncTests(unittest.TestCase):
    def _zip(self, name="app.py", content="print('ok')"):
        buff = io.BytesIO()
        with zipfile.ZipFile(buff, "w") as archive:
            archive.writestr(name, content)
        return buff.getvalue()

    def test_repository_validation(self):
        self.assertTrue(github_sync.validate_repo("applloo/marsad-pro"))
        self.assertFalse(github_sync.validate_repo("https://github.com/applloo/marsad-pro"))

    def test_release_zip_filters_secrets_and_accepts_code(self):
        buff = io.BytesIO()
        with zipfile.ZipFile(buff, "w") as archive:
            archive.writestr("app.py", "print('ok')")
            archive.writestr(".env", "TOKEN=secret")
            archive.writestr("secrets.toml", "password='secret'")
        files = github_sync.inspect_release_zip(buff.getvalue())
        self.assertIn("app.py", files)
        self.assertNotIn(".env", files)
        self.assertNotIn("secrets.toml", files)

    def test_release_zip_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            github_sync.inspect_release_zip(self._zip("../outside.py"))


if __name__ == "__main__":
    unittest.main()
