import io
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import source_intelligence as si


class SourceIntelligenceTests(unittest.TestCase):
    def test_catalog_has_major_sides_and_paid_watch(self):
        sides = {x['side'] for x in si.SOURCE_CATALOG}
        self.assertTrue({'us', 'il', 'uk', 'ar'}.issubset(sides))
        self.assertTrue(any(x.get('paid_watch') for x in si.SOURCE_CATALOG))
        self.assertGreaterEqual(len(si.SOURCE_CATALOG), 250)

    def test_feed_latest_parses_rss_title_and_date(self):
        xml = b'''<?xml version="1.0"?><rss><channel><item><title>Red Sea update</title><pubDate>Mon, 23 Nov 2026 10:00:00 GMT</pubDate></item></channel></rss>'''
        latest, title = si._feed_latest(xml)
        self.assertEqual(title, 'Red Sea update')
        self.assertTrue(latest.startswith('2026-11-23T10:00:00'))

    def test_cluster_groups_related_headlines_and_compares_sides(self):
        rows = [
            {'title': 'US Navy deploys carrier to Red Sea after regional tensions', 'title_ar': 'تحرك حاملة أمريكية إلى البحر الأحمر', 'url': 'https://apnews.com/a', 'domain': 'apnews.com', 'source_name': 'AP', 'published_at': '2026-11-23T10:00:00+00:00'},
            {'title': 'US carrier deployment to Red Sea follows regional tensions', 'title_ar': 'انتشار حاملة أمريكية في البحر الأحمر', 'url': 'https://www.bbc.com/b', 'domain': 'bbc.com', 'source_name': 'BBC', 'published_at': '2026-11-23T11:00:00+00:00'},
            {'title': 'Israeli analysis: Red Sea security and regional naval deployments', 'title_ar': 'تحليل إسرائيلي لأمن البحر الأحمر', 'url': 'https://www.inss.org.il/c', 'domain': 'inss.org.il', 'source_name': 'INSS', 'published_at': '2026-11-23T12:00:00+00:00'},
        ]
        groups = si.cluster_articles(rows, threshold=0.10)
        self.assertEqual(len(groups), 1)
        self.assertGreaterEqual(groups[0]['article_count'], 2)
        self.assertTrue(groups[0]['narratives'])
        self.assertTrue(any(x.get('origin_assessment') for x in groups[0]['articles']))
        self.assertIn('لا يثبت', groups[0]['caveat'])

    def test_cluster_does_not_merge_far_apart_dates(self):
        rows = [
            {'title': 'Iran nuclear talks resume in Vienna', 'url': 'https://apnews.com/a', 'domain': 'apnews.com', 'published_at': '2026-11-01T00:00:00+00:00'},
            {'title': 'Iran nuclear talks resume in Vienna', 'url': 'https://bbc.com/b', 'domain': 'bbc.com', 'published_at': '2026-11-23T00:00:00+00:00'},
        ]
        self.assertEqual(si.cluster_articles(rows, max_gap_days=3), [])

    def test_source_scan_is_bounded_and_uses_selected_sources(self):
        fake = {'domain': 'example.com', 'name': 'Example', 'side': 'us', 'language': 'en', 'groups': []}
        with patch.object(si, 'SOURCE_CATALOG', [fake]), patch.object(si, 'check_source_health', return_value={**fake, 'status': 'healthy_no_feed'}):
            result = si.scan_sources(['Example'])
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['counts']['healthy_no_feed'], 1)

    def test_safe_get_rejects_private_redirect_before_following(self):
        class Redirect:
            status_code = 302
            headers = {'Location': 'http://127.0.0.1/admin'}
            def close(self):
                pass
        with patch.object(si, '_safe_https', side_effect=lambda u: u == 'https://example.com/'), \
             patch.object(si.requests, 'get', return_value=Redirect()) as get:
            with self.assertRaises(ValueError):
                si._safe_get('https://example.com/')
        self.assertEqual(get.call_count, 1)
        self.assertFalse(get.call_args.kwargs['allow_redirects'])

    def test_health_comparison_detects_feed_url_change_and_loss(self):
        previous = {"checked_at": "2026-11-22T00:00:00+00:00", "rows": [
            {"domain": "example.com", "status": "healthy_feed", "feed_url": "https://example.com/rss", "latest_item": "Old", "checked_at": "2026-11-22T00:00:00+00:00"},
            {"domain": "lost.example", "status": "healthy_feed", "feed_url": "https://lost.example/rss", "latest_item": "Old", "checked_at": "2026-11-22T00:00:00+00:00"},
        ]}
        current = {"checked_at": "2026-11-23T00:00:00+00:00", "rows": [
            {"domain": "example.com", "status": "healthy_feed", "feed_url": "https://example.com/feed.xml", "latest_item": "New"},
            {"domain": "lost.example", "status": "healthy_no_feed", "feed_url": "", "latest_item": ""},
        ]}
        result = si.compare_health_runs(current, previous)
        self.assertEqual(result['rows'][0]['change_status'], 'feed_changed')
        self.assertEqual(result['rows'][1]['change_status'], 'feed_lost')

    def test_case_dossier_contains_methodology_and_limits(self):
        with patch.object(si.core, 'tr', side_effect=lambda x, *a: 'أمن البحر الأحمر'):
            dossier = si.build_case_dossier('Red Sea security', [], [])
        self.assertIn('methodology', dossier)
        self.assertIn('limitations', dossier)
        self.assertEqual(dossier['article_count'], 0)


if __name__ == '__main__':
    unittest.main()
