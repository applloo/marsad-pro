# Active scope update — Phase 8.18

The user's current priority is source intelligence and content discovery, not backups. Dedicated backup UI, workflow, modules, tests, and encryption dependency have been removed in Phase 8.18. Older Phase 8.14–8.17 notes are historical release records only. Gist remains the existing app-data persistence mechanism and is not being expanded as a backup product.

# Marsad News — implementation audit and remaining roadmap

Audit basis: the Phase 8.10 source ZIP was inspected directly. Phase 8.11 changes in this release were then added to that source. Local validation is not evidence of a live deployment or live provider billing.

## Implemented in the source tree

### Research and case management
- Research cases with materials, claims, and dated events.
- Case links and thread context, including safeguards against treating temporal association as proof of causality.
- Early-warning baselines and reports, currently run on demand.
- Manual stance-change records and conditional scenario worksheets.
- Analysis packages with immutable source snapshots, SHA-256 fingerprints, version numbers, and Markdown/TXT/JSON exports.

### AI and content production
- Gemini, OpenRouter free route, Groq, Cloudflare Workers AI, local Ollama, and a custom OpenAI Chat Completions-compatible endpoint.
- Manual model override and human approval before each API action.
- Usage records with provider/model/task/tokens and estimated cost where available.
- Content-production briefs, storyboard/visual-production plans, editing maps, production ZIP bundles, and OpenAI image generation.
- Image price is user-entered and confirmed per generation; generated image bytes remain in the Streamlit session until downloaded or included in a production ZIP.
- Phase 8.10 task-specific conversation prompts and cost preview.
- Phase 8.11 persistent prompt library: create, edit as a new immutable version, inspect history, rollback as a new version, archive, restore, download, and select saved prompts during case-package creation.

### Automation and storage
- GitHub Actions workflows for daily report, full-source search, topic tracking, and watch tracking.
- Daily report schedule at 04:00 UTC and full-source search at 07:00 UTC; manual triggers remain enabled.
- Per-workflow concurrency groups; these do not create one global queue across every workflow.
- GitHub Gist is used for application data persistence. This is not source-code synchronization or a Git commit/push.
- Streamlit Secrets and GitHub Actions Repository Secrets are separate and documented.

## Partially implemented / limitations

1. **Auto AI Router is advisory, not yet intelligent benchmarking.** It uses fixed task priority lists and detects configured providers. It does not measure current latency, quota, model quality, context limits, or live prices, and does not automatically compare multiple candidate models.
2. **Cost protection is an estimate, not a hard billing guarantee.** Text prices are entered by the user for Gemini/custom paid routes; input tokens use a rough character-based estimate before the request. Provider invoices may differ. Monthly caps are entered in the UI and checked against local usage records; they are not a provider-side hard stop and are not an atomic cross-session reservation.
3. **Protocol coverage is limited.** Gemini has its own connector; custom endpoints support OpenAI Chat Completions compatibility. Native Anthropic Messages, native Cohere/Mistral APIs, and other distinct protocols need dedicated adapters.
4. **Prompt Workbench scope.** The new library is persistent and versioned, but prompts are currently applied while building a single research-case package. A cross-case research brief, reusable multi-stage workflow chains, and automatic prompt variables are still future work.
5. **Large packages.** Automatic chunking, context-window planning, per-chunk provenance, retry/resume, and merging model outputs are not implemented yet.
6. **Image persistence.** Generated images are session-held until the user downloads the production ZIP; they are not durable image objects in Gist storage.
7. **Early warning.** The baseline scan is available on demand; scheduled case-specific monitoring and notification rules are not implemented.
8. **Workflow concurrency.** Each workflow prevents overlapping runs of itself on the same ref. There is no global cross-workflow lock. Current jobs generally write separate Gist filenames, but shared-file writes should be audited before adding workflows.
9. **Multi-session Gist writes.** The Streamlit `persist()` flow reloads the Gist before saving, but the JSON file update is not an atomic compare-and-swap transaction. Two owner sessions changing the same store around the same time could still overwrite each other's edits. Optimistic concurrency and conflict resolution remain a priority.
10. **Local versus hosted execution.** `127.0.0.1` for Ollama inside Streamlit Cloud points to the hosted container, not the user's PC. Local Ollama is useful only when the app and Ollama are on the same machine/network or a secure reachable endpoint is configured.

## Not yet verified in a live environment

