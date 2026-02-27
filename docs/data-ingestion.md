# Data Ingestion

## Scope

Ingestion runs monthly for Bengaluru (`2020-01` to `2024-12`) and stores artifacts by source:

`data/raw/<source>/<year>/<month>/`

## Sources currently wired

- Sentinel-1 (monthly preprocessed composite)
- Sentinel-2 (monthly preprocessed composite)
- ERA5-equivalent rainfall
- DEM
- GHSL built-up
- WorldPop reference payload
- OSM roads

## Key files per source/month

- `manifest.json`: status, metadata, and ingestion payload summary
- source-specific artifact files (for example `.tif`, `.json`, `.zip`)

## Reliability behavior

- Timestamped logs for each source/month
- Skip already downloaded months
- Retry behavior for CDSE auth/process calls
- Error status written to manifest when source fails

## Verify completion

Expected completed months per source for this phase: **60**.

Example verification command:

```bash
python -c "from pathlib import Path; import json; root=Path('data/raw'); s='sentinel_1'; print(sum((root/s/str(y)/f'{m:02d}'/'manifest.json').exists() for y in range(2020,2025) for m in range(1,13)))"
```

## Important note

Ingestion is intentionally batch-oriented and can be long-running for satellite-heavy steps. Always inspect source-wise logs before re-running whole pipeline.
