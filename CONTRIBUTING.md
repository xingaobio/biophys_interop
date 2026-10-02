# Contributing

Issues and pull requests are welcome. Include the input, expected behavior and actual QC reasons when reporting a
problem; remove private identifiers and credentials before sharing a record.

## Development setup

```bash
python -m pip install -e ".[batch,test]"
python src/biophys_interop/tests/test_pipeline.py
python tools/verify_quickstart.py --local-checkout
```

The notebook runner requires a Git checkout and exercises every code cell, including batch output verification.

## Adding or changing a QC rule

Rules live in `src/biophys_interop/qc.py`. Each declares a unique `code`, applicable `modalities`, `severity`,
literature or curation `basis`, and recommended `action`. Explain the evidence supporting the check and its limits.
Update the rule cards in `docs/rule_cards.md`, `docs/rule_cards.json` and `docs/rule_cards.csv` together, and cover the
behavior with an appropriate example or test. Keep registry counts consistent with `RULE_COUNT`.

## Evidence scope

The 72 public rules are a transparent registry. ChEMBL annotation-proxy benchmark operations R1/R5b do not establish
rule-level accuracy against independently source-verified errors. R1 is a post-hoc restricted range analysis;
R5b is a dataset operation outside the per-record registry. Do not label a public rule empirically validated on the
strength of those comparisons. Default heuristic uncertainty is an estimate, not calibrated error.

Keep changes focused and include relevant verification. Changes to scientific claims or reported numbers must cite
corresponding source evidence and reproducibility artifacts. Preserve archived releases and published deposits.
