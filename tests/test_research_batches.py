import unittest
import research_batches as rb


class ResearchBatchTests(unittest.TestCase):
    def items(self, n=19):
        return [{"title": f"خبر {i}", "title_ar": f"عنوان عربي {i}",
                 "url": f"https://example.com/story/{i}", "domain": "example.com",
                 "seendate": "2026-11-23T10:00:00Z", "snippet": f"نص الخبر {i}"}
                for i in range(n)]

    def test_create_splits_and_preserves_manifest(self):
        batch = rb.create_batch("ملف إثيوبيا", self.items(), batch_size=6)
        self.assertEqual(batch["material_count"], 19)
        self.assertEqual(len(batch["chunks"]), 4)
        self.assertEqual([len(x["materials"]) for x in batch["chunks"]], [6, 6, 6, 1])
        self.assertEqual(len(batch["manifest"]), 19)
        self.assertTrue(batch["manifest"][0]["url"].startswith("https://"))

    def test_deduplicates_urls(self):
        items = self.items(2)
        items.append(dict(items[0], title="نسخة مكررة"))
        batch = rb.create_batch("اختبار", items, batch_size=4)
        self.assertEqual(batch["material_count"], 2)

    def test_rejects_invalid_batch_size_and_empty_items(self):
        with self.assertRaises(ValueError):
            rb.create_batch("اختبار", self.items(1), batch_size=0)
        with self.assertRaises(ValueError):
            rb.create_batch("اختبار", [], batch_size=4)

    def test_prompt_contains_provenance_and_no_claim_of_link_reading(self):
        batch = rb.create_batch("اختبار", self.items(1), batch_size=1)
        prompt = rb.chunk_prompt(batch, batch["chunks"][0])
        self.assertIn(batch["chunks"][0]["materials"][0]["source_id"], prompt)
        self.assertIn("https://example.com/story/0", prompt)
        self.assertIn("لا تدّعِ أنك فتحت الروابط", prompt)

    def test_incomplete_batch_cannot_be_merged(self):
        batch = rb.create_batch("اختبار", self.items(3), batch_size=1)
        rb.set_chunk_output(batch, batch["chunks"][0]["id"], "نتيجة")
        with self.assertRaises(ValueError):
            rb.merge_prompt(batch)

    def test_completed_batches_can_be_merged(self):
        batch = rb.create_batch("اختبار", self.items(2), batch_size=1)
        for chunk in batch["chunks"]:
            rb.set_chunk_output(batch, chunk["id"], f"تحليل {chunk['index']}")
        prompt = rb.merge_prompt(batch)
        self.assertIn("دمج البحث الكامل", prompt)
        self.assertIn("تحليل 1", prompt)
        self.assertIn("سجل المصادر الأصلي", prompt)

    def test_failed_chunk_retry_is_preserved(self):
        batch = rb.create_batch("اختبار", self.items(1), batch_size=1)
        chunk = batch["chunks"][0]
        rb.set_chunk_output(batch, chunk["id"], "", state="failed", error="فشل النموذج")
        rb.retry_chunk(batch, chunk["id"])
        self.assertEqual(chunk["state"], "pending")
        self.assertEqual(chunk["error"], "")

    def test_output_is_clipped(self):
        batch = rb.create_batch("اختبار", self.items(1), batch_size=1)
        rb.set_chunk_output(batch, batch["chunks"][0]["id"], "x" * (rb.MAX_OUTPUT_CHARS + 100))
        self.assertEqual(len(batch["chunks"][0]["output"]), rb.MAX_OUTPUT_CHARS)

    def test_summary_progress(self):
        batch = rb.create_batch("اختبار", self.items(3), batch_size=1)
        rb.set_chunk_output(batch, batch["chunks"][0]["id"], "done")
        summary = rb.summary(batch)
        self.assertEqual(summary["completed"], 1)
        self.assertEqual(summary["pending"], 2)
        self.assertEqual(summary["progress_percent"], 33)


    def test_empty_result_cannot_be_marked_completed(self):
        batch = rb.create_batch("اختبار", self.items(1), batch_size=1)
        with self.assertRaises(ValueError):
            rb.set_chunk_output(batch, batch["chunks"][0]["id"], "", state="completed")


if __name__ == "__main__":
    unittest.main()
