# TAAIP Real-Data Proof and Targeting Repair Notes

Date: 2026-04-12
Scope: Completion/validation pass after ingest operationalization fixes.

Artifacts:
- After proof payloads: services/api/targeting_repair_proof_after.clean.json
- Before snapshot source: live capture run immediately before repair (STN 1A1D baseline)

## 1) Live Payload Proof (Before -> After)

### A. Market engine / market_qma

Before (STN 1A1D):
- market_engine status: no_active_dataset
- market_engine source_dataset_name: 6L MARKET CORE.csv
- market_engine rows_used: 0
- market_engine output type: default/empty for this STN scope
- market_qma status: ok
- market_qma source_dataset_name: station_zip_coverage
- market_qma rows_used: 2
- market_qma output type: real

Before sample (market_qma):
```json
{"zip_code":"37011","station_rsid":"1A1D","opportunity_gap":1.0,"qma_density":1.0,"output_score":0.0,"market_classification":"market_capable"}
```

After (USAREC):
- market_engine status: ok
- market_engine source_dataset_name: 6L MARKET CORE.csv
- market_engine rows_used: 10
- market_engine output type: real
- market_qma status: ok
- market_qma source_dataset_name: station_zip_coverage
- market_qma rows_used: 2
- market_qma output type: real

After sample (market_engine):
```json
{"zip":"98105","station_rsid":"6L2C","market_capability_score":82.22,"opportunity_band":"strong","trace_id":"market-engine:6L2C:98105"}
```

### B. School access

Before (STN 1A1D):
- status: ok
- source_dataset_name: fact_school_contacts
- rows_used: 2
- output type: real

Before sample:
```json
{"school_name":"High School A","station_rsid":"1A1D","zip_code":"90001","contacts_count":5,"contracts_count":0,"access_classification":"underpenetrated"}
```

After (USAREC + STN):
- status: ok
- source_dataset_name: fact_school_contacts
- rows_used: 2
- output type: real

### C. Targeting expansion / market_targeting

Before (STN 1A1D):
- endpoint /api/v2/targeting/recommendations rows_used: 2
- output existed, but it was coverage-driven with weak market integration details
- example lacked school-access signal and had market_opportunity_band=unknown fallback

Before sample:
```json
{"zip_code":"37011","station_rsid":"1A1D","market_opportunity_band":"unknown","priority_score":61.33,"reason_codes":[]}
```

After (USAREC):
- endpoint status: 200
- rows_used: 48
- zip_rows_used: 20
- source_dataset_name: 6L MARKET CORE.csv
- output type: real prioritized rows from market engine + school-access evidence

After sample (required fields present):
```json
{
  "zip": "37011",
  "station_rsid": "1A1D",
  "market_capability_score": 100.0,
  "opportunity_band": "unknown",
  "school_access_signal": {"status":"constrained","penetration_rate":0.0,"access_gap_score":0.0,"contacts_count":0,"contracts_count":0},
  "rationale": "market unknown (100.0); school_access constrained",
  "priority_score": 61.33,
  "trace_id": "targeting:1A1D:37011"
}
```

After (STN 1A1D):
- endpoint status: 200
- rows_used: 2
- zip_rows_used: 2
- school_access_signal now attached and populated

### D. Mission adjustment justification

Before (STN 1A1D):
- endpoint status: 200
- recommended_action: hold
- targeting_count in payload: null
- market status in command narrative context: could remain unknown for this STN scope

After (USAREC):
- endpoint status: 200
- recommended_action: hold
- signal_summaries.market.status: ok
- signal_summaries.market.source_dataset_name: 6L MARKET CORE.csv
- signal_summaries.market.rows_used: 15
- signal_summaries.school_access.status: ok
- signal_summaries.school_access.source_dataset_name: fact_school_contacts
- signal_summaries.targeting.status: ok
- signal_summaries.targeting.rows_used: 38

After sample (mission signal_summaries):
```json
{
  "market": {"status":"ok","source_dataset_name":"6L MARKET CORE.csv","rows_used":15},
  "school_access": {"status":"ok","source_dataset_name":"fact_school_contacts","rows_used":2},
  "targeting": {"status":"ok","source_dataset_name":"6L MARKET CORE.csv","rows_used":38}
}
```

### E. Command center market/targeting portions

Before (STN 1A1D):
- phase2.market_engine.summary.overall_market_status: unknown
- phase2.targeting_focus top entries existed but no targeting source_dataset_name field

After (USAREC):
- phase2.market_engine.market_engine.summary.overall_market_status: weak (non-default)
- phase2.market_engine.market_engine.source_dataset_name: 6L MARKET CORE.csv
- phase2.targeting_focus.top_focus_count: 15
- phase2.targeting_focus.source_dataset_name: 6L MARKET CORE.csv

## 2) Targeting Repair Summary

Implemented:
- Targeting candidate set now unions:
  - market-engine prioritized ZIP rows
  - station_zip_coverage rows
- This removes the prior behavior where targeting depended mainly on station_zip_coverage and ignored real market-engine ZIPs.
- Added school-access integration per ZIP/station:
  - school_access_signal status
  - penetration_rate
  - access_gap_score
  - contacts_count/contracts_count
- Added required targeting output fields:
  - zip
  - station_rsid
  - market_capability_score
  - opportunity_band
  - school_access_signal
  - rationale
  - priority_score
  - trace_id
- Added source dataset metadata on targeting payload:
  - source_dataset_name
  - market_source_dataset_name

## 3) Mission Adjustment Integration Check

Implemented:
- Added mission output signal_summaries block with:
  - market status/source_dataset_name/rows_used
  - school_access status/source_dataset_name/rows_used
  - targeting status/source_dataset_name/rows_used

Result:
- When real market/school/targeting rows exist (USAREC), mission output references real evidence and row counts.
- STN scopes with no matching market-engine rows remain explicitly no_active_dataset, while targeting/school still report real rows when available.

## 4) Command Center Check

Implemented:
- Enhanced targeting_focus summary with:
  - zip_focus_count
  - source_dataset_name
  - trace_id in top ZIP excerpts

Result:
- Command center now surfaces market and targeting source dataset names in phase2 payload.

## 5) Tests Added/Updated

Updated/added coverage:
- services/api/tests/test_market_engine.py
  - targeting includes source_dataset_name
  - targeting rows include market+school+trace fields from engine-driven paths
- services/api/tests/test_mission_decrease_justification.py
  - mission adjustment emits populated signal_summaries for market/school/targeting with source dataset names
- services/api/tests/test_phase2_full.py
  - command center phase2 targeting includes source_dataset_name and zip_focus_count
  - command center phase2 includes market source dataset and targeting source dataset fields

Test run:
- pytest -q services/api/tests/test_market_engine.py services/api/tests/test_mission_decrease_justification.py services/api/tests/test_phase2_full.py -k 'targeting or mission_adjustment or command_center or overview_phase2'
- Result: 20 passed, 0 failed
