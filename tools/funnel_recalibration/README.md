Funnel Recalibration Tools
==========================

Purpose
-------
These scripts inspect and recalibrate raw Recruiting Funnel workbook exports (for example `Recruiting Funnel Enriched.xlsx`) into a set of deterministic, auditable CSV artifacts that can later be integrated into TAAIP.

Artifacts produced (written to `artifacts/funnel_recalibrated/`):
- `person_snapshot.csv` — one row per original person/row with normalized person-level fields.
- `funnel_events_long.csv` — long-format event rows expanded from timeline/array columns.
- `funnel_summary.csv` — per-person derived summary (first/last seen, first stage timestamps, event counts, deltas).
- `data_quality_report.json` — structural and quality diagnostics.

Scripts
-------
- `inspect_funnel_workbook.py <xlsx>` — quick structural report (sheets, header row index, duplicate/unnamed columns, timeline column candidates). Writes `structural_report.json`.
- `recalibrate_funnel_workbook.py <xlsx>` — main recalibration pipeline producing the artifacts above.
- `mapping_config.py` — conservative mapping rules and stage mapping used by the recalibration step. Edit carefully; mapping decisions must be explicit and logged.

How to run
----------
Ensure Python dependencies are available (pandas).

Example:
```
python tools/funnel_recalibration/inspect_funnel_workbook.py \
  "/path/to/Recruiting Funnel Enriched.xlsx"

python tools/funnel_recalibration/recalibrate_funnel_workbook.py \
  "/path/to/Recruiting Funnel Enriched.xlsx"
```

Notes and constraints
---------------------
- The original workbook is preserved; these scripts read and emit separate artifacts.
- Any mapping that is not 1:1 or provable is recorded in `data_quality_report.json` under `inferred_mappings` and must be reviewed before integration.
- Rows with broken timeline alignment are preserved but flagged in the quality report — no silent dropping.

Next steps (after review)
-------------------------
Once mappings and stage semantics are confirmed, the canonical mapping can be promoted and an ingestion adapter added to TAAIP (separate change).
