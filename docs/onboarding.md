# Developer Onboarding

## 1) Prerequisites

- Python 3.11+ (project currently runs on 3.14 in this workspace)
- Git + Git LFS
- Internet access for public data sources

## 2) Clone and setup

```bash
git clone <repo-url>
cd machine_learners
python -m pip install -r requirements.txt
```

## 3) Environment

Create `.env` with required keys:

- `CDS_API_KEY`
- `CDSE_CLIENT_ID`
- `CDSE_CLIENT_SECRET`
- `GEE_PROJECT_ID`

## 4) Understand workflow

- Read `build.md` for product intent
- Read docs in this order:
  1. `architecture.md`
  2. `data-ingestion.md`
  3. `modeling.md`
  4. `api.md`
  5. `ui.md`

## 5) First successful run

Execute:

```bash
python scripts/run_ingestion.py --config config/bengaluru_2020_2024.json
python scripts/run_preprocessing.py --config config/bengaluru_2020_2024.json
python scripts/run_feature_build.py --city bengaluru
python scripts/run_training.py
python scripts/run_inference.py
python scripts/run_evaluation.py
```

Then start services:

```bash
python scripts/run_api.py
python scripts/run_frontend.py
```

## 6) Contribution guidance

- Keep module boundaries clean (ingestion vs processing vs serving).
- Avoid leakage in model experiments.
- Keep API read-only over `data/results/`.
- For large files, rely on Git LFS.
