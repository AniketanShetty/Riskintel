# RiskIntel ML Dataset Forensics

This directory contains the production-grade implementation scripts for the top 3 Priority Dataset Forensics Checks.

## Directory Structure
* `scripts/`: Contains the executable Python modules.
* `tests/`: Contains the Pytest suite verifying statistical logic.
* `metrics/`: Auto-generated directory for JSON and CSV outputs.
* `plots/`: Auto-generated directory for PNG outputs.

## Setup
Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage Examples

All scripts must be executed from within the `experiments/` directory or root, specifying the path to the processed eligibility dataset.

### 1. Target Leakage Detection
```bash
python scripts/f1_target_leakage.py \
    --input ../data/processed/eligibility_data.csv \
    --target loan_status \
    --outdir .
```

### 2. Train/Test Contamination
```bash
python scripts/f2_contamination.py \
    --input ../data/processed/eligibility_data.csv \
    --target loan_status \
    --outdir .
```

### 3. Duplicate Row Detection
```bash
python scripts/f3_duplicates.py \
    --input ../data/processed/eligibility_data.csv \
    --outdir .
```

## Running Tests
To verify the math and logic, execute pytest from the experiments directory:
```bash
pytest tests/
```
