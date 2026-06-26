# biophys_interop — making biophysical experimental data computable

> A standardization + model-free **quality-control / interoperability layer** for heterogeneous
> biophysical bioactivity data. Public reference implementation.

Protein-design ML is bottlenecked less by models than by **data heterogeneity**: affinity, kinetics
and stability measurements (SPR, BLI, ITC, SAXS, MST, NMR, DMS, …) live in incompatible units,
formats, conditions, and quality, so they cannot be pooled into one training set without heavy manual
curation. `biophys_interop` defines a canonical record, encodes biophysics QC judgment as code, and
emits model-agnostic features — turning that mess into a mergeable, quality-controlled substrate.

## What's here

```
biophys_interop/
├── src/biophys_interop/      # the toolkit (numpy-only, tested)
│   ├── schema.py             # canonical record + validator — 24 modalities
│   ├── standardize.py        # loose dict → canonical record; units → SI
│   ├── qc.py                 # 72 method-aware QC rules, each cited (the core)
│   ├── featurize.py          # canonical record → fixed-dim model-agnostic vector
│   ├── adapter.py            # bolt-on conditioning contract (frozen backbone + thin head)
│   ├── calibration.py        # uncertainty calibration from replicate spread
│   ├── cli.py                # `validate` / `run`
│   ├── examples/*.json       # synthetic example records (SPR/SAXS/DLS/DMS/FIDA)
│   └── tests/test_pipeline.py
├── INTEROP_SPEC_v0.md        # the design spec (record schema + alignment to FAIR/Allotrope/…)
├── demo.ipynb                # runnable walkthrough on the synthetic examples
└── pyproject.toml            # pip-installable
```

## Quickstart

```bash
pip install -e .
python3 -m biophys_interop.cli run src/biophys_interop/examples/spr.json
python3 src/biophys_interop/tests/test_pipeline.py    # 5/5 pass
```

```python
from biophys_interop import standardize, qc, featurize, Adapter

rec = qc(standardize(raw, "SPR"))   # canonical record + QC flags + calibrated uncertainty
fx  = featurize(rec)                 # 64-dim model-agnostic vector
cond = Adapter(backbone_dim=1280)(backbone_emb, fx["vector"])   # bolt-on contract
```

## Design principles

1. **Shared schema** — one envelope, units, controlled vocabulary; aligned data merges by concatenation.
2. **Uncertainty + QC as first-class fields** — the differentiator (see `qc.py`).
3. **Units & ontology normalization** — reuse OBI / UO / ChEBI; never invent ad-hoc vocab.
4. **Clean provenance & licensing** — every record carries source + license.
5. **Model-agnostic + privacy-preserving** — consumers run the pipeline *locally*; raw private data
   never leaves their environment.

## Scope & honesty

This repository is the **engineering core** (schema + QC + featurization + adapter contract), built and
validated on public data. It is a reference implementation, not a trained predictor: the `Adapter` ships
**untrained** (it validates the bolt-on contract, not predictions) and **no predictive metrics are
claimed in this repo**. A validation study (model-free QC vs. an independent curator's labels) is in
preparation; figures and numbers available on request.

## License

Apache-2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
