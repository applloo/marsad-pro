import unittest
from unittest.mock import patch
import gh_actions


class Response:
    def raise_for_status(self):
        pass
    def json(self):
        return {"workflow_runs": [{
            "status": "completed", "conclusion": "success", "html_url": "https://github.com/example/run/1",
            "created_at": "2026-11-23T10:00:00Z", "updated_at": "2026-11-23T10:01:00Z", "run_number": 1,
        }]}


class WorkflowOverviewTests(unittest.TestCase):
    @patch("gh_actions.requests.get", return_value=Response())
    def test_recent_runs_collects_all_known_workflows(self, get):
        rows = gh_actions.recent_runs("token", "owner/repo", 1)
        self.assertEqual(len(rows), len(gh_actions.WORKFLOWS))
        self.assertEqual(rows[0]["conclusion"], "success")
        self.assertEqual(get.call_count, len(gh_actions.WORKFLOWS))


if __name__ == "__main__":
    unittest.main()
