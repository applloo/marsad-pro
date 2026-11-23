import unittest
import ai_billing


class AIBillingTests(unittest.TestCase):
    def test_profile_round_trip_is_model_specific(self):
        settings = {}
        saved = ai_billing.save_profile(settings, "gemini", "model-a", 1.0, 2.0, 10.0, "https://example.com/pricing")
        self.assertEqual(ai_billing.get_profile(settings, "gemini", "model-a"), saved)
        self.assertEqual(ai_billing.get_profile(settings, "gemini", "model-b"), {})
        self.assertEqual(saved["currency"], "USD")
        self.assertTrue(saved["last_reviewed_at"])

    def test_invalid_profile_rejected(self):
        with self.assertRaises(ValueError):
            ai_billing.save_profile({}, "gemini", "model-a", 0, 1, 10)

    def test_model_month_spend(self):
        rows = [
            {"month": "2026-11", "provider": "gemini", "model": "a", "cost_usd": 1.25},
            {"month": "2026-11", "provider": "gemini", "model": "b", "cost_usd": 4.00},
        ]
        self.assertEqual(ai_billing.month_spend(rows, "2026-11", "gemini", "a"), 1.25)

    def test_preflight_cap(self):
        self.assertTrue(ai_billing.preflight(2, 3, 5)["allowed"])
        self.assertFalse(ai_billing.preflight(2, 3.01, 5)["allowed"])


if __name__ == '__main__':
    unittest.main()
