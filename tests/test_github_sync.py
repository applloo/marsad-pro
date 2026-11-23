import io
import unittest
import zipfile
from unittest.mock import patch

import github_sync


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


class FakeResponse:
    def __init__(self, data=None, status=200):
        self._data = data or {}
        self.status_code = status
    def json(self):
        return self._data
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('http error')


class GitHubSyncTests(unittest.TestCase):
    def test_app_contains_github_release_sync_and_auto_mode(self):
        from pathlib import Path
        app = Path('app.py').read_text(encoding='utf-8')
        self.assertIn('GH_SYNC_TOKEN', app)
        self.assertIn('GH_SYNC_AUTO', app)
        self.assertIn('push_release_zip', app)
        self.assertIn('tab_health', app)
        self.assertIn('tab_clusters', app)

    def test_ci_workflow_runs_tests_on_push_and_pr(self):
        from pathlib import Path
        ci = Path('.github/workflows/ci.yml').read_text(encoding='utf-8')
        self.assertIn('pull_request:', ci)
        self.assertIn('python -m unittest discover', ci)
        self.assertIn('cancel-in-progress: false', ci)

    def test_validate_repo(self):
        self.assertTrue(github_sync.validate_repo('owner/repo-name'))
        self.assertFalse(github_sync.validate_repo('https://github.com/owner/repo'))

    def test_zip_inspection_filters_secrets_and_backup(self):
        data = make_zip({'app.py': 'print(1)', '.github/workflows/ci.yml': 'name: CI', '.env': 'SECRET=x', 'secrets.toml': 'x=1', 'backup.zip': 'x', '.gitignore': '.env'})
        got = github_sync.inspect_release_zip(data)
        self.assertIn('app.py', got)
        self.assertIn('.github/workflows/ci.yml', got)
        self.assertIn('.gitignore', got)
        self.assertNotIn('.env', got)
        self.assertNotIn('secrets.toml', got)
        self.assertNotIn('backup.zip', got)

    def test_zip_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            github_sync.inspect_release_zip(make_zip({'../evil.py': 'x'}))

    def test_zip_rejects_duplicate_paths(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('app.py', '1')
            z.writestr('app.py', '2')
        with self.assertRaises(ValueError):
            github_sync.inspect_release_zip(buf.getvalue())

    def test_push_release_zip_uses_non_force_update(self):
        data = make_zip({'app.py': 'print("hello")'})
        calls = []
        def get(url, **kwargs):
            calls.append(('get', url, kwargs))
            if '/git/ref/' in url:
                return FakeResponse({'object': {'sha': 'old'}})
            return FakeResponse({'tree': {'sha': 'tree-old'}})
        def post(url, **kwargs):
            calls.append(('post', url, kwargs))
            if url.endswith('/git/blobs'):
                return FakeResponse({'sha': 'blob-new'})
            if url.endswith('/git/trees'):
                return FakeResponse({'sha': 'tree-new'})
            return FakeResponse({'sha': 'commit-new', 'html_url': 'https://github.com/o/r/commit/commit-new'})
        def patch_request(url, **kwargs):
            calls.append(('patch', url, kwargs))
            return FakeResponse({'ref': 'refs/heads/main'})
        with patch.object(github_sync.requests, 'get', side_effect=get), patch.object(github_sync.requests, 'post', side_effect=post), patch.object(github_sync.requests, 'patch', side_effect=patch_request):
            result = github_sync.push_release_zip('token', 'o/r', 'main', data)
        self.assertEqual(result['commit_sha'], 'commit-new')
        update = [x for x in calls if x[0] == 'patch'][0]
        self.assertFalse(update[2]['json']['force'])


if __name__ == '__main__':
    unittest.main()
