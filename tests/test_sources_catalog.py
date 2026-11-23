import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import sources
import intel
import paid_radar
import core


class SourceCatalogTests(unittest.TestCase):
    def test_all_search_catalog_languages_are_supported(self):
        supported = {"he", "en", "ar", "tr", "fa", "am", "fr", "es", "pt", "hi", "zh", "ko", "both"}
        for groups in (sources.ISRAEL, sources.USA, sources.UK, sources.REGION, sources.ARABIC, sources.EGYPT):
            for entries in groups.values():
                for _label, domain, language in entries:
                    self.assertFalse(set(language.split(",")) - supported, (domain, language))
                    self.assertNotIn("/", domain, domain)

    def test_catalog_expansion_is_visible_in_main_search_groups(self):
        domains = {d for groups in (sources.ISRAEL, sources.USA, sources.UK, sources.REGION)
                   for entries in groups.values() for _name, domain, _lang in entries for d in domain.split("|")}
        self.assertGreaterEqual(len(domains), 180)
        self.assertIn("sis.gov.uk", domains)
        self.assertIn("mod.gov.il", domains)
        self.assertIn("news.un.org", domains)
        self.assertIn("xinhuanet.com", domains)

    def test_intelligence_registry_includes_official_and_regional_sources(self):
        names = {row[0] for row in intel.SOURCES}
        self.assertIn("Tactical Report", names)
        self.assertIn("UK SIS / MI6", names)
        self.assertIn("US Intelligence Community", names)
        self.assertIn("IAEA", names)

    def test_french_sources_use_the_french_google_news_locale(self):
        feed_item = {"title": "La situation à Djibouti", "link": "https://lavoixdedjibouti.info/story",
                     "date": datetime.now(timezone.utc), "source_url": "https://lavoixdedjibouti.info",
                     "source_name": "La Voix de Djibouti"}
        with patch.object(core, "_get_feed", return_value=[feed_item]):
            items, notes = core.gnews_site_search([("La Voix de Djibouti", "lavoixdedjibouti.info", "fr")], 7, max_items=5)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["language"], "French")
        self.assertEqual(items[0]["sourcecountry"], "France")

    def test_paid_and_open_source_registries_are_separate(self):
        paid_domains = {d for row in paid_radar.PAID_SOURCES for d in row[1].split("|")}
        self.assertIn("tacticalreport.com", paid_domains)
        self.assertIn("nytimes.com", paid_domains)
        self.assertIn("haaretz.com", paid_domains)
        self.assertIn("apnews.com", paid_radar.OPEN_ALTERNATIVE_DOMAINS)
        self.assertNotIn("nytimes.com", paid_radar.OPEN_ALTERNATIVE_DOMAINS)


if __name__ == "__main__":
    unittest.main()