- GitHub repository push/commit and automatic Streamlit Cloud redeployment.
- GitHub Actions dispatches and scheduled workflow completion against the user's actual repository and Gist.
- Real Gist read/write and recovery under concurrent sessions.
- Live Gemini, Groq, OpenRouter, Cloudflare, custom endpoint, Ollama, and OpenAI Images API requests.
- Streamlit browser interaction and end-to-end UI testing on Streamlit Cloud.
- Actual provider invoice reconciliation against the local usage ledger.

## Recommended execution order

### Priority 1 — data integrity and safe operations
- Add optimistic concurrency/version checks for Gist writes, conflict messages, and safe retry/merge behavior.
- Persist model pricing profiles and monthly caps per provider/model, with explicit last-reviewed timestamps and currency.
- Add a hard local preflight reservation for estimated spend so two simultaneous approvals cannot both consume the same remaining local budget; clearly distinguish it from provider-side billing limits.
- Add a global job status/queue view and review shared Gist filenames across workflows.

### Priority 2 — Prompt Workbench expansion
- Add reusable prompt variables and validated placeholders for case title, time window, selected threads, source bundle, output format, dialect, and duration.
- Add multi-case and multi-thread research packages with deduplication and provenance.
- Add prompt chains: collect/extract → verify → connect events → geopolitical analysis → Egyptian script → production plan.
- Add output review, revision comparison, and approval status for final scripts.

### Priority 3 — reliable AI orchestration
- Add protocol-specific adapters (starting with Anthropic Messages and other explicitly selected providers).
- Add model capability registry: context size, supported modalities, JSON output, tool use, and known pricing source/date.
- Make Router recommendations explainable and cost-aware, with manual approval and fallback suggestions only.
- Add chunking, retry/resume, merge, citations/provenance retention, and per-chunk cost accounting.

### Priority 4 — deployment and operations
- Connect the actual GitHub repository for source commits/pushes and verify Streamlit auto-deploy.
- Add automated smoke tests and a release checklist for the live app.
- Add backup/restore drills and retention controls for large result/image histories.
- Add scheduled early-warning checks and notifications only after data-integrity protections are in place.

## Phase 8.11 local validation
- `python -m py_compile *.py`: passed.
- `python -m unittest discover -s tests -q`: 48 tests passed.
- ZIP integrity check: passed.
- No live provider request, GitHub push, or Streamlit Cloud deployment was performed.

## Phase 8.12 additions
- Three-way merge uses the session baseline, local state, and latest Gist state. Independent dictionary changes and distinct ID-based records can merge; overlapping edits, deletions versus edits, and conflicting list order changes are reported and the save is stopped.
- Billing profiles are persisted per exact provider/model ID, including input/output prices per million tokens, monthly local budget, optional pricing source URL, currency, and last-reviewed timestamp. Gemini and custom OpenAI-compatible paid analysis reuse these settings.
- Paid analysis spend checks are model-specific and preflight blocks a request when the projected amount exceeds the model's local monthly budget.
- Workflow concurrency remains separate per workflow. A shared GitHub Actions concurrency group was rejected because GitHub retains only one pending run per group, so newer queued runs can replace older pending runs.
- These safeguards are best-effort, not transactions: Gist PATCH still has a narrow simultaneous read/write race, and local budgets are not provider-side hard caps.
- Phase 8.12 local validation: Python compilation passed; 58 unit tests passed; no live services were exercised.

## Updated next priorities
1. Add durable backup/restore snapshots and an operational recovery drill for the Gist store.
2. Expand Prompt Workbench with validated variables, multi-case/thread bundles, prompt chains, and output review/approval.
3. Add a true durable cross-workflow queue/lease only if it can be implemented without GitHub pending-run replacement or unsafe non-atomic Gist locking.
4. Add protocol-specific model adapters and capability metadata.
5. Add large-package chunking, resumable jobs, provenance-preserving merge, and per-chunk cost accounting.
6. Connect the actual GitHub repository and verify push, Actions, and Streamlit deployment only after repository access is authorized.

## Phase 8.13 status - Prompt Workbench Pro
Implemented in the working release package:
- Prompt variable substitution for case title, dates, parties, threads, preferred sources, output type, dialect, duration, audience, research question, and extra instructions.
- Missing and unknown variables are surfaced; no silent guessing.
- Multi-case bundle snapshots deduplicate materials by URL and retain provenance edges to every source case. URL-less materials use a title/text fingerprint.
- Six-stage resumable manual chain: extraction, verification, event/thread linkage, geopolitical analysis, Egyptian-dialect script, and production plan.
- Stage outputs persist and are included in later-stage prompts only when marked completed. Skipped prior stages are explicitly flagged.
- Same-stage output comparison prompt, final review, human approval, and SHA-256 fingerprint.
- Bundles/chains are stored in the app data store and participate in ID-based three-way merge.

