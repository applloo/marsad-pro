# Marsad News — Phase 8.11

## Prompt Workbench

- Persistent user prompt library stored in the existing Gist data store.
- Create named prompts with category and description.
- Every edit creates a new immutable version; prior versions remain available.
- SHA-256 fingerprint and timestamp stored for each version.
- Restore an old version by creating a new version from it, never by overwriting history.
- Archive and restore prompts without deleting them.
- Saved prompts can be selected while building analysis packages; the case context is appended to the saved prompt.
- Existing built-in analysis prompts and Phase 8.10 human-approved AI routing remain available.
- API keys are not stored in prompt records.

## Validation

- Python compilation and unit tests are run for this release.
- Streamlit browser interaction, live API calls, GitHub push, and Streamlit Cloud deployment are not claimed unless separately completed.
