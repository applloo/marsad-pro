# Marsad News Phase 8.36 — Intelligence Report Center

## New in this release
- Adds `intelligence_reports.py` to build evidence-linked reports from the current research case.
- Supports six report profiles: comprehensive case intelligence, daily developments, narrative/source comparison, actor network, alerts/changes, and verification gaps.
- Preserves source title, URL, publisher, author, date, type, source ID, and available excerpt.
- Carries case claims with their entered evidence status and links, plus the case timeline.
- Explicitly flags missing source text, missing original URLs, absent claim/event records, and limited source diversity.
- Produces Markdown report, analytical prompt, and Egyptian Arabic video-script prompt.
- Persists reports in the existing store/Gist structure under `intel_reports`, with a bounded history and case-deletion cascade.
- Does not call paid AI APIs, scrape paywalled content, or claim independent fact verification.

## Validation
- `python -m py_compile *.py`: passed.
- `PYTHONPATH=. pytest -q --disable-warnings`: 203 passed, 1 existing expected warning.
- ZIP integrity: verified separately at packaging.

## Limitations
- Streamlit runtime/browser interaction was not tested in this build environment.
- GitHub/Gist live persistence and external source retrieval were not exercised.
- The report is a structured compilation of the case data available at generation time, not an automatic fact-check.
