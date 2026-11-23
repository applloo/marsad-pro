# Phase 8.33 — Narrative Comparison & Evidence Matrix

## Scope
Extends the Phase 8.32 case research workspace with a source-by-source narrative comparison tool. It works only on materials already saved in a research case and makes no external requests.

## Changes
- Added `narrative_analysis.py` to group materials by source domain and expose source-independence caveats.
- Added comparison candidates for text-bearing materials with shared subject vocabulary, showing both excerpts, source names, dates, URLs, lexical polarity hints, and review questions.
- Distinguishes a possible lexical difference from a confirmed contradiction; no truth verdict is produced.
- Headline-only items are not treated as claim-level comparison evidence.
- Added an in-case UI panel with source map, comparison candidates, limitations, JSON report export, and a ready-to-use analysis prompt.
- The prompt requires claim/evidence separation, syndication checks, competing explanations, primary-source verification steps, confidence limits, and open questions.
- No AI API calls, paid services, new secrets, or automatic network collection.

## Tests
- 192 tests passed.
- Python compileall passed.
- ZIP integrity checked after packaging.
- One pre-existing warning comes from a test that intentionally creates a duplicate ZIP path to verify rejection.

## Not tested
- Streamlit runtime/UI, because Streamlit is not installed in the build environment.
- Live websites, GitHub/Gist synchronization, or deployment.
- No automated system can determine which narrative is true; candidates require human source review.
