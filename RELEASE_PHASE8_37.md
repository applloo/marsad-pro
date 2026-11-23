# Phase 8.37 - Automated Case Workflow

## What changed
- One-click workflow inside each research case.
- Runs early-warning baseline/change scan, relationship co-mention network, narrative comparison, and intelligence report generation.
- Produces a concise run summary plus separate analysis and Egyptian-script prompts.
- Persists report and early-warning state through the existing store/Gist path when configured.
- Reuses an existing report when the case fingerprint and report type are unchanged.

## Important boundaries
- This phase processes materials already stored in the case.
- It does not fetch live news, trigger paid AI APIs, or schedule recurring GitHub Actions runs.
- A first run initializes a baseline; subsequent runs can identify additions/changes against that baseline.
- Alerts are review candidates, not confirmation of events. Network edges mean co-mention only, not verified relationships.
- Live Streamlit/Gist/GitHub deployment testing was not performed in the build environment.
