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

    def test_gist_token_has_no_github_token_fallback(self):
        # GITHUB_TOKEN مايقدرش يكتب في الـGist، فالرجوع ليه كان بيخلّي المهمة تفشل بخطأ مش مفهوم
        files = list(Path('.github/workflows').glob('*.yml'))
        for path in files:
            text = path.read_text(encoding='utf-8')
            if 'GIST_TOKEN:' in text:
                self.assertIn('GIST_TOKEN: ${{ secrets.GIST_TOKEN }}', text, path.name)
                self.assertNotIn('secrets.GITHUB_TOKEN', text, path.name)

    def test_smart_sections_run_after_full_search_without_repeating_it(self):
        text = Path('.github/workflows/monitor.yml').read_text(encoding='utf-8')
        self.assertIn('workflow_run:', text)
        self.assertIn('البحث الشامل في كل المصادر', text)
        self.assertIn('python intel_job.py', text)
        self.assertNotIn('search_job.py', text)

    def test_daily_report_schedule_is_preserved(self):
        text = Path('.github/workflows/daily.yml').read_text(encoding='utf-8')
        self.assertIn('cron: "7 6 * * *"', text)
        self.assertIn('workflow_dispatch:', text)

    def test_full_search_is_scheduled_and_remains_manual(self):
        text = Path('.github/workflows/search.yml').read_text(encoding='utf-8')
        self.assertIn('cron: "7 9 * * *"', text)
        self.assertIn('workflow_dispatch:', text)

    def test_run_all_workflow_runs_every_job_in_order(self):
        text = Path('.github/workflows/all.yml').read_text(encoding='utf-8')
        order = [text.index(x) for x in ('daily.py', 'search_job.py', 'watch_job.py', 'scheduled_monitor.py', 'intel_job.py')]
        self.assertEqual(order, sorted(order))
        self.assertEqual(text.count('continue-on-error: true'), 4)
        self.assertIn('workflow_dispatch:', text)

    def test_backup_workflow_is_not_part_of_active_operations(self):
        self.assertFalse(Path('.github/workflows/backup.yml').exists())


if __name__ == '__main__':
    unittest.main()
