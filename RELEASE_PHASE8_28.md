# Phase 8.28 — Search, Translation & Automatic Intelligence Pipeline

## Delivered
- Added `intelligence_pipeline.py` for UTC date-window handling, strict post-filtering, URL normalization, conservative lexical thread candidates, Arabic card summaries from supplied snippets, and automatic research-batch preparation.
- Added six-hour search-all option; existing 12-hour and longer options remain.
- Main interactive search now applies a strict time-window post-filter after merging GDELT, Google News and direct-feed results. Undated results remain visible but are explicitly marked `unknown_date` rather than silently discarded.
- Main search automatically translates available snippets/descriptions into Arabic for article-card summaries using the existing free translation path. Missing snippets and translation failures are labeled honestly.
- Search completion automatically creates a provenance-preserving research batch from the collected results, persists it through the existing store path, and offers a first-batch prompt download.
- Added candidate news-thread clustering with source domains and stable source IDs. The UI explicitly labels it as lexical candidate grouping, not factual confirmation.
- GitHub Actions search scopes now apply strict post-filtering for the configured hour window after broad upstream retrieval and prepare Arabic summaries.
- Existing article reader remains in place and continues to distinguish inaccessible/partial articles from extracted text. Paywalls are not bypassed.

## Safety and cost
- No paid AI API calls were added. Summary translation uses the existing translation helper; research prompts are generated locally.
- The automatic summary is a translation of the available snippet/description, not a claim to summarize the full article. Full article extraction remains subject to publisher access, robots restrictions, JavaScript rendering, and paywalls.
- Missing publication timestamps are labeled unknown and retained for review; they are not falsely represented as falling inside the selected window.

## Validation
- `python -m py_compile app.py core.py search_job.py intelligence_pipeline.py`
- `python -m pytest -q`: 171 passed.
- ZIP integrity checked after packaging.

## Limitations not claimed as solved
- The Streamlit UI was not launched in a browser in this environment.
- Live crawling of Israeli, US, UK, or other publisher sites was not performed as part of this offline build verification.
- Precise filtering can only use timestamps supplied by a provider. Undated homepage items remain visible with an unknown-date marker.
- Automatic thread grouping is lexical and should be reviewed before merging distinct events into one research case.
- GitHub push, Gist sync, and Streamlit deployment were not performed.
