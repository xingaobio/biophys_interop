# Contributing

Thanks for your interest in `biophys_interop`.

## Development setup
```bash
pip install -e ".[batch,test]"
python src/biophys_interop/tests/test_pipeline.py   # or: pytest
```

## Adding or changing a QC rule
- Rules live in `src/biophys_interop/qc.py`. Each rule declares its `code`, applicable `modalities`, `severity`
  (`fail`/`warn`), a literature `basis`, and the `action` it triggers.
- New rules must cite a literature basis and state the tier of evidence (validated vs literature-grounded registry).
- Regenerate the rule cards in `docs/` after any rule change.
- Add or update a worked example under `src/biophys_interop/examples/` and cover the rule in the smoke tests.

## Scope note
Only two general affinity rules (value-range, exact-value duplicate) are empirically validated. Method-specific
biophysical rules are a literature-grounded registry; keep that distinction explicit in code, docs, and PRs.

## Pull requests
Keep changes focused, include a test, and do not alter validated numbers or claims without a corresponding update to
the reproducibility artifacts.
