# GitHub Auto-Sync — Phase 8.19

## What is implemented
- `github_sync.py` validates a release ZIP, rejects traversal/symlinks/duplicate paths and excludes secrets, backup archives and unsupported file types.
- It creates Git blobs/tree/commit through GitHub's Git Database API and advances the configured branch with `force=false` (no force push and no deletions).
- The Operations tab contains a release-sync panel. It previews the allowed file list before the explicit commit action.
- The sync token is read only from `GH_SYNC_TOKEN` in Streamlit Secrets / environment and is never written to Gist or app data.
- `.github/workflows/ci.yml` runs compile + unit tests on pushes and pull requests to `main`.
- If Streamlit Community Cloud is connected to the same repository/branch with deploy-on-push enabled, a successful push triggers its deployment flow.

## One-time setup still required
Add these Streamlit secrets:

```toml
GH_REPO = "applloo/marsad-news"
GH_BRANCH = "main"
GH_SYNC_AUTO = true
GH_SYNC_TOKEN = "<fine-grained-token>"
```

Set `GH_SYNC_AUTO = true` to automatically create the commit after a new release ZIP is uploaded in the Operations tab. If false/omitted, the app asks for a manual push click. The fine-grained token must be limited to the target repository and grant **Contents: Read and write**. Keep the token in Streamlit Secrets only. Existing `ACTIONS_TOKEN` remains separate and is used for workflow dispatch/monitoring.

## Important boundary
This release provides an authenticated in-app release-to-GitHub commit path, not an already-connected ChatGPT-to-GitHub development session. The current build environment has no authorized GitHub write credential or repository connector, so no remote commit/push or live deploy is claimed. Until the one-time secret is configured and a successful commit is verified, release ZIP import into the sync panel remains the bridge. Even with auto mode, ChatGPT-generated files must first reach the Streamlit sync panel; direct push from this chat is not enabled in the current environment. Direct automatic commits from future ChatGPT code edits require an authorized GitHub connector or equivalent write integration in the development environment.
