# Preprocessing and Feature Construction

## Preprocessing objective

Convert source artifacts into aligned flood stress variables per tile per month.

Output:

- `data/processed/bengaluru/YYYY_MM.parquet`

## Core processed signals

- `sar_water_persistence`
- `rainfall_accumulation`
- `low_lying_score`
- `impervious_change_rate`
- `population_exposure`

## Feature dataset objective

Build one model-ready table across all months and tiles.

Output:

- `data/features/flood_dataset.parquet`

Key columns:

- identifiers: `tile_id`, `year_month`, `time_window`
- geo: `lat`, `lon`
- stress features listed above
- target proxy used for supervised learning

## Run

```bash
python scripts/run_preprocessing.py --config config/bengaluru_2020_2024.json
python scripts/run_feature_build.py --city bengaluru
```

## Quality checks

- 60 monthly processed files present
- no empty feature dataset
- expected feature columns available
