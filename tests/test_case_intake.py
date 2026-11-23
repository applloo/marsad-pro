import unittest
import casebook
import case_intake


class CaseIntakeTests(unittest.TestCase):
    def test_suggest_cases_ranks_matching_case_without_auto_mutation(self):
        cases = [casebook.new_case('مفاوضات إيران النووية', tags=['إيران', 'الولايات المتحدة']),
                 casebook.new_case('الاقتصاد العالمي')]
        suggestions = case_intake.suggest_cases('إيران والمفاوضات النووية', ['إيران'], cases)
        self.assertEqual(suggestions[0]['case_id'], cases[0]['id'])
        self.assertEqual(len(cases[0]['materials']), 0)

    def test_import_deduplicates_canonical_urls_and_preserves_provenance(self):
        case = casebook.new_case('ملف')
        rows = [
            {'title_ar': 'خبر أول', 'url': 'https://www.example.com/story/?utm_source=x',
             'domain': 'example.com', 'seendate': '2026-11-23', 'snippet': 'مقتطف الخبر', 'writer': 'كاتب'},
            {'title': 'نسخة مكررة', 'url': 'https://example.com/story'},
            {'title': 'خبر ثان', 'url': 'https://other.example/story', 'description': 'نص ثان'},
        ]
        result = case_intake.import_search_results(case, rows)
        self.assertEqual(len(result['added']), 2)
        self.assertEqual(result['skipped'], 1)
        self.assertEqual(case['materials'][0]['author'], 'كاتب')
        self.assertEqual(case['materials'][0]['text'], 'مقتطف الخبر')
        again = case_intake.import_search_results(case, rows)
        self.assertEqual(len(again['added']), 0)
        self.assertEqual(again['skipped'], 3)

    def test_batch_is_created_only_for_new_materials_and_linked_to_case(self):
        case = casebook.new_case('ملف تجريبي')
        result = case_intake.import_search_results(case, [
            {'title': 'خبر', 'url': 'https://example.com/a', 'snippet': 'نص مقتطف'}
        ])
        batch = case_intake.batch_from_materials(case, result['added'])
        self.assertEqual(batch['case_id'], case['id'])
        self.assertEqual(batch['origin'], 'search_results_import')
        self.assertEqual(batch['material_count'], 1)
        self.assertIn('source_id', batch['manifest'][0])

    def test_empty_materials_do_not_create_batch(self):
        self.assertIsNone(case_intake.batch_from_materials(casebook.new_case('ملف'), []))


if __name__ == '__main__':
    unittest.main()
