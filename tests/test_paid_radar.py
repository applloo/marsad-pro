import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import paid_radar


class PaidRadarTests(unittest.TestCase):
    def test_app_exposes_paid_radar_as_a_separate_search_tab(self):
        from pathlib import Path
        app = Path("app.py").read_text(encoding="utf-8")
        self.assertIn("tab_paid", app)
        self.assertIn("with tab_paid:", app)
        self.assertIn("رادار التقارير المدفوعة", app)
        self.assertNotIn("gist_backups", app)

    def test_catalog_includes_priority_subscription_sources(self):
        names = {row[0] for row in paid_radar.PAID_SOURCES}
        self.assertIn("Tactical Report", names)
        self.assertIn("Haaretz", names)
        self.assertIn("The New York Times", names)
        self.assertIn("Jane's", names)

    def test_alternatives_reject_paywall_and_non_allowlisted_domains(self):
        dt = datetime.now(timezone.utc)
        rows = [
            {"source_url": "https://apnews.com", "link": "https://apnews.com/a", "title": "Iran regional talks continue", "date": dt, "source_name": "AP"},
            {"source_url": "https://nytimes.com", "link": "https://nytimes.com/a", "title": "Iran regional talks continue", "date": dt, "source_name": "NYT"},
            {"source_url": "https://randomblog.example", "link": "https://randomblog.example/a", "title": "Iran regional talks continue", "date": dt, "source_name": "Blog"},
        ]
        with patch.object(paid_radar.core, "_get_feed", return_value=rows), \
             patch.object(paid_radar.core, "gdelt_call", return_value=([], "")), \
             patch.object(paid_radar.core, "decode_gnews", side_effect=lambda x: x), \
             patch.object(paid_radar.core, "tr", side_effect=lambda x, *a: x):
            got, note = paid_radar.find_open_coverage("Iran regional talks continue", "tacticalreport.com", 30)
        self.assertEqual([x["domain"] for x in got], ["apnews.com"])
        self.assertIn("روابط مرشحة", note)

    def test_existing_article_fallback_refuses_paywall_bypass(self):
        with patch.object(paid_radar.core.requests, "get") as get:
            result, reason = paid_radar.core.fetch_alternative("https://www.tacticalreport.com/reports/locked")
        self.assertIsNone(result)
        self.assertIn("لا نستخدم خدمات وسيطة", reason)
        get.assert_not_called()

    def test_gdelt_is_used_as_an_independent_open_coverage_path(self):
        row = {"url": "https://www.bbc.com/news/world-middle-east-123", "domain": "bbc.com",
               "title": "Iran regional talks continue", "seendate": "20261123T090000Z"}
        with patch.object(paid_radar.core, "_get_feed", return_value=[]), \
             patch.object(paid_radar.core, "gdelt_call", return_value=([row], "")), \
             patch.object(paid_radar.core, "tr", side_effect=lambda x, *a: "عنوان مترجم"):
            items, note = paid_radar.find_open_coverage("Iran regional talks continue", "tacticalreport.com", 30)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["discovery_method"], "GDELT")
        self.assertEqual(items[0]["domain"], "bbc.com")

    def test_reader_rejects_paywalled_domain(self):
        article, note = paid_radar.read_open_article("https://www.nytimes.com/story")
        self.assertIsNone(article)
        self.assertIn("النطاقات المفتوحة", note)

    def test_reader_only_uses_direct_open_source_fetch(self):
        class Response:
            ok = True
            url = "https://apnews.com/story"
            content = b"html"
            encoding = "utf-8"
            apparent_encoding = "utf-8"
        with patch.object(paid_radar.core, "is_safe_url", return_value=True), \
             patch.object(paid_radar.requests, "get", return_value=Response()) as get, \
             patch.object(paid_radar.core, "_extract", return_value={"title": "Test", "text": "x" * 900}), \
             patch.object(paid_radar.core, "translate_long", return_value="مترجم"):
            article, note = paid_radar.read_open_article("https://apnews.com/story")
        get.assert_called_once()
        self.assertEqual(article["text_ar"], "مترجم")
        self.assertIn("مباشرة", note)

    def test_tactical_public_index_reads_only_report_links(self):
        class Response:
            ok = True
            url = "https://www.tacticalreport.com/reports"
            text = '<a href="/reports/egypt-note">Egypt: A new regional defense arrangement</a><a href="/login">Sign in</a>'
            def raise_for_status(self):
                return None
        with patch.object(paid_radar.core, "is_safe_url", return_value=True), \
             patch.object(paid_radar.requests, "get", return_value=Response()), \
             patch.object(paid_radar.core, "tr", side_effect=lambda x, *a: "عنوان مترجم"):
            items, notes = paid_radar.tactical_public_headlines()
        self.assertEqual(len(items), 1)
        self.assertIn("Tactical Report", items[0]["paid_source"])
        self.assertTrue(items[0]["url"].endswith("/reports/egypt-note"))

    def test_legal_search_links_preserve_original_link(self):
        links = paid_radar.legal_search_links("A report title", "https://tacticalreport.com/reports/abc")
        self.assertEqual(links[-1][0], "المقال الأصلي")
        self.assertTrue(all(url.startswith("https://") for _, url in links))


if __name__ == "__main__":
    unittest.main()
