# Phase 8.35 — Entity Relationship & Influence Network

## Added
- Added `relationship_network.py` to build a conservative, evidence-linked entity co-mention network from collected dossier articles.
- Nodes include entity type, mention count, article count, source domains, and matching research-case IDs.
- Edges are explicitly labeled `co_mentioned` and include supporting article IDs, source domains, publication dates, URLs, and a caveat.
- Duplicate article URLs are counted once per entity pair.
- Added a configurable minimum co-mention threshold and a bounded edge count.
- Added a Graphviz network view in the existing entity intelligence panel, with evidence drill-down and JSON/prompt exports.
- Added a review prompt that explicitly forbids treating co-mentions as proof of contact, alliance, financing, command, or causation.

## Methodological safeguards
- This is not a verified social or operational relationship graph. A connection means only that two curated entities appeared in the same collected article.
- Entity extraction remains based on the existing curated alias dictionary and is not comprehensive NER.
- Source counts describe the collected sample, not total media coverage.
- No automatic political, financial, military, or personal relationship is asserted.

## Validation
- `python -m compileall -q .` passed.
- `PYTHONPATH=. pytest -q`: 199 passed, 1 expected warning from the existing duplicate-ZIP-path security test.
- ZIP integrity and required module presence checked during packaging.
- Streamlit live UI, Graphviz rendering in Streamlit Cloud, live sources, Gist, GitHub push, and deployment were not tested.
