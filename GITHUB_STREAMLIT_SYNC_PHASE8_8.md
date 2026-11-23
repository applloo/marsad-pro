# Phase 8.8 — GitHub / Streamlit deployment and scheduling

## What changed
- Added a concurrency group to each GitHub Actions workflow so two runs of the same workflow on the same ref do not execute simultaneously.
- Preserved the existing daily scheduled report and all manual workflow triggers.
- GitHub Actions now accepts either `GIST_TOKEN` (legacy name) or `GITHUB_TOKEN` for Gist storage.
- Expanded the Streamlit deployment guide to explain that Streamlit Cloud Secrets and GitHub Actions Repository Secrets are separate stores. The same Gist token and Gist ID must be entered in both places when both services need them.
- Kept `ACTIONS_TOKEN` separate: it is used by the Streamlit UI to dispatch workflows and is not the Gist storage token.

## What did not change
- No workflows were removed.
- The daily report schedule remains `04:00 UTC`.
- Search-all remains manually dispatchable and now also runs daily at 07:00 UTC (09:00 Cairo); custom watch and topic tracking remain manually dispatchable.
- Streamlit remains the UI; GitHub Actions remains the automation runner; Gist remains the persistent JSON store.
- No API key or GitHub secret was added to the source tree.

## Deployment steps
1. Update the GitHub repository with this version.
2. In Streamlit Cloud Secrets, keep `GITHUB_TOKEN`, `GIST_ID`, and `ADMIN_KEY` as applicable.
3. In GitHub Repository Actions Secrets, add `GITHUB_TOKEN` and `GIST_ID` with the same storage values. Existing `GIST_TOKEN` continues to work.
4. Keep `ACTIONS_TOKEN`, `GH_REPO`, and `GH_BRANCH` in Streamlit Cloud if the UI should trigger workflows.
5. Run the daily workflow manually once and confirm it finishes successfully and updates `marsad_reports.json` in the configured Gist.
6. Trigger search or watch from the UI and confirm the result appears in the Gist and then in Streamlit.

## Validation limits
- Python compilation and the existing unit suite validate the local source only.
- A real GitHub Actions dispatch, Streamlit deployment, and Gist write/read cycle require the user's connected GitHub repository and configured Secrets. They were not performed from this local build.

## Phase 8.8 schedule
- Daily report: 04:00 UTC (06:00 Cairo).
- Full-source search: 07:00 UTC (09:00 Cairo).
- The full-source search retains `workflow_dispatch` for manual runs.
- Workflow concurrency guards prevent overlapping runs of the same workflow on the same branch.
