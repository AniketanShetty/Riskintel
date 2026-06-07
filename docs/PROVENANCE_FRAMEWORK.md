# RiskIntel Provenance Framework

**Date:** 2026-06-07
**Status:** Binding Data Governance Policy

This framework enforces strict data provenance tracking. The Model Risk Committee mandates that no dataset, raw or processed, may exist in this repository without explicit provenance documentation.

## 1. The `provenance.json` Requirement

Every data file in the repository MUST have an accompanying `provenance.json` file located in the same directory, named `{filename}_provenance.json`.

**Required Fields:**
- `dataset_name`: The exact filename.
- `source_url`: Where the data came from.
- `license`: The explicit legal license governing the data.
- `license_url`: Link to the license text.
- `geographic_population`: e.g., "India", "Global", "Synthetic".
- `row_count`: Exact integer row count.
- `column_count`: Exact integer column count.
- `sha256`: Cryptographic hash of the file.
- `download_date`: ISO 8601 date.
- `build_script`: The exact relative path to the Python script that generated the file (if processed).
- `build_operator`: The name/email of the engineer who generated it.

## 2. The `data/lineage.json` Requirement

A master `data/lineage.json` must be maintained at the root of the data directory. It defines the exact directed acyclic graph (DAG) of how raw data turns into processed data, and how processed data turns into model artifacts.

Example structure:
```json
{
  "eligibility_data.csv": {
    "parents": ["loan_approval_dataset.csv"],
    "script": "scripts/process_eligibility.py",
    "children": ["random_forest.joblib"]
  }
}
```

## 3. Enforcement

If a dataset is found in the repository without a complete `provenance.json` or an entry in `LICENSE_INVENTORY.md`, it will be treated as an **Unauthorized Artifact** and deleted without warning by the CI/CD pipeline.
