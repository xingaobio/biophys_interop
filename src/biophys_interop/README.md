# biophys_interop (v0.1.0) — the Gap-4 core

A small, dependency-light (numpy-only) reference toolkit implementing `INTEROP_SPEC_v0`: the calibrated,
model-agnostic representation of heterogeneous biophysical experimental data. This is the program's
**primary, non-colliding contribution** (see `knowledge/landscape/gaps.md` v3 and `foresight_2026Q3.md`).

## Four contracts
| Function | Does | Spec |
|---|---|---|
| `standardize(raw, modality)` | loose dict -> canonical record; units -> SI | §3 |
| `qc(record)` | adds QC flags + **calibrated uncertainty** from distilled biophysics rules | §5 |
| `featurize(record)` | -> fixed-dim numpy vector, model-agnostic | §6 |
| `Adapter(H, D)(emb, feat)` | bolt-on conditioning contract (frozen backbone + thin adapter) | §7 |

## Run
```bash
python -m biophys_interop.cli run      src/biophys_interop/examples/spr.json
python -m biophys_interop.cli validate src/biophys_interop/examples/saxs.json
python src/biophys_interop/tests/test_pipeline.py
```

## The moat = `qc.py`
QC rules encode biophysics judgment (equilibration, titration regime, active fraction, mass transport,
ITC enthalpy/stoichiometry, SAXS aggregation, DMS read depth, simulated-data leakage), each traceable to a
corpus source (Jarmoskaite 2020, Patrone 2024, Geng 2016). **This is where Xin's rules go** — extend the
rule set; it is what differentiates this from a generic data schema and from competitors building closed loops.

## Honesty notes (anti-stub compliant)
- `Adapter` weights are **untrained reference** (random-seeded); it validates shapes/bolt-on, not predictions.
  Production = torch frozen backbone + LoRA head with identical I/O. `trained=False` is exposed.
- `featurize` ref-v0 uses deterministic scalar features; dims 28–47 are reserved for a learned curve encoder.
- No metrics are claimed anywhere.

## Privacy / enterprise use
Consumers run `standardize -> qc -> featurize -> Adapter.fit(private_data)` **locally**; we ship spec + code +
(eventually) a frozen reference encoder + warm-start adapter. Raw private data never leaves their environment.
