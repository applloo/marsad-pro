import unittest
from datetime import datetime, timezone, timedelta
import job_control


class JobControlTests(unittest.TestCase):
    def test_new_task_starts_queued_with_audit_event(self):
        task = job_control.new_task("search.yml", "البحث الشامل")
        self.assertEqual(task["state"], "queued")
        self.assertEqual(task["events"][0]["state"], "queued")

    def test_transition_records_history_and_terminal_time(self):
        task = job_control.new_task("daily.yml", "التقرير اليومي")
        job_control.transition(task, "submitted", "قبل GitHub الطلب")
        self.assertEqual(task["state"], "submitted")
        job_control.transition(task, "succeeded", "اكتمل")
        self.assertIn("finished_at", task)
        self.assertEqual([x["state"] for x in task["events"]], ["queued", "submitted", "succeeded"])

    def test_invalid_transition_rejected(self):
        task = job_control.new_task("daily.yml", "التقرير")
        with self.assertRaises(ValueError):
            job_control.transition(task, "succeeded")

    def test_heartbeat_prevents_stale_detection(self):
        base = datetime(2026, 11, 23, 10, tzinfo=timezone.utc)
        task = job_control.new_task("watch.yml", "المراقبة", now=base)
        job_control.transition(task, "submitted", "accepted", now=base)
        job_control.heartbeat(task, "still active", now=base + timedelta(minutes=50))
        changed = job_control.mark_stale([task], stale_after_minutes=60, now=base + timedelta(minutes=100))
        self.assertEqual(changed, [])

    def test_stale_is_review_flag_not_failure(self):
        base = datetime(2026, 11, 23, 10, tzinfo=timezone.utc)
        task = job_control.new_task("watch.yml", "المراقبة", now=base)
        job_control.transition(task, "submitted", "accepted", now=base)
        changed = job_control.mark_stale([task], stale_after_minutes=60, now=base + timedelta(minutes=90))
        self.assertEqual(len(changed), 1)
        self.assertEqual(task["state"], "stale")

    def test_active_lookup_and_idempotent_append(self):
        task = job_control.new_task("search.yml", "البحث", idempotency_key="topic-x")
        self.assertIs(job_control.find_active([task], "search.yml", "topic-x"), task)
        rows = job_control.append_event([], task)
        rows = job_control.append_event(rows, task)
        self.assertEqual(len(rows), 1)

    def test_retry_creates_child_attempt(self):
        task = job_control.new_task("daily.yml", "التقرير")
        job_control.transition(task, "failed", "error")
        retry = job_control.retry_task(task)
        self.assertEqual(retry["attempt"], 2)
        self.assertEqual(retry["parent_task_id"], task["id"])

    def test_summary_counts_states(self):
        a = job_control.new_task("a", "A")
        b = job_control.new_task("b", "B")
        job_control.transition(b, "failed", "no")
        result = job_control.summary([a, b])
        self.assertEqual(result["active"], 1)
        self.assertEqual(result["failed"], 1)


if __name__ == "__main__":
    unittest.main()
