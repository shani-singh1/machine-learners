# API Reference

API module: `src/api/app.py`

Run:

```bash
python scripts/run_api.py
```

Default base URL: `http://127.0.0.1:8000`

## Endpoints

### `GET /vulnerability/latest`

Returns latest-month tile-level vulnerability rows.

Query:

- `limit` (optional): max rows

### `GET /vulnerability/by_zone`

Aggregates vulnerability by zone bins.

Query:

- `year_month` (optional)
- `bins_lat` and `bins_lon` (optional)

### `GET /vulnerability/timeseries`

Returns city average vulnerability trend per month.

### `GET /metadata`

Returns dataset coverage, available months, source list, and optional training/evaluation metadata.

## API design rule

API is read-only over `data/results/`.  
No model training/inference computation should run inside API request handling.
