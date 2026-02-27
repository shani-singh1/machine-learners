# Bengaluru Flood Vulnerability Platform

## What this platform does

This project estimates **where flood vulnerability is likely to be higher** across Bengaluru, month by month, using publicly available satellite and environmental data.

It is designed for:

- planning teams that need a city-wide risk view
- response teams that need hotspot prioritization
- engineers/data scientists who need a reproducible pipeline

## Business value

- Identifies high-priority risk zones in a consistent way
- Tracks seasonal and month-to-month risk changes
- Provides decision-ready outputs through API and dashboard
- Uses public data so it is reproducible and scalable

## What it does NOT do

- No real-time flood alerting
- No hydraulic simulation or flood depth modeling
- No drainage pipe network simulation

## End-to-end flow

1. Ingest monthly source data (`data/raw/`)
2. Build flood stress signals (`data/processed/`)
3. Build model-ready dataset (`data/features/`)
4. Train temporal model (`data/results/models/`)
5. Generate vulnerability scores (`data/results/vulnerability_scores.parquet`)
6. Evaluate signal quality (`data/results/evaluation.json`)
7. Serve via API + UI (`src/api`, `src/frontend`)

## Start here

- New developer? Read `onboarding.md`
- Running system? Read `operations.md`
- Debugging issue? Read `troubleshooting.md`
