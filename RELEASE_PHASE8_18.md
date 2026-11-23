# Phase 8.18 — Source Intelligence Expansion & Paid-Article Radar

## Delivered

- Audited the existing source registries and expanded coverage across Israeli, US, UK, European, Chinese, Japanese, Korean, Russian, African, UN, and specialist defense/intelligence sources.
- Added official government/intelligence sources and explicitly described their outputs as official party statements rather than independent verification.
- Added `paid_radar.py` with a 33-publisher watchlist, public Tactical Report reports/newsletters index discovery, Google News RSS and GDELT headline discovery, Arabic headline translation, and legal access/search links.
- Added open-coverage discovery across a 64-domain allowlist. Results are labelled as likely related coverage, with an approximate headline similarity score.
- Added direct-only article reading and Arabic translation for open alternative pages. The original paid publisher is never fetched for full text by this feature.
- Added a manual headline search for titles copied from newsletters or subscription portals.
- Expanded the known paywall-domain guard so the existing article fallback will not use proxy/archive services on known paid domains.
- Removed the dedicated backup UI, backup workflow, backup modules, backup tests, and the now-unneeded `cryptography` dependency at the user's request. Gist remains as the app's existing data-persistence mechanism; it is not a new backup project.
- Updated the app's help text and source catalog audit.

## Source counts

- 263 unique domains across the main press/source groups.
- 119 entries in the intelligence office registry.
- 33 publishers/services in the paid or limited-access watchlist.
- 64 domains in the open-coverage discovery allowlist.

See `SOURCE_CATALOG_AUDIT.md` for the detailed inventory and limitations.

## Validation

- `python -m py_compile *.py tests/*.py`: passed.
- `python -m unittest discover -s tests -q`: **87 tests passed**.
- Static source-registry checks: passed (supported language codes, valid domain-only entries, key official sources present).
- Paywall guard test: passed; known paid domains do not invoke proxy/archive fallback.
- Paid-radar tests: passed for allowlist filtering, paywall exclusion, Tactical Report public index parsing, direct-only open article reading, and legal search links.
- No live scan of all source websites, no real paid publisher login, no Streamlit browser run, no live Gist test, no GitHub Actions execution, no GitHub push, and no deployment were performed.

## Important limitations

- Similarity scores are heuristic and cannot prove syndication or article identity.
- Headline availability depends on Google News RSS indexing and public publisher pages.
- Tactical Report public index items may not expose a date; missing dates are not inferred.
- Full article translation is only for directly accessible open alternative pages. Paid originals are represented by public headlines/metadata and links.
- The new feature is not a subscription entitlement or paywall-unlocking mechanism.
