# biophys_interop (v0.1.0)

A small, dependency-light (numpy-only) reference toolkit for representing heterogeneous
biophysical experimental data (SPR / BLI / ITC / SAXS / MST / NMR / DMS / …) as
**calibrated, model-agnostic, quality-controlled** records and feature vectors.

The problem: a Kd from SPR, an ITC ΔH, a SAXS Rg and a DMS fitness score are all
"binding/biophysics" yet live in incompatible units, formats, conditions, and quality —
so they cannot be pooled into one ML training set without heavy manual curation. This
toolkit defines the missing envelope plus the QC/uncertainty layer that makes them mergeable.

## Four contracts

| Function | Does | Spec |
|---|---|---|
| `standardize(raw, modality)` | loose dict → canonical record; units → SI | §3 |
| `qc(record)` | adds QC flags + calibrated uncertainty from method-aware rules | §5 |
| `featurize(record)` | → fixed-dim numpy vector, model-agnostic | §6 |
| `Adapter(H, D)(emb, feat)` | bolt-on conditioning contract (frozen backbone + thin adapter) | §7 |

Full design rationale: [`INTEROP_SPEC_v0.md`](../../INTEROP_SPEC_v0.md).

## Run

```bash
pip install -e .                     # from the repo root
python3 -m biophys_interop.cli run      src/biophys_interop/examples/spr.json
python3 -m biophys_interop.cli validate src/biophys_interop/examples/saxs.json
python3 src/biophys_interop/tests/test_pipeline.py
```

(Without installing, prefix commands with `PYTHONPATH=src`.)

## The core = `qc.py`

QC rules encode biophysics judgment as code (equilibration, titration regime, active
fraction, mass transport, ITC enthalpy/stoichiometry, SAXS aggregation, DMS read depth,
simulated-data leakage), each traceable to a literature basis (e.g. Jarmoskaite 2020,
Patrone 2024, Geng 2016) and paired with an `action`. The registry currently holds
**72 method-aware rules** across **24 modalities** (`qc.RULE_COUNT` is the single source
of truth — cite it, not a frozen number). Adding a new domain rule = appending one
`@rule(...)` function.

## Honesty notes

- `Adapter` weights are **untrained reference** (random-seeded); the contract validates
  shapes / bolt-on wiring, not predictions. A production version pairs a frozen backbone
  (e.g. a protein LM) with a small trained head of identical I/O. `trained=False` is exposed.
- `featurize` ref-v0 uses deterministic scalar features; dims 28–47 are reserved for a
  learned curve encoder.
- **No predictive metrics are claimed anywhere in this package.**

## Privacy / enterprise use

The intended deployment is local: a consumer runs
`standardize → qc → featurize → Adapter.fit(private_data)` inside their own environment,
merging public records with proprietary ones by concatenation. Raw private data never
leaves their environment.
