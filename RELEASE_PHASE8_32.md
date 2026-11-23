# Phase 8.32 — Early Warning & Change Monitoring

## Scope
Builds on the complete Phase 8.31 project. Extends the existing early-warning center rather than duplicating it.

## Changes
- Baselines now retain fingerprints and prior values for case materials, claims, and timeline events.
- Detects newly added materials and entities, edits to previously saved materials, changes to claim text/status/source/notes, and changes to event dates/details/sources.
- Flags possible actor-position changes only when a material explicitly identifies a speaker/actor and stores a position/stance. These are review flags, not proof of an official policy shift.
- Adds cautious triage labels: متابعة, مراجعة مهمة, مراجعة عاجلة. Urgent language only raises review priority and never confirms an attack or other event.
- Daily brief and analysis prompt now include before/after records, source checks, alternative explanations, confidence, and explicit limits.
- Manual material entry now supports speaker/actor and attributed position fields to enable traceable comparison.
- Existing persisted baselines remain readable; older baselines without the new detail fields are handled safely.

## Tests
- 188 tests passed.
- Python compileall passed.
- ZIP integrity checked after packaging.
- One pre-existing warning is emitted by a test that intentionally creates a duplicate ZIP path to verify rejection.

## Not tested
- Streamlit runtime/UI: Streamlit is not installed in the build environment.
- Live collection, external websites, GitHub/Gist sync, and deployment.
- The system does not autonomously verify contradictions or infer political intent. It surfaces changed records and review candidates.

## Cost and data
- No AI API calls are made by the new monitoring logic.
- No API keys are added to the archive.
