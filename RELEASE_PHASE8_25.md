# Phase 8.25 — Data Safety & Task Lifecycle

## Added
- `job_control.py`: storage-agnostic lifecycle records for GitHub Actions requests.
- Task states: queued, submitted, running, succeeded, failed, cancelled, stale.
- Validated state transitions, bounded event history, heartbeat updates, stale-task flags, retry lineage, active-task lookup, and summaries.
- `job_tasks` is added to the normalized Gist store and three-way merge's stable-ID list handling.
- Dispatches initiated from the app (daily, search, topic, watch) are recorded before submission and updated with GitHub's immediate acceptance/rejection response.
- Operations view displays the recent local dispatch audit trail.

## Safety boundaries
- `submitted` means GitHub accepted the dispatch request; it does NOT mean the workflow completed.
- `stale` means no heartbeat was recorded within the threshold; it is a human-review flag, not proof of failure.
- GitHub Actions run status remains the authoritative execution status.
- Gist writes still do not provide an atomic cross-session compare-and-swap lock. Three-way merge detects many collisions but cannot eliminate the race between reading and patching.
- No automatic paid AI calls, no backups/restores, no secrets added.

## Validation
- Added 8 unit tests for lifecycle transitions, stale flags, retries, and summaries.
- Python compile and full unit test suite results are recorded in the release package after validation.
