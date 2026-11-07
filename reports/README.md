# Current research evidence

- `longitudinal_v2_1/results.json`: current model selection, held-out metrics,
  calibration and timing sensitivity.
- `longitudinal_v2_1/summary.json`: aggregate cohort counts and source audit.
- `longitudinal_v2_1/manifest.json`: immutable current source/model/result hashes.
- `longitudinal_v2_1/verification.json`: latest cohort verification result.
- `runtime_handoff_validation.json`: current-model delivery validation.
- `cleanup.json`: user-authorized removal record and preservation checks.
- `restoration.json`: useful tracked research code/docs/tests recovered from
  Git after cleanup, with original-byte hashes and validation scope.
- `feature_mapping_evidence.json`, `prediction_source_evidence.json`: source
  documentation supporting field meanings and harmonization.

Reports contain aggregate results and metadata only. Earlier next-survey
reports are restored as historical comparison/audit evidence, not current-model
results. The invalid initial longitudinal diagnostic remains removed. See
`docs/RESEARCH_GUIDE.md` and `docs/faculty_guide.md`. Participant histories stay
in ignored `data/`; the one included model contains the documented small
survey-derived explanation reference for authorized recipients.
