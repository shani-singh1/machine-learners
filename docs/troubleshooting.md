# Troubleshooting

## README preview fails on GitHub

- Ensure `README.md` is plain UTF-8 markdown text.
- Replace corrupted/binary markdown files.

## Ingestion stalls or seems slow

- Satellite monthly composites can be slow due to remote processing.
- Check timestamped ingestion logs for month-level progress.
- Re-run ingestion: completed months are skipped.

## Push fails with large repo payload

- Use Git LFS for heavy artifacts (`.tif`, `.zip`, `.joblib`, raw data).
- If push stalls, retry with verbose mode:
  - `git push --verbose origin main`

## API not starting on port 8000

- Another process is using the port.
- Find and stop existing process, then restart API.

## UI cannot fetch data

- Verify API is running.
- Validate `FLOOD_API_BASE` points to API host.

## Missing result files

- Run training/inference/evaluation scripts in order.
- Confirm outputs exist in `data/results/`.
