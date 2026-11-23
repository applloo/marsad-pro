# Marsad News Phase 8.38

## Scheduled collection and case monitoring
- Adds `.github/workflows/monitor.yml`, scheduled daily and manually dispatchable.
- Runs the existing `search_job.py` against the scopes configured in `marsad_search_cfg.json` in the shared Gist.
- Adds `scheduled_monitor.py`, which loads configured watched case IDs from `marsad_watch_cases.json`, matches collected items against case title/tags/monitor_terms, deduplicates by canonical URL, appends new material, and runs the existing 8.37 analysis workflow only when new material is added.
- Writes run status to `marsad_watch_status.json` in the Gist, including counts, per-case additions, errors, and no-change state.

## Required repository setup
The workflow is included in the release but cannot run in the user's GitHub repository until this release is pushed to the configured repository and repository Actions secrets `GIST_TOKEN` and `GIST_ID` are configured. `GIST_TOKEN` must be allowed to read and update the target Gist. `GITHUB_TOKEN` fallback may not have Gist write access, so a dedicated secret is recommended.

## Gist configuration
`marsad_search_cfg.json`: existing search configuration (`terms`, `scopes`, `days`, `joiner`, etc.).
`marsad_watch_cases.json`: `{"case_ids": ["case-id-1"], "scopes": ["il", "us", "uk", "rg", "eg", "wr", "wa"]}`. Empty/missing `case_ids` monitors all research cases that have matching title/tags/monitor_terms.

The daily schedule is 04:17 UTC (06:17 Cairo in winter, 07:17 in summer). It is not a real-time alerting service. Collection is limited to what existing search providers return; it does not bypass paywalls or guarantee exhaustive coverage.
