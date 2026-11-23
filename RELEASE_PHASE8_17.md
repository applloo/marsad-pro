# Phase 8.17 — Encrypted Off-site Backups

## Delivered
- Added client-side encryption for portable off-site backup archives using AES-256-GCM.
- Derives a 256-bit key from a user-held passphrase using PBKDF2-HMAC-SHA256 with 600,000 iterations and a random 16-byte salt; each archive also receives a random 12-byte nonce.
- The passphrase is not written to Gist, app storage, or the archive. The encrypted `.mrbak` file contains only a format marker, salt, nonce, and authenticated ciphertext.
- Added authenticated decryption and inner ZIP/manifest/SHA-256 validation before a backup can be previewed or restored.
- Streamlit UI now downloads encrypted off-site backups and accepts encrypted `.mrbak` files for restore.
- Restore decrypts and validates locally before using the existing guarded Gist restore path, which creates a pre-restore safety snapshot.
- Added `cryptography>=42.0.0` dependency.

## User-facing security notes
- Use a unique passphrase of at least 12 characters; a longer randomly generated passphrase is preferable.
- Keep the passphrase in a separate password manager or secure location. Losing it means the archive cannot be decrypted; there is no recovery key.
- AES-GCM detects tampering. The inner archive additionally verifies SHA-256 checksums, which detect accidental or malicious changes but are not a substitute for authentication.
- Encryption occurs in the running Streamlit server process before download. The passphrase is transient UI input and is not intentionally persisted, but the user should trust the app host and its operators.
- Gist restore remains non-atomic; this release does not claim a transactional recovery operation.

## Validation
- `python -m py_compile *.py tests/*.py`: passed.
- `python -m unittest discover -s tests -q`: 85 tests passed.
- Encrypted round-trip, wrong-passphrase rejection, ciphertext tamper rejection, and minimum passphrase length tests passed.
- ZIP package integrity checked after release packaging.
- No live Gist restore drill, Streamlit browser run, GitHub Actions execution, GitHub push, or deployment was performed.
