# Phase 8.26 — Resumable Large Research Engine

## Added
- `research_batches.py`: prepares large case research into bounded, resumable batches.
- Stable per-source IDs derived from canonical URL (or a metadata fallback), deduplication, and a source manifest retaining original URL, publisher/domain, title, publication date, and available excerpt/text.
- Per-batch prompts require claim/evidence separation, explicit source IDs, publication-vs-event date distinction, contradiction tracking, and syndication caution.
- Manual result capture with pending/completed/failed states, retry of failed batches, progress summary, and final synthesis prompt only after every batch is completed.
- Streamlit UI embedded in the active research case: create batches, download/copy prompts, paste outputs, resume incomplete work, and generate the final merge prompt.
- `research_batches` added to the normalized Gist store and stable-ID three-way merge lists.

## Cost and data boundaries
- Creating batches, prompts, and merge prompts is local application logic. No model/API request is made.
- User manually sends prompts to a model or approved provider. This preserves the existing explicit-consent workflow.
- The engine does not crawl article URLs. It uses only content already present in case materials.
- Source text is clipped to 5,000 characters per material; batch output is clipped to 30,000 characters. Full originals remain in their original case materials where those records retain them.
- Gist is used as the application's existing data store, not as backup/restore.
- No backup/restore functionality added.

## Validation
- Unit tests cover chunking, deduplication, provenance, retry, merge gating, output limits, and progress.
