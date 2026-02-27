# Inference and Scoring

## Purpose

Transform trained model outputs into normalized vulnerability scores for decision workflows.

## Output artifact

- `data/results/vulnerability_scores.parquet`

Contains:

- `tile_id`, `year`, `month`, `year_month`
- location (`lat`, `lon`)
- `vulnerability_score` (0 to 1 normalized)
- `vulnerability_rank`

## Run

```bash
python scripts/run_inference.py
python scripts/run_evaluation.py
```

## Evaluation output

- `data/results/evaluation.json`

Includes:

- rank correlation proxy
- high-vs-low gap
- months evaluated

## Usage

- API reads this data directly
- dashboard consumes API output for risk communication
