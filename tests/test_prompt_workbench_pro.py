import unittest
import prompt_workbench as pw
import store


class PromptWorkbenchProTests(unittest.TestCase):
    def test_variable_render_replaces_known_and_reports_missing_and_unknown(self):
        result = pw.render_template('قضية {{case_title}} من {{date_from}} إلى {{date_to}} {{mystery}}',
                                    {'case_title': 'البحر الأحمر', 'date_from': '2026-01-01'})
        self.assertIn('البحر الأحمر', result['text'])
        self.assertIn('{{date_to}}', result['text'])
        self.assertEqual(result['missing'], ['date_to'])
        self.assertEqual(result['unknown'], ['mystery'])
        with self.assertRaises(ValueError):
            pw.render_template('{{case_title}} {{date_to}}', {'case_title': 'قضية'}, strict=True)

    def test_bundle_deduplicates_by_url_and_keeps_all_provenance(self):
        cases = [
            {'id': 'a', 'title': 'ملف أ', 'materials': [{'title': 'خبر', 'url': 'https://example.com/x', 'text': 'نص'}], 'claims': [], 'events': []},
            {'id': 'b', 'title': 'ملف ب', 'materials': [{'title': 'نسخة أخرى', 'url': 'https://example.com/x', 'text': 'نص مختلف'}, {'title': 'خبر آخر', 'url': 'https://example.com/y'}], 'claims': [], 'events': []},
        ]
        bundle = pw.create_bundle(cases, ['a', 'b'])
        self.assertEqual(bundle['source_case_count'], 2)
        self.assertEqual(bundle['material_count'], 2)
        self.assertEqual(bundle['deduplicated_count'], 1)
        self.assertEqual(len(bundle['materials'][0]['provenance']), 2)
        self.assertIn('ملف ب', pw.render_bundle(bundle))

    def test_bundle_without_valid_cases_rejected(self):
        with self.assertRaises(ValueError):
            pw.create_bundle([], ['missing'])

    def test_chain_is_resumable_and_passes_completed_prior_outputs(self):
        bundle = pw.create_bundle([{'id': 'c', 'title': 'قضية', 'materials': [], 'claims': [], 'events': []}], ['c'])
        chain = pw.new_chain('سلسلة', bundle, {'case_title': 'قضية'})
        first = pw.chain_stage_prompt(chain, 0, pw.render_bundle(bundle))
        self.assertIn('جمع واستخراج المعلومات', first['prompt'])
        pw.save_stage_output(chain, 0, 'استخراج: واقعة أ')
        second = pw.chain_stage_prompt(chain, 1, pw.render_bundle(bundle))
        self.assertIn('استخراج: واقعة أ', second['prompt'])
        self.assertEqual(second['prior_count'], 1)
        self.assertEqual(len(chain['stages']), 6)

    def test_stage_output_required_and_approval_requires_all_stages(self):
        bundle = pw.create_bundle([{'id': 'c', 'title': 'قضية', 'materials': [], 'claims': [], 'events': []}], ['c'])
        chain = pw.new_chain('سلسلة', bundle)
        with self.assertRaises(ValueError):
            pw.save_stage_output(chain, 0, '  ')
        for i in range(len(chain['stages'])):
            pw.save_stage_output(chain, i, f'نتيجة {i}')
        approval = pw.approve_chain(chain, 'النسخة النهائية')
        self.assertEqual(approval['status'], 'approved')
        self.assertEqual(len(approval['sha256']), 64)

    def test_compare_requires_two_results_and_keeps_both(self):
        with self.assertRaises(ValueError):
            pw.compare_outputs([{'label': 'أ', 'text': 'نتيجة'}])
        text = pw.compare_outputs([{'label': 'أ', 'text': 'نتيجة أ'}, {'label': 'ب', 'text': 'نتيجة ب'}])
        self.assertIn('نتيجة أ', text)
        self.assertIn('نتيجة ب', text)

    def test_store_normalizes_and_three_way_merges_new_collections(self):
        self.assertEqual(store.normalize({})['prompt_chains'], [])
        chain = {'id': 'pc_1', 'title': 'سلسلة'}
        bundle = {'id': 'pb_1', 'title': 'حزمة'}
        normalized = store.normalize({'prompt_chains': [chain], 'prompt_bundles': [bundle]})
        self.assertEqual(normalized['prompt_chains'], [chain])
        self.assertEqual(normalized['prompt_bundles'], [bundle])
        merged, conflicts = store.three_way_merge(store.empty(), normalized, store.empty())
        self.assertFalse(conflicts)
        self.assertEqual(merged['prompt_chains'], [chain])
        self.assertEqual(merged['prompt_bundles'], [bundle])


if __name__ == '__main__':
    unittest.main()
