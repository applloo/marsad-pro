import unittest

import case_intelligence as ci


class CumulativeCaseIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.case = {
            "id": "case_1",
            "title": "التوترات الإقليمية",
            "description": "متابعة التطورات والأدلة",
            "tags": ["إيران", "الولايات المتحدة"],
            "materials": [{
                "id": "m1", "title": "تصريح رسمي", "type": "بيان رسمي",
                "outlet": "جهة رسمية", "url": "https://example.org/a",
                "text": "النص المتاح للتصريح"
            }],
            "claims": [{
                "id": "c1", "statement": "تم الإعلان عن إجراء", "type": "ادعاء منسوب",
                "status": "منسوب لمصدر واحد", "source": "https://example.org/a"
            }],
            "events": [{
                "id": "e1", "date": "2026-11-20", "title": "صدور التصريح",
                "detail": "تفاصيل الحدث", "source": "https://example.org/a"
            }],
        }

    def test_first_snapshot_tracks_existing_evidence(self):
        record, result = ci.update_case_file(None, self.case)
        self.assertTrue(result["changed"])
        self.assertEqual(len(record["snapshots"]), 1)
        self.assertEqual(len(record["ledger"]["materials"]), 1)
        self.assertEqual(len(record["ledger"]["claims"]), 1)
        self.assertEqual(len(record["ledger"]["events"]), 1)
        self.assertGreaterEqual(len(result["events"]), 3)

    def test_identical_snapshot_does_not_create_duplicate(self):
        record, _ = ci.update_case_file(None, self.case)
        updated, result = ci.update_case_file(record, self.case)
        self.assertFalse(result["changed"])
        self.assertEqual(len(updated["snapshots"]), 1)

    def test_new_material_and_claim_status_change_are_logged(self):
        record, _ = ci.update_case_file(None, self.case)
        changed = dict(self.case)
        changed["materials"] = list(self.case["materials"]) + [{
            "id": "m2", "title": "تقرير جديد", "url": "https://example.org/b", "text": "نص جديد"
        }]
        changed["claims"] = [dict(self.case["claims"][0], status="مدعوم بمصادر مستقلة")]
        updated, result = ci.update_case_file(record, changed)
        self.assertTrue(result["changed"])
        kinds = {x["type"] for x in result["events"]}
        self.assertIn("new_material", kinds)
        claim_change = next(x for x in result["events"] if x["type"] == "updated_claims")
        self.assertEqual(claim_change["before"]["status"], "منسوب لمصدر واحد")
        self.assertEqual(claim_change["after"]["status"], "مدعوم بمصادر مستقلة")
        self.assertEqual(len(updated["ledger"]["claims"]["c1"]["versions"]), 2)

    def test_removed_material_is_retained_in_history(self):
        record, _ = ci.update_case_file(None, self.case)
        changed = dict(self.case)
        changed["materials"] = []
        updated, result = ci.update_case_file(record, changed)
        self.assertIn("removed_materials", {x["type"] for x in result["events"]})
        self.assertIn("m1", updated["ledger"]["materials"])
        self.assertIn("removed_from_current_case", updated["ledger"]["materials"]["m1"])

    def test_restored_material_is_logged_without_erasing_previous_history(self):
        record, _ = ci.update_case_file(None, self.case)
        without_material = dict(self.case)
        without_material["materials"] = []
        record, _ = ci.update_case_file(record, without_material)
        restored, result = ci.update_case_file(record, self.case)
        self.assertIn("restored_materials", {x["type"] for x in result["events"]})
        self.assertNotIn("removed_from_current_case", restored["ledger"]["materials"]["m1"])
        self.assertEqual(len(restored["ledger"]["materials"]["m1"]["versions"]), 1)

    def test_prompt_contains_history_and_explicit_non_paid_manual_boundary(self):
        record, _ = ci.update_case_file(None, self.case)
        prompt = ci.build_cumulative_prompt(self.case, record)
        self.assertIn("سجل التغييرات", prompt)
        self.assertIn("لا تنفذ بحثاً أو استدعاء API أو عملية مدفوعة", prompt)
        self.assertIn("https://example.org/a", prompt)

    def test_snapshots_store_hashes_not_duplicate_full_material_text(self):
        long_case = dict(self.case)
        long_case["materials"] = [dict(self.case["materials"][0], text="x" * 5000)]
        record, _ = ci.update_case_file(None, long_case)
        snap_material = record["snapshots"][0]["content"]["materials"][0]
        ledger_payload = record["ledger"]["materials"]["m1"]["versions"][0]["payload"]
        self.assertNotIn("payload", snap_material)
        self.assertEqual(len(ledger_payload["text"]), 3000)
        self.assertTrue(ledger_payload["text_truncated"])
        self.assertEqual(ledger_payload["original_text_characters"], 5000)

    def test_summary_counts(self):
        record, _ = ci.update_case_file(None, self.case)
        summary = ci.summarize(record)
        self.assertEqual(summary["snapshots"], 1)
        self.assertEqual(summary["materials_tracked"], 1)
        self.assertEqual(summary["claims_tracked"], 1)
        self.assertEqual(summary["events_tracked"], 1)


if __name__ == "__main__":
    unittest.main()
