# Phase 8.29 — Search Consistency & Date Integrity

## Delivered
- Unified the author/opinion-writer search path with the same exact date-window filtering used by the other search scopes.
- Added Arabic translation of available snippets/descriptions to writer-search cards, with explicit missing/translation-failure states inherited from the shared card-preparation pipeline.
- Extended the GitHub-wide search period selector to include 14 and 30 days, matching the supported period range elsewhere in the app.
- Improved timestamp selection: an invalid primary timestamp no longer masks a valid fallback timestamp. The selected timestamp field is recorded as `date_window_field`; undated records remain explicitly marked `unknown_date`.
- Added regression tests for writer search filtering, Arabic snippet preparation, and timestamp fallback behavior.

## Safety and cost
- No paid AI API calls added.
- Translation continues through the existing free translation helper.
- Undated records remain visible but are not falsely labeled as within the selected date window.
- No backup/restore functionality added.

## Validation
- Python compilation: passed for `app.py`, `core.py`, `search_job.py`, and `intelligence_pipeline.py`.
- Full test suite: 174 passed.
- ZIP integrity: checked after packaging.

## Limitations
- Streamlit UI was not launched in a browser in this environment.
- Live publisher crawling, GitHub Actions dispatch, Gist sync, and Streamlit deployment were not performed.
