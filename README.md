# Urban Flood Vulnerability Forecasting - Bengaluru (2020-2024)

Production-oriented flood vulnerability forecasting system using public earth observation and environmental signals.

This repository implements the workflow defined as:

- data ingestion (multi-source, monthly)
- preprocessing + feature construction
- temporal vulnerability modeling
- scoring + evaluation
- API + decision-maker UI

## Project at a glance

- **City:** Bengaluru
- **Period:** 2020-01 to 2024-12
- **Core output:** relative vulnerability scores (not flood depth)
- **Main results:**
  - `data/results/vulnerability_scores.parquet`
  - `data/results/evaluation.json`
  - `data/results/training_metrics.json`

## Repository structure

- `config/` runtime configs
- `src/ingestion/` source adapters and ingestion pipeline
- `src/preprocessing/` flood stress signal generation
- `src/features/` model dataset builder
- `src/models/` temporal model training logic
- `src/training/` model training pipeline
- `src/inference/` score generation
- `src/evaluation/` evaluation pipeline
- `src/api/` FastAPI endpoints
- `src/frontend/` Streamlit dashboard
- `scripts/` runnable entrypoints
- `data/` raw, processed, features, and results artifacts

## Quick start

1. Install dependencies:
  - `python -m pip install -r requirements.txt`
2. Ensure `.env` contains:
  - `CDS_API_KEY`
  - `CDSE_CLIENT_ID`
  - `CDSE_CLIENT_SECRET`
  - `GEE_PROJECT_ID`
3. Run ingestion:
  - `python scripts/run_ingestion.py --config config/bengaluru_2020_2024.json`
4. Run training workflow:
  - `python scripts/run_preprocessing.py --config config/bengaluru_2020_2024.json`
  - `python scripts/run_feature_build.py --city bengaluru`
  - `python scripts/run_training.py`
  - `python scripts/run_inference.py`
  - `python scripts/run_evaluation.py`

## Run services

- API server:
  - `python scripts/run_api.py`
- UI dashboard:
  - `python scripts/run_frontend.py`

## API endpoints

- `GET /vulnerability/latest`
- `GET /vulnerability/by_zone`
- `GET /vulnerability/timeseries`
- `GET /metadata`

## Full documentation

Comprehensive developer docs are available in `docs/` with MkDocs configuration in `mkdocs.yml`.

To run docs locally:

1. Install docs dependencies:
  - `python -m pip install mkdocs mkdocs-material`
2. Start docs server:
  - `mkdocs serve`

