# Decision Dashboard UI

Frontend module: `src/frontend/app.py`

Run:

```bash
python scripts/run_frontend.py
```

Optional env:

- `FLOOD_API_BASE` to point UI to API host

## UX goals

Dashboard is intentionally non-technical and decision-oriented.

## Core sections

- **City Snapshot**
  - current risk level
  - latest average score
  - hotspot coverage
- **Risk Map**
  - latest-month spatial view
- **Top Priority Zones**
  - plain-language priority labels
- **Seasonal Trend**
  - month-to-month city risk trend
- **Recommended actions**
  - operational guidance for planning/response teams

## Intended audience

- city operations
- disaster response planners
- ward-level planning teams
- policy stakeholders
