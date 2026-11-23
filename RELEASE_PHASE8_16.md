# Phase 8.16 — Independent Off-site Backup Export & Restore

## Delivered
- Added a portable ZIP export format (`marsad-offsite-backup`) containing a manifest, creation timestamp, file count, and SHA-256 checksum for every data file.
- Added strict ZIP validation: supported schema, unique archive entries, safe relative paths, exact manifest/file-set matching, per-file checksums, and JSON parsing checks for `.json` files.
- Added export of a selected, verified Gist snapshot directly from the backup panel as a downloadable ZIP.
- Added import/restore of a user-held ZIP into Gist. The app validates the entire archive before mutation, creates a pre-restore safety snapshot in Gist, then applies the selected file set and refreshes the Streamlit store/baseline.
- The downloaded ZIP is independent of GitHub only after the user saves it outside GitHub (local computer, external drive, or another storage provider). No third-party storage account is assumed or connected.

## Local validation
- `python -m py_compile *.py tests/*.py`: passed.
- `python -m unittest discover -s tests -q`: 82 tests passed.
- Added tests for ZIP round-trip, checksum tampering rejection, invalid JSON rejection, and safety snapshot creation before restore.
- ZIP integrity: checked at release packaging.

## Not tested / limitations
- No live Gist export/import or disposable-Gist recovery drill was run.
- Streamlit is not installed in the build environment; UI interaction was not browser-tested.
- Gist restore remains a multi-request, non-atomic operation. The safety snapshot is created first, but a failure during the subsequent PATCH may leave a partial restore.
- The ZIP is not encrypted. Store it in a private location because it may contain sensitive research data. Encryption-at-rest and cloud off-site integrations are future work.
- No GitHub source-code push, Actions live run, or Streamlit Cloud deployment was performed.
