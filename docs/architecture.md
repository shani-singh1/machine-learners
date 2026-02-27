# Architecture

## Design principle

The system predicts **relative vulnerability accumulation**, not flood depth.

## High-level modules

- **Ingestion (`src/ingestion`)**  
  Pulls raw source files and writes source/month manifests.
- **Preprocessing (`src/preprocessing`)**  
  Converts raw observations into aligned flood stress signals.
- **Features (`src/features`)**  
  Builds model-ready tabular dataset.
- **Modeling (`src/models`, `src/training`)**  
  Trains baseline and temporal models using chronological split.
- **Inference (`src/inference`)**  
  Produces normalized vulnerability scores.
- **Evaluation (`src/evaluation`)**  
  Computes trend/impact consistency metrics.
- **Serving (`src/api`, `src/frontend`)**  
  Exposes data for decision use.

## Data zones

- `data/raw/`: source-specific monthly artifacts
- `data/processed/`: monthly city-level processed features
- `data/features/`: unified training dataset
- `data/results/`: model artifacts and outputs

## Execution order

1. `run_ingestion.py`
2. `run_preprocessing.py`
3. `run_feature_build.py`
4. `run_training.py`
5. `run_inference.py`
6. `run_evaluation.py`
7. `run_api.py` + `run_frontend.py`

## Deployment model

- Single-server deployment
- Batch execution (cron-friendly)
- Local volumes for data persistence
- API + Streamlit UI exposed via reverse proxy (if needed)
