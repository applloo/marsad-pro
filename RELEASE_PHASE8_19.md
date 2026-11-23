# Phase 8.19 — Source Health & Intelligence Clustering

## Delivered

### Source Health
- Merged 299 unique domains from the existing Israeli, US, UK, regional, Arabic, Egyptian, intelligence-office, and paid-radar registries.
- Concurrent HTTPS homepage probing with bounded worker count and timeout.
- RSS/Atom discovery through `link rel=alternate` and common public feed paths. Redirects are followed manually only after each HTTPS destination passes the public-host safety check.
- Reports HTTP status, latency, discovered feed URL, latest feed headline/date, and cautious failure states.
- Compares the latest run with the prior saved run to detect changed RSS URLs, disappeared feeds, recovered sites, newly observed feed headlines, and temporary reachability loss.
- Exports the result as CSV and stores the last five runs in the existing app data store when Gist persistence is configured.

### Intelligence Clustering
- Collects headlines from GDELT and Google News RSS across selected US, Israeli, UK, and Arabic/regional source perspectives.
- Translates collected headlines into Arabic while retaining original headline and source URL.
- Clusters related headlines using token similarity, title normalization, and publication-time windows.
- Compares coverage by source perspective and distinguishes headline-based analysis/opinion, wire-service candidates, early observed timestamps, and likely syndication candidates.
- Builds a unified case dossier with article provenance, event clusters, perspective narratives, tentative origin/syndication assessments, methodology, and limitations.
- Exports the dossier as JSON and persists it in Gist using stable IDs.

### GitHub Release Sync
- Added `github_sync.py` using GitHub Git Database API: fetch branch ref, create blobs, create tree, create commit, and advance the branch with `force=false`.
- Added ZIP safety validation: path traversal and symlink rejection, duplicate-path rejection, per-file/total size limits, extension allowlist, and exclusion of `.env`, secrets files, `.mrbak`, ZIP archives, and backup artifacts.
- Added an Operations-tab sync panel with file preview and optional automatic commit after a new ZIP upload (`GH_SYNC_AUTO=true`). No deletion or force-push is performed.
- Added `.github/workflows/ci.yml` for Python compile and unit tests on pushes and PRs to `main`.
- Documented one-time Streamlit Secrets: `GH_REPO`, `GH_BRANCH`, `GH_SYNC_TOKEN`, and optional `GH_SYNC_AUTO=true`.

## Source counts
- 299 unique domains in the merged runtime health catalog.
- Perspectives represented: US, Israeli, UK, Arabic/regional, Egyptian, and other international sources.

## Validation
- `python -m py_compile *.py tests/*.py`: passed.
- `python -m unittest discover -s tests -q`: **102 tests passed**.
- GitHub sync tested with mocked API responses, including non-force branch update.
- RSS parsing, feed-change detection, date-window clustering, perspective grouping, and dossier generation tested locally.
- ZIP payload is generated and integrity-checked separately.

## Not tested / important limits
- No live scan of the 299 domains was run in this build session.
- No Streamlit browser run was possible because Streamlit is not installed in the build environment.
- No real GitHub credentials or repository connector were available; no real commit/push, Actions execution, or Streamlit deployment is claimed.
- The GitHub sync panel needs one-time configuration in Streamlit Secrets. `GH_SYNC_AUTO=true` auto-commits after a ZIP is uploaded in the app, but does not itself connect this ChatGPT conversation directly to GitHub.
- Health probes can be blocked by anti-bot systems or transient DNS/network problems. Such failures are not proof that a publisher has shut down.
- Event similarity and origin/syndication labels are heuristic. The earliest observed headline is not proof of original publication, and a similar headline is not proof of copied content.
- Perspective labels classify source geography, not truthfulness or political alignment. Official sources are treated as the issuing institution's account, not independent verification.
- Backups and backup workflows remain removed as requested; no backup feature is included in this release.