Validation: `python -m py_compile *.py` passed; `python -m unittest discover -s tests -q` passed (65 tests). Streamlit UI and live Gist were not exercised in this environment. No GitHub push or deployment was performed.

Remaining roadmap:
1. Phase 8.14: backup rotation and tested restore/recovery drill for Gist data.
2. Harden concurrent budget reservation and durable job coordination without a lossy shared GitHub Actions concurrency group.
3. Audit all paid text/image/content generation paths for preflight estimates, explicit consent, and complete usage logging.
4. Add provider-native adapters and a capability registry while keeping the router advisory.
5. Configure authorized GitHub commit/push and Streamlit Cloud deployment workflow; not yet connected or executed.

## Phase 8.14 additions
- Added compressed Gist snapshots covering all current Gist text files, with SHA-256 validation and a manifest.
- Added weekly backup automation (Sunday 02:30 UTC) plus manual workflow dispatch; default retention is 10 snapshots.
- Added UI inspection and guarded restore. A pre-restore safety snapshot is created before files are replaced; the app store and session baseline are refreshed afterward.
- Added tests for snapshot round-trip, corruption/checksum rejection, mocked backup creation, and workflow wiring.
- Important: backups are stored in the same Gist, not off-site. Gist PATCH/rotation/restore is not atomic and does not provide a cross-session lock. Configure a user PAT with Gist scope in `GIST_TOKEN` (or a user-provided `GITHUB_TOKEN` secret); the default Actions token is not assumed to have Gist access.

## Phase 8.14 local validation
- `python -m py_compile *.py tests/*.py`: passed.
- `python -m unittest discover -s tests -q`: see final release validation result.
- ZIP integrity: see final release validation result.
- No live Gist, GitHub Actions, Streamlit browser, GitHub push, or deployment test was performed.

## Updated next priorities
1. Add independent off-site backup export and a restore drill against a disposable test Gist.
2. Harden simultaneous budget reservations and audit every paid text/image/content-generation path.
3. Implement durable cross-workflow job coordination without a lossy shared Actions concurrency group or unsafe Gist lock assumptions.
4. Add provider-native adapters and model capability metadata.
5. Connect authorized GitHub commit/push and verify Streamlit Cloud auto-deploy.

## Phase 8.15 status - Spend Reservations & Workflow Visibility
- Added persistent-intent reservations for paid text analysis, content generation, and image generation. Reservations include request ID, provider, exact model, UTC month, amount, creation/expiry timestamps, and lifecycle status.
- Budget checks now count recorded usage plus unexpired pending reservations. The paid paths reserve before calling the provider, persist/reconcile the reservation, and recheck the merged store before making the API request. Successful calls settle the reservation; failures release it from active accounting.
- Image generation now requires a monthly budget as well as a reviewed unit price and explicit per-image approval.
- Added a GitHub Actions recent-run overview for daily/search/topic/watch/backup in the operations room. This is monitoring only; it is not a central queue or lease manager.
- Kept independent Actions concurrency groups to avoid replacement of pending runs.

### Phase 8.15 limits and unverified behavior
- Gist PATCH is not atomic CAS. Two truly simultaneous sessions can still race between read and patch; the new reservation mechanism is best-effort and not a hard distributed lock.
- If Gist persistence is disabled, reservations coordinate only within the current session.
- A provider may bill a request that times out before the app receives its response. Reservations expire after 15 minutes, so provider-side usage reconciliation remains necessary.
- No live provider calls, live Gist concurrency test, Streamlit browser test, GitHub Actions live test, repository push, or deployment was performed.

### Phase 8.15 local validation
- `python -m py_compile *.py tests/*.py`: passed.
- `python -m unittest discover -s tests -q`: 78 tests passed.
- ZIP integrity: passed.

## Updated next priorities
1. Add independent off-site backup export and run a restore drill against a disposable test Gist.
2. Evaluate a real transactional coordination backend (for example, a managed database/Redis service) before claiming hard cross-session budget enforcement or a durable cross-workflow queue.
3. Add provider-native adapters and model capability metadata while keeping routing advisory and every paid call explicitly approved.
4. Add resumable chunking with per-chunk provenance and cost accounting.
5. Authorize and configure GitHub source-code commit/push, then verify Actions and Streamlit Cloud deployment end-to-end.

