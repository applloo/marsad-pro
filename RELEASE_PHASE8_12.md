# Marsad News — Phase 8.12

## Data integrity and billing profiles

- Added three-way merge for the Streamlit owner store: non-overlapping dictionary edits and distinct ID-based records can merge; overlapping edits, conflicting deletes/edits, and conflicting record-order changes are detected and saving is stopped rather than silently overwriting the latest remote version.
- The owner session retains a baseline snapshot and refreshes it after a successful save.
- Added persistent billing profiles keyed by provider + exact model ID. Profiles store input/output price per million tokens, monthly local budget, currency, optional pricing source URL, and last-reviewed timestamp. API keys are not stored in these profiles.
- Gemini and custom OpenAI-compatible paid routes can save and reuse their model-specific pricing profiles.
- Monthly spend checks for paid analysis requests are model-specific. The preflight check disables sending when the estimated request would exceed the locally recorded model budget.
- Existing usage ledger and explicit per-request approval remain in place.
- Kept separate GitHub Actions concurrency groups for each workflow. A single shared GitHub Actions concurrency group is deliberately avoided because GitHub allows only one pending run per group and a newer pending run can replace an older pending run. This could silently skip a scheduled or manual workflow.

## Important limitations

- Three-way merge reduces stale-session overwrites but is not an atomic compare-and-swap transaction. GitHub Gist PATCH does not provide a transactional lock for this JSON document; a very narrow simultaneous read/patch race remains possible.
- Model budgets are local application guardrails, not provider-side billing caps. Concurrent Streamlit sessions and external API usage can make the actual provider invoice exceed the local estimate.
- Token estimates remain approximate before the request. Actual provider usage metadata is recorded when returned.
- Billing profiles store user-entered prices and an optional source URL; the application does not independently verify prices against the provider's live pricing page.
- No live Gist, provider API, GitHub Actions, or Streamlit Cloud deployment test was performed.

## Validation

- Python compilation passed.
- `python -m unittest discover -s tests -q`: 58 tests passed.
- ZIP integrity checked after packaging.
