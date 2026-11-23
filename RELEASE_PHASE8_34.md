# Phase 8.34 — Article-to-Script Workflow & Search Persistence

## Delivered
- Added `article_script_prompts.py` to generate a structured, source-grounded Arabic/Egyptian script-analysis prompt for one article or a manually selected group.
- Each prompt preserves title variants, publisher/domain, author, date, URL, and available extracted text/snippet.
- Prompt instructions require claim/evidence separation, rebuttal and alternative explanations, source independence checks, event-vs-publication date distinction, Egypt/regional impact only where supported, confidence caveats, and a final fact-check table.
- Added per-result actions: generate a prompt for one article; search for open alternative coverage using title, translated title, author, and topic queries in Google and Google News.
- Added manual checkboxes for selecting multiple articles and generating one combined analytical/script prompt.
- Added prompt generation from saved-for-later articles.
- Added a global search-results dock outside the main tabs, so result sets remain accessible while navigating across all app sections.
- Improved result-set signature so URL changes are detected even when result counts remain the same; added visible persistence/recovery guidance and a manual reload action when no results are loaded.
- Confirmed existing save-for-later implementation remains present and persistent through the app's `saved` store collection when GitHub Gist persistence is enabled.

## Important limitations
- Open-alternative links are search paths, not a guarantee that a free equivalent exists.
- No paywall bypass or restricted-content extraction is attempted.
- Prompt generation is local and free; it does not call an AI API. The user copies/downloads the prompt and submits it to their chosen AI service.
- Cross-session persistence requires the app's existing owner GitHub Gist configuration (`GITHUB_TOKEN` and `GIST_ID`). Without it, results and saved items remain session-local/in-memory and can disappear after a restart.
- Streamlit UI, live search providers, GitHub/Gist network persistence, and deployment were not live-tested in this environment.

## Tests
- 196 tests passed.
- 1 expected warning from the existing duplicate-ZIP-path rejection test.
- Python compile checks passed.
- ZIP integrity check passed.