## Phase 8.16 status — Independent Off-site Backup Export & Restore
- Added a portable ZIP archive format with manifest and per-file SHA-256 integrity checks.
- Added a download action for selected Gist snapshots, so the user can retain copies outside GitHub.
- Added validation and guarded restore from a user-held ZIP. A pre-restore Gist safety snapshot is created before applying the imported data; Streamlit session state is refreshed afterward.
- ZIP validation rejects unsupported schemas, duplicate entries, unsafe paths, mismatched file sets, checksum failures, and invalid JSON files.
- Local validation: Python compilation passed; 82 unit tests passed; ZIP integrity checked.
- Limits: off-site independence requires the user to download/store the ZIP elsewhere; archive is not encrypted; Gist restore remains non-atomic. No live Gist, browser, recovery drill, Actions, GitHub push, or Streamlit deployment was tested.

## Updated next priorities
1. Run a real recovery drill against a disposable Gist after authorized credentials are configured; verify post-restore application loading and compare expected file hashes.
2. Add optional client-side encryption for downloadable backups, with a user-held passphrase that is never sent to Gist.
3. Evaluate an external transactional backend for atomic spend reservations and durable workflow leases.
4. Add provider-native adapters and capability metadata, then resumable chunking with provenance and per-chunk cost accounting.
5. Configure authorized GitHub commit/push and verify Actions and Streamlit Cloud deployment end-to-end.

## Phase 8.17 status — Encrypted Off-site Backups
- Added local AES-256-GCM encryption of portable off-site ZIP backups, with PBKDF2-HMAC-SHA256 (600,000 iterations), random 16-byte salt, and random 12-byte nonce.
- Added encrypted `.mrbak` export/import controls. Passphrases are not stored in Gist or app settings; decryption validates the authenticated ciphertext and inner ZIP/manifest/SHA-256 checksums before allowing restore.
- Added minimum passphrase length validation and tests for round-trip, wrong password, and tampering.
- Added `cryptography>=42.0.0` dependency.
- Limits: user must retain the passphrase independently; loss is unrecoverable. Encryption runs in the Streamlit server process before download. Gist restore remains non-atomic.
- Local validation: Python compilation passed; 87 tests passed; ZIP integrity checked. No live Gist recovery drill, Streamlit browser test, GitHub Actions test, repository push, or deployment was performed.

## Updated next priorities
1. Run a real recovery drill against a disposable Gist with explicit user-authorized credentials, then verify restored application loading and file hashes.
2. Evaluate a transactional backend for truly atomic budget reservations and durable cross-workflow leases.
3. Add provider-native adapters and capability metadata, then resumable chunking with provenance and per-chunk cost accounting.
4. Configure authorized GitHub source-code commit/push and verify Actions and Streamlit Cloud deployment end-to-end.

## Phase 8.18 — Source Intelligence Expansion & Paid-Article Radar
- Expanded the main source catalogs to 263 unique domains, including official US/UK/Israeli sources, defense publications, European and Asian media, African sources, and international institutions.
- Expanded the intelligence office registry to 119 sources/organizations.
- Added a separate paid/limited-access radar for 33 publishers/services, including Tactical Report, major US and Israeli outlets, UK subscription publications, and selected international publishers.
- Tactical Report discovery uses its public reports and newsletters indexes plus Google News RSS. Only public titles/metadata are collected from the publisher index; locked report text is not fetched.
- Added a 64-domain open-coverage allowlist. The radar searches for related coverage through Google News RSS and GDELT, displays Arabic headlines and match heuristics, and can directly read/translate an alternative article only when its text is publicly served.
- Added direct publisher, reprint/syndication, public summary/newsletter, Google News, and legal subscription search routes.
- Added a paywall guard to prevent known subscription domains from being sent to proxy/archive article fallbacks.
- Removed the dedicated backup UI/workflow/modules/tests and cryptography dependency per the user's explicit priority change. Historical Phase 8.14–8.17 entries above describe previous releases only; backup work is no longer an active roadmap item. Gist data persistence remains unchanged.
- Validation: Python compilation passed; 87 unit tests passed. The full 263-domain registry was not live-probed; Streamlit, real feeds, GitHub Actions, Gist, push, and deployment were not tested.

## Current active roadmap (supersedes older "next priorities" lists)
1. Improve source-health diagnostics: identify dead domains, broken RSS, indexing gaps, language mismatches, and last successful retrieval per source.
2. Improve paid-radar matching: query variants, exact/near-duplicate detection, source-country diversity, and clearer distinction between same-story reporting and independent analysis.
3. Add public-source evidence extraction with source/date/link provenance, then translate and summarize open material without conflating it with the paywalled original.
4. Add an operator review queue for headline clusters, source credibility notes, conflicting accounts, and saved research leads.
5. Connect authorized GitHub source-code commit/push and verify Streamlit Cloud deployment only when repository access is available and explicitly authorized.

