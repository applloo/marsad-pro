from pathlib import Path
import unittest


class WorkflowWiringTests(unittest.TestCase):
    def test_each_workflow_has_non_overlapping_run_guard(self):
        files = list(Path('.github/workflows').glob('*.yml'))
        self.assertGreaterEqual(len(files), 4)
        for path in files:
            text = path.read_text(encoding='utf-8')
            self.assertIn('concurrency:', text, path.name)
            self.assertIn('cancel-in-progress: false', text, path.name)

    def test_workflows_keep_distinct_groups_to_avoid_pending_run_replacement(self):
        files = list(Path('.github/workflows').glob('*.yml'))
        groups = []
        for path in files:
            text = path.read_text(encoding='utf-8')
            line = next(line for line in text.splitlines() if line.strip().startswith('group:'))
            groups.append(line.split('group:', 1)[1].strip())
        self.assertEqual(len(groups), len(set(groups)))

    def test_gist_token_legacy_and_current_names_are_supported(self):
        files = list(Path('.github/workflows').glob('*.yml'))
        for path in files:
            text = path.read_text(encoding='utf-8')
            if 'GIST_TOKEN:' in text:
                self.assertIn('secrets.GIST_TOKEN || secrets.GITHUB_TOKEN', text, path.name)

    def test_daily_report_schedule_is_preserved(self):
        text = Path('.github/workflows/daily.yml').read_text(encoding='utf-8')
        self.assertIn('cron: "0 4 * * *"', text)
        self.assertIn('workflow_dispatch:', text)

    def test_full_search_is_scheduled_and_remains_manual(self):
        text = Path('.github/workflows/search.yml').read_text(encoding='utf-8')
        self.assertIn('cron: "0 7 * * *"', text)
        self.assertIn('workflow_dispatch:', text)

    def test_backup_workflow_is_not_part_of_active_operations(self):
        self.assertFalse(Path('.github/workflows/backup.yml').exists())


if __name__ == '__main__':
    unittest.main()
