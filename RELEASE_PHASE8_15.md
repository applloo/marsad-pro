# Release Notes: Phase 8.15 - Spend Reservations & Workflow Visibility

## Objective
Reduce accidental budget overspend across ordinary overlapping app sessions, cover paid text/content/image paths consistently, and make GitHub Actions activity easier to inspect without introducing a lossy shared concurrency group.

## Implemented
- Added `billing_reservations` to the persistent store. Reservations are keyed by unique request IDs and scoped by provider, exact model, and UTC month.
- Added reservation lifecycle helpers: create, expire-aware active lookup, settle, release/fail, and budget preflight including committed usage plus active reservations.
- Paid text analysis, content generation, and OpenAI image generation now create a reservation before the external API call. When Gist persistence is configured, a failed reservation save or detected merge conflict blocks the paid call.
- After reservation persistence, each paid path rechecks the merged store's committed spend plus all active reservations before calling the provider.
- Successful calls settle the reservation and record usage; failed calls mark the reservation failed so it no longer counts as active. Pending reservations expire after 15 minutes by default.
- Image generation now requires a user-entered monthly image budget in addition to a reviewed unit price and explicit per-image approval.
- Added a GitHub Actions operations overview in the operations room, listing recent runs for daily, search, topic, watch, and backup workflows.
- Kept separate workflow concurrency groups. The new overview is observability only, not a durable queue or cross-workflow lease.

## Important limitations
- Gist PATCH is not atomic compare-and-swap. The reservation merge/recheck is a best-effort guard and reduces ordinary overlapping-session overspend, but a narrow simultaneous read/modify/write race remains possible. It is not a hard distributed lock or provider-side billing cap.
- When Gist persistence is not configured, reservations are session-local and do not coordinate separate users/sessions.
- A timed-out request may have been billed by the provider even if the app did not receive a response. Its reservation expires after 15 minutes; reconcile provider usage before relying on remaining local budget.
- Workflow overview requires `ACTIONS_TOKEN` with Actions read access. It displays recent runs but does not dispatch, serialize, retry, or resume them.
- No global shared GitHub Actions concurrency group was added because newer pending runs can replace older pending runs within a concurrency group.

## Validation
- `python -m py_compile *.py tests/*.py`: passed.
- `python -m unittest discover -s tests -q`: 78 tests passed.
- ZIP integrity: passed.
- No live provider API calls, live Gist concurrency test, Streamlit browser run, GitHub Actions run, repository push, or deployment was performed.
