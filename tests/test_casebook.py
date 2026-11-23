import unittest
import casebook
import store


class CasebookTests(unittest.TestCase):
    def test_create_case_has_separate_research_ledgers(self):
        case = casebook.new_case('ملف تجريبي', 'وصف')
        self.assertEqual(case['materials'], [])
        self.assertEqual(case['claims'], [])
        self.assertEqual(case['events'], [])

    def test_material_deduplication_by_url(self):
        case = casebook.new_case('ملف')
        article = {'title': 'خبر', 'url': 'https://example.com/a', 'text': 'نص'}
        self.assertTrue(casebook.add_material(case, article, 'خبر'))
        self.assertFalse(casebook.add_material(case, article, 'مقال رأي'))
        self.assertEqual(len(case['materials']), 1)

    def test_claims_and_events_are_kept_separate(self):
        case = casebook.new_case('ملف')
        casebook.add_claim(case, 'ادعاء قابل للفحص', 'ادعاء منسوب', 'منسوب لمصدر واحد', 'https://example.com')
        casebook.add_event(case, '2026-11-22', 'حدث تجريبي', 'تفاصيل')
        self.assertEqual(len(case['claims']), 1)
        self.assertEqual(len(case['events']), 1)

    def test_prompt_contains_provenance_and_uncertainty_rules(self):
        case = casebook.new_case('قضية الاختبار', 'نطاق')
        casebook.add_material(case, {'title': 'مقال', 'url': 'https://example.com', 'text': 'مقتطف'}, 'مقال رأي')
        prompt = casebook.build_prompt(case)
        self.assertIn('الرابط الأصلي', prompt)
        self.assertIn('لا تعتبر تعدد المقالات تعدداً للمصادر', prompt)
        self.assertIn('سجل الوقائع والادعاءات', prompt)

    def test_store_migrates_old_data_and_preserves_research_cases(self):
        old = {'saved': [], 'sources': [], 'writers': [], 'keys': [], 'watch_topics': '', 'posts': []}
        normalized = store.normalize(old)
        self.assertEqual(normalized['research_cases'], [])
        sample = casebook.new_case('ملف محفوظ')
        normalized = store.normalize({'research_cases': [sample]})
        self.assertEqual(normalized['research_cases'][0]['title'], 'ملف محفوظ')


if __name__ == '__main__':
    unittest.main()
