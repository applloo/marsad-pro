import unittest
from datetime import datetime, timezone
import ai_billing


class BillingReservationTests(unittest.TestCase):
    def setUp(self):
        self.settings = {"billing_reservations": []}
        self.month = "2026-11"

    def test_reservation_reduces_available_budget(self):
        ai_billing.reserve(self.settings, "gemini", "model-a", self.month, 2.5, "r1")
        check = ai_billing.budget_preflight([], self.settings, self.month, "gemini", "model-a", 2.0, 4.0)
        self.assertFalse(check["allowed"])
        self.assertEqual(check["reserved_usd"], 2.5)

    def test_settled_reservation_no_longer_counts_as_pending(self):
        ai_billing.reserve(self.settings, "gemini", "model-a", self.month, 2.5, "r1")
        ai_billing.finish_reservation(self.settings, "r1", 2.2, "settled")
        self.assertEqual(ai_billing.reserved_spend(self.settings, "gemini", "model-a", self.month), 0)

    def test_failed_reservation_released_from_pending(self):
        ai_billing.reserve(self.settings, "gemini", "model-a", self.month, 2.5, "r1")
        ai_billing.finish_reservation(self.settings, "r1", status="failed")
        self.assertEqual(ai_billing.reserved_spend(self.settings, "gemini", "model-a", self.month), 0)

    def test_expired_reservation_does_not_count(self):
        now = datetime(2026, 11, 23, tzinfo=timezone.utc)
        ai_billing.reserve(self.settings, "gemini", "model-a", self.month, 2.5, "r1", ttl_seconds=1, now=now)
        later = datetime(2026, 11, 23, 0, 0, 2, tzinfo=timezone.utc)
        self.assertEqual(ai_billing.reserved_spend(self.settings, "gemini", "model-a", self.month, now=later), 0)

    def test_reservation_idempotent(self):
        first = ai_billing.reserve(self.settings, "gemini", "model-a", self.month, 2.5, "r1")
        second = ai_billing.reserve(self.settings, "gemini", "model-a", self.month, 9.0, "r1")
        self.assertEqual(first, second)
        self.assertEqual(len(self.settings["billing_reservations"]), 1)

    def test_provider_model_isolation(self):
        ai_billing.reserve(self.settings, "gemini", "model-a", self.month, 2.5, "r1")
        self.assertEqual(ai_billing.reserved_spend(self.settings, "gemini", "model-b", self.month), 0)


if __name__ == "__main__":
    unittest.main()
