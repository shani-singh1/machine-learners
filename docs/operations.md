# Operations Runbook

## Environment

Required `.env` keys:

- `CDS_API_KEY`
- `CDSE_CLIENT_ID`
- `CDSE_CLIENT_SECRET`
- `GEE_PROJECT_ID`

## Full pipeline run

```bash
python scripts/run_ingestion.py --config config/bengaluru_2020_2024.json
python scripts/run_preprocessing.py --config config/bengaluru_2020_2024.json
python scripts/run_feature_build.py --city bengaluru
python scripts/run_training.py
python scripts/run_inference.py
python scripts/run_evaluation.py
```

## Serving run

```bash
python scripts/run_api.py
python scripts/run_frontend.py
```

## Suggested batch schedule

- Ingestion: monthly or on data refresh event
- Full training/inference: monthly after ingestion
- API/UI: continuous service

## Storage and sync

- Large artifacts are tracked using Git LFS.
- Ensure Git LFS is installed on all contributor machines.
