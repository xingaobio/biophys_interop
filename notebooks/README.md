# Quickstart notebook

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/xingaobio/biophys_interop/blob/master/notebooks/biophys_interop_quickstart.ipynb)

Choose **Runtime → Run all** in a fresh Python runtime. No GPU is required. The first cell resolves public master
once, installs that exact commit with the batch dependencies, and prints the commit and Python version.
The notebook checks SPR and ITC examples, then processes the real 200-row ChEMBL demonstration CSV.
The demo is fetched from the same commit and checked against its SHA-256; download or installation errors stop execution.

Outputs appear in `out/`: `canonical.parquet`, `qc_report.json`, `manifest.json`, and `quickstart_runtime.json`.
Keep them together to retain the input hash, source commit and runtime package versions. Re-running overwrites these
demonstration outputs. An existing `demo_input.csv` must match the bundled demo; rename other data before running.

For Jupyter, open the notebook and run all cells. To verify a source checkout without a notebook server:

```bash
python -m pip install ".[batch]"
python tools/verify_quickstart.py --local-checkout
```

The runner executes every code cell and checks actual Parquet rows, QC outcomes and manifest hashes. CI uses the
checkout's package and demo; a normal Colab run installs the resolved public commit. `--output` saves a per-cell JSON
log; `--write-notebook` refreshes notebook outputs from that execution.

This is a basic toolkit demonstration. To reconstruct cached manuscript statistics, use the separate
[public-limited companion](https://doi.org/10.5281/zenodo.23097835) and its offline checker. Hosted MAPK14 materials
are excluded. Default heuristic uncertainty is an estimate, not a calibrated error or confidence interval.
