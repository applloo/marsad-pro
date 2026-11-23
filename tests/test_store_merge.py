import unittest
import store


class ThreeWayMergeTests(unittest.TestCase):
    def test_remote_only_change_is_preserved(self):
        base = {"items": [{"id": "a", "value": 1}]}
        local = {"items": [{"id": "a", "value": 1}]}
        remote = {"items": [{"id": "a", "value": 2}]}
        merged, conflicts = store.three_way_merge(base, local, remote)
        self.assertEqual(merged["items"][0]["value"], 2)
        self.assertEqual(conflicts, [])

    def test_local_and_remote_distinct_records_merge(self):
        base = {"items": [{"id": "a", "value": 1}]}
        local = {"items": [{"id": "a", "value": 1}, {"id": "b", "value": 2}]}
        remote = {"items": [{"id": "a", "value": 1}, {"id": "c", "value": 3}]}
        merged, conflicts = store.three_way_merge(base, local, remote)
        self.assertEqual({x["id"] for x in merged["items"]}, {"a", "b", "c"})
        self.assertEqual(conflicts, [])

    def test_same_record_conflict_is_reported(self):
        base = {"items": [{"id": "a", "value": 1}]}
        local = {"items": [{"id": "a", "value": 2}]}
        remote = {"items": [{"id": "a", "value": 3}]}
        merged, conflicts = store.three_way_merge(base, local, remote)
        self.assertTrue(conflicts)
        self.assertEqual(merged["items"][0]["value"], 3)

    def test_conflicting_reorders_are_reported(self):
        base = {"items": [{"id": "a"}, {"id": "b"}, {"id": "c"}]}
        local = {"items": [{"id": "b"}, {"id": "a"}, {"id": "c"}]}
        remote = {"items": [{"id": "a"}, {"id": "c"}, {"id": "b"}]}
        _, conflicts = store.three_way_merge(base, local, remote)
        self.assertTrue(any("order" in item for item in conflicts))

    def test_independent_dict_fields_merge(self):
        base = {"settings": {"x": 1, "y": 1}}
        local = {"settings": {"x": 2, "y": 1}}
        remote = {"settings": {"x": 1, "y": 3}}
        merged, conflicts = store.three_way_merge(base, local, remote)
        self.assertEqual(merged["settings"], {"x": 2, "y": 3})
        self.assertEqual(conflicts, [])


    def test_job_task_records_survive_store_normalization(self):
        task = {"id": "task-1", "workflow": "daily.yml", "state": "submitted"}
        normalized = store.normalize({"job_tasks": [task]})
        self.assertEqual(normalized["job_tasks"], [task])

    def test_job_task_records_merge_by_stable_id(self):
        base = {"job_tasks": [{"id": "task-1", "state": "queued"}]}
        local = {"job_tasks": [{"id": "task-1", "state": "submitted"}]}
        remote = {"job_tasks": [{"id": "task-1", "state": "queued"}, {"id": "task-2", "state": "failed"}]}
        merged, conflicts = store.three_way_merge(base, local, remote)
        self.assertEqual({x["id"] for x in merged["job_tasks"]}, {"task-1", "task-2"})
        self.assertEqual(next(x for x in merged["job_tasks"] if x["id"] == "task-1")["state"], "submitted")
        self.assertEqual(conflicts, [])


    def test_research_batches_survive_store_normalization(self):
        batch = {"id": "batch-1", "case_id": "case-1", "state": "prepared"}
        normalized = store.normalize({"research_batches": [batch]})
        self.assertEqual(normalized["research_batches"], [batch])

    def test_research_batches_merge_by_stable_id(self):
        base = {"research_batches": [{"id": "batch-1", "state": "prepared"}]}
        local = {"research_batches": [{"id": "batch-1", "state": "in_progress"}]}
        remote = {"research_batches": [{"id": "batch-1", "state": "prepared"},
                                      {"id": "batch-2", "state": "ready_to_merge"}]}
        merged, conflicts = store.three_way_merge(base, local, remote)
        self.assertEqual({x["id"] for x in merged["research_batches"]}, {"batch-1", "batch-2"})
        self.assertEqual(next(x for x in merged["research_batches"] if x["id"] == "batch-1")["state"], "in_progress")
        self.assertEqual(conflicts, [])


if __name__ == '__main__':
    unittest.main()
