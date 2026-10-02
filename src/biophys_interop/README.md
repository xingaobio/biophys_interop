# biophys_interop package

A NumPy-based toolkit for standardizing biophysical measurements and applying deterministic, method-aware QC.
For installation, runnable examples, evidence scope and citations, see the repository's [main README](../../README.md).

## Interfaces

- `standardize(raw, modality)`: normalize supported units and fields into the canonical record schema.
- `qc(record, calibrator=None)`: attach flags, reasons and uncertainty. The default estimate is labelled
  `source="estimated", method="heuristic"`; an explicitly supplied fitted calibrator uses the calibrated branch.
- `featurize(record)`: return a 64-dimensional NumPy feature vector and a mask indicating available fields.
- `Adapter(backbone_dim, feature_dim=FEATURE_DIM)`: a reference conditioning interface with deterministically seeded,
  untrained weights. It checks input/output shapes; it does not predict affinity or protein structure.

The public schema supports 24 modalities and the QC registry contains 72 rules. Literature or curation bases and
recommended actions are recorded with each rule. These checks support review; their empirical error-detection
accuracy is not established by the manuscript's separate ChEMBL annotation-proxy benchmark operations.

## Run from a repository checkout

```bash
python -m biophys_interop.cli run src/biophys_interop/examples/spr.json
python -m biophys_interop.cli validate src/biophys_interop/examples/saxs.json
python src/biophys_interop/tests/test_pipeline.py
```

Five bundled records cover SPR, SAXS, DMS, DLS and FIDA. The root `examples/demo_input.csv` contains the 200-row
ChEMBL batch demonstration. Package and schema versions are 0.1.0; current master maintenance is distinguished by
its Git commit. See the root CHANGELOG for the heuristic-uncertainty label correction.
