# Marsad News — Phase 8.20 Release

## Scope
Entity Intelligence, Publication Timelines, Contradiction Candidates, and Prior-Case Linking.

## What changed
- `entity_intelligence.py` adds a curated alias dictionary for selected people, countries, organizations, military vessels, and military bases. It supplements the existing entity vocabulary in `case_links.py`; it is not a general-purpose named-entity recognition model.
- Entity mentions retain provenance: original title, source name, domain, URL, publication date, and matched alias.
- A publication timeline orders dated source materials and explicitly distinguishes publication time from event-occurrence time.
- Contradiction detection surfaces candidate pairs only when claim text overlaps and polarity markers differ. Candidates include both source links and a mandatory human-review caveat.
- New articles can be matched against saved research cases using the existing explainable similarity engine. A match is not evidence of causation or coordination.
- The Streamlit intelligence area adds `🧭 الكيانات والتناقضات` to inspect saved dossiers, enrich them, and export the result as JSON.

## Methodological limits
- The entity catalog is curated and incomplete; aliases can be ambiguous and require review.
- Publication timestamps do not establish when an event happened.
- Contradiction candidates can reflect negation, timing, definitions, translation, or quoted speech. They do not determine which claim is true.
- Case links are topical similarity suggestions, not proof of a direct relationship.
- Full text is used only when already present in the collected article record. Headlines alone are not silently promoted to verified claims.

## Cost and operations
- No paid model/API call is made by this phase.
- No automatic paid operation or external write is initiated.
- Existing human approval and cost-preview requirements remain in force.
- No backup/restore features are included.
- GitHub sync code remains prepared through the existing Phase 8.19 release panel. No actual GitHub commit, push, or Streamlit deployment is claimed by this release.

## Validation
- Python compilation: passed (`python -m py_compile *.py tests/*.py`).
- Unit tests: 108 passed (`python -m unittest discover -s tests -q`).
- Live Streamlit UI, live source crawl, Gist persistence, GitHub push, and hosted deployment: not exercised in this build environment.