No further backup development is planned unless the user explicitly asks to revisit it.

## Current direction — Phase 8.19 (2026-11-23)
The user explicitly deprioritized and requested removal of the backup/restore work. Phase 8.18 removed backup modules, backup workflows, backup tests, and the encryption dependency. Do not reintroduce backup features unless explicitly requested. Gist remains only as the app's existing operational data store.

### Phase 8.19 — Source Health & Intelligence Clustering
- Added a combined source health catalog from the press registries, intelligence-office registry, and paid-radar watchlist: 299 unique domains at this release.
- Added concurrent HTTPS homepage checks, public RSS/Atom autodiscovery, common feed-path checks, HTTP/latency status, latest discovered feed title/date, and cautious failure states (blocked/unreachable is not labelled as a dead source).
- Added comparison against the previous saved scan to detect feed URL changes, disappeared feeds, recovered sites, newly observed feed items, and temporary unreachability.
- Added cross-perspective event discovery through GDELT and domain-scoped Google News RSS for US, Israeli, UK, and Arabic/regional sources.
- Added heuristic title/date clustering, perspective-separated headline comparison, tentative wire/syndication/origin assessments, and Arabic headline translation.
- Added unified case dossier JSON export and optional persistence in Gist using stable record IDs.
- Added GitHub release ZIP sync using Git Database API (blobs/tree/commit/ref update), no force push and no deletion. The Operations tab previews files and can automatically commit after upload when `GH_SYNC_AUTO=true`.
- Added GitHub Actions CI on push/PR to main for Python compilation and the unit test suite.

### Phase 8.19 validation and boundaries
- `python -m py_compile *.py tests/*.py`: passed.
- `python -m unittest discover -s tests -q`: 102 tests passed.
- ZIP integrity and release payload checks: see Phase 8.19 release notes.
- No live scan of all 299 domains was run; health probes are implemented but require runtime network execution.
- No Streamlit browser test was run because Streamlit is not installed in the build environment.
- No GitHub token/connector was available in this build session; no real commit, push, Actions run, or Streamlit deployment is claimed.
- GitHub sync requires one-time `GH_SYNC_TOKEN`, `GH_REPO`, `GH_BRANCH`, and optionally `GH_SYNC_AUTO=true` in Streamlit Secrets. This makes the in-app release ZIP sync automatic after upload, but does not create a direct ChatGPT-to-GitHub connection for code authored in this chat.

### Next priorities
1. Run a real source-health scan on a selected batch, then tune false positives/blocked-source handling using observed results.
2. Improve clustering with entity extraction, event-date normalization, and source citation graph while keeping the current heuristic caveats visible.
3. Complete authorized GitHub integration and verify one real commit, CI run, and Streamlit auto-deploy end-to-end.
4. Do not spend further development time on backups unless the user changes this priority.

## Phase 8.20 additions — entity intelligence
- Curated entity extraction covers selected people, countries, organizations, military vessels, and bases, with provenance at each article mention.
- Saved news dossiers can be enriched with an entity index, a publication-time timeline, contradiction candidates, and advisory matches to prior research cases.
- Contradiction candidates require overlapping claim text and opposite polarity markers, retain both source links, and remain explicitly unverified until human review.
- The timeline is a publication timeline. Event occurrence time must be separately sourced and recorded before it can be asserted.
- Entity extraction is a bounded alias dictionary, not comprehensive NER; ambiguous aliases and incomplete coverage remain known limitations.
- Phase 8.20 does not make paid AI calls, perform a live crawl, or push to GitHub.

## Phase 8.21 additions — cumulative intelligence case file
- Every research case can now have a cumulative record, created and updated only when the researcher presses the update button.
- Snapshots are fingerprinted; identical content does not create duplicate snapshots.
- Evidence ledger versions materials, claims, and events and records additions, field changes, evidence-status changes, removals from the current case, and restorations.
- The history stores before/after payloads and source links. It is an in-app history, not an immutable external audit log or backup.
- Saved Phase 8.20 dossiers are referenced only when their prior-case match explicitly names the exact case ID.
- The cumulative update prompt is manual and copyable; no provider request or spend occurs.
- Build validation: 116 unit tests passed after Phase 8.21; Python compilation passed. Streamlit browser/Gist live tests and GitHub push/deployment remain unverified.
