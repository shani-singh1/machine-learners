# Training and Evaluation

## Production training strategy

Current training is built to reduce leakage and reflect real deployment:

- predicts **next-month** vulnerability target
- uses **chronological split** (train/val/test by time)
- performs temporal model selection via validation set

## Outputs

- `data/results/models/baseline_model.joblib`
- `data/results/models/temporal_model.joblib`
- `data/results/training_metrics.json`
- `data/results/feature_importance.json`

## Current model logic

- Baseline: ridge regression
- Temporal candidates: tree-based temporal regressors
- Best model selected by validation MAE

## Run

```bash
python scripts/run_training.py
```

## Evaluation metrics

- MAE (lower is better)
- R2 (higher is better)
- rank correlation in evaluation stage (`evaluation.json`)

## Interpretation guidance

- Compare temporal vs baseline on held-out test period
- Use feature importance to validate signal dominance
- Track metric drift between retrains
