# Release Notes — Phase 8.21
## Cumulative Intelligence Case File

### Added
- Added `case_intelligence.py` to maintain a cumulative, versioned record for each research case.
- Added on-demand snapshots with content fingerprints, avoiding duplicate snapshots when nothing changed.
- Added append-only evidence history for materials, claims, and events. New items, edited items, claim evidence-status changes, removals from the current case, and later restorations are recorded as change events.
- Added source-preserving change entries with before/after payloads and changed-field lists.
- Added explicit links to saved Phase 8.20 intelligence dossiers only when a prior-case match contains the exact research-case ID; inferred or guessed dossier links are not created.
- Added a cumulative update prompt that asks the AI model to update the existing assessment, distinguish new facts from corrections and interpretations, preserve unresolved contradictions, and review prior conclusions. It is a copy/download artifact and does not call an AI provider.
- Added the Arabic cumulative intelligence panel to the existing research casebook, with snapshot/change counters, recent history, prompt export, and JSON record export.
- Added `intel_case_files` to the existing app-data store and merge/normalization logic. No new external storage service was introduced.
- Deleting a research case also deletes its associated cumulative record and case links, consistent with the app's existing delete action.

### Safety and methodology
- No automatic AI/API call, paid request, background web search, or GitHub push is triggered.
- The researcher explicitly chooses when to create a snapshot.
- Removed materials remain in the cumulative evidence ledger with a removal marker; they are not silently erased from history.
- A changed evidence status is a record of the researcher's edit, not proof that the underlying claim became true or false.
- This is an in-app cumulative research history, not a backup/restore feature and not an immutable external audit log.
- No backup/restore features were added.

### Validation
- `python -m py_compile *.py tests/*.py`: passed.
- `python -m unittest discover -s tests -q`: 116 tests passed.
- Streamlit browser interaction, Gist persistence against a live account, GitHub commit/CI, and deployment require runtime credentials/environment and were not claimed as tested here.
