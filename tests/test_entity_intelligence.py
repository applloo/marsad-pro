import unittest
import entity_intelligence as ei
import casebook


class EntityIntelligenceTests(unittest.TestCase):
    def test_extracts_named_entities_by_category(self):
        found = ei.extract_entities("تحركت حاملة الطائرات USS Abraham Lincoln قرب إيران، وأعلنت CENTCOM ذلك")
        names = {(x['name'], x['type']) for x in found}
        self.assertIn(("USS Abraham Lincoln", "ships"), names)
        self.assertIn(("إيران", "countries"), names)
        self.assertIn(("القيادة المركزية الأمريكية", "organizations"), names)

    def test_publication_timeline_does_not_claim_event_time(self):
        rows = ei.build_publication_timeline([{"title":"خبر", "published_at":"2026-11-20T10:00:00Z", "url":"https://x.test/a"}])
        self.assertEqual(len(rows), 1)
        self.assertIn("ليس بالضرورة وقت وقوع الحدث", rows[0]["time_basis"])

    def test_contradictions_are_candidates_with_sources_and_caveat(self):
        articles = [
            {"title":"القوات تؤكد تنفيذ الضربة في الموقع المحدد", "text":"القوات أكدت تنفيذ الضربة في الموقع المحدد صباح اليوم", "url":"https://a.test/1", "source_name":"A"},
            {"title":"القوات تنفي تنفيذ الضربة في الموقع المحدد", "text":"القوات تنفي تنفيذ الضربة في الموقع المحدد صباح اليوم", "url":"https://b.test/1", "source_name":"B"},
        ]
        found = ei.detect_contradiction_candidates(articles, min_overlap=0.2)
        self.assertTrue(found)
        self.assertEqual(found[0]["status"], "candidate_review_required")
        self.assertTrue(found[0]["source_a"]["url"])
        self.assertIn("لا يمثل حكماً", found[0]["caveat"])

    def test_headlines_alone_are_not_used_as_contradiction_claims(self):
        articles = [
            {"title":"القوات تؤكد تنفيذ الضربة في الموقع المحدد", "url":"https://a.test/1"},
            {"title":"القوات تنفي تنفيذ الضربة في الموقع المحدد", "url":"https://b.test/1"},
        ]
        self.assertEqual(ei.detect_contradiction_candidates(articles, min_overlap=0.2), [])

    def test_links_articles_to_existing_case(self):
        case = casebook.new_case("ملف إيران والبحر الأحمر", "", ["إيران", "البحر الأحمر"])
        casebook.add_material(case, {"title":"تحركات إيران في البحر الأحمر", "url":"https://case.test/a", "text":"إيران والبحر الأحمر"})
        rows = ei.link_new_articles_to_cases([{"title":"إيران والبحر الأحمر", "url":"https://news.test/a", "text":"تحركات إيران في البحر الأحمر"}], [case], min_score=12)
        self.assertTrue(rows)
        self.assertEqual(rows[0]["matches"][0]["case_id"], case["id"])

    def test_entity_index_preserves_provenance(self):
        rows = ei.build_entity_index([{"title":"قاعدة العديد في قطر", "url":"https://news.test/a", "domain":"news.test", "source_name":"News"}])
        item = next(x for x in rows if x["name"] == "قاعدة العديد الجوية")
        self.assertEqual(item["mentions"][0]["url"], "https://news.test/a")
        self.assertEqual(item["source_domains"], ["news.test"])


if __name__ == "__main__": unittest.main()
