# biophys_interop

**Make messy biophysical measurements computable.**
An open standardization and *model-free* quality-control (QC) layer for heterogeneous biophysical bioactivity data.

[![Quickstart checks](https://github.com/xingaobio/biophys_interop/actions/workflows/quickstart.yml/badge.svg)](https://github.com/xingaobio/biophys_interop/actions/workflows/quickstart.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/xingaobio/biophys_interop/blob/master/notebooks/biophys_interop_quickstart.ipynb)

![Conceptual flow from heterogeneous biophysical measurements through standardization and transparent quality control to auditable canonical records](assets/biophys-interop-flow-light.png)

> **From measurements to reusable records.** The left side represents heterogeneous experimental evidence, including
> SPR sensorgrams, ITC thermograms, and binding dose-response curves. The central prism represents conversion into a
> shared schema followed by transparent, method-aware QC. The right side represents canonical records that retain QC
> outcomes and provenance, ready for reproducible downstream analysis.

- **Standardize:** convert reported values, units, metadata, and assay context into one canonical representation.
- **Quality control:** apply explicit, cited rules that return pass/warn/fail outcomes with reasons.
- **Preserve provenance:** retain record identifiers, QC evidence, and source information so each output is auditable.

---

## What this is

Machine-learning models for proteins increasingly train on large, pooled collections of laboratory measurements —
binding affinities (IC50, Ki, Kd, EC50) together with biophysical readouts from techniques such as surface plasmon
resonance (SPR), bio-layer interferometry (BLI), and isothermal titration calorimetry (ITC). These measurements arrive
in different units, different assay formats, and at different levels of quality. Pooling them without care injects
substantial noise, and the per-record quality flags that some databases attach are incomplete and do not travel with
the data once sources are combined.

`biophys_interop` is a small, dependency-light layer that turns raw measurements into records a downstream pipeline can
consume directly. It does three things to every measurement:

| Step | Function | What it does |
|------|----------|--------------|
| 1 | `standardize()` | Puts a raw record into one canonical schema across **24 measurement modalities**, with SI units. |
| 2 | `qc()` | Runs **72 transparent, method-aware rules** and attaches a `pass` / `warn` / `fail` flag **with reasons**. |
| 3 | `featurize()` | Emits a fixed-width **64-dimension** vector plus a mask marking which fields are trustworthy. |

There is no trained model anywhere in the quality-control step — the checks are simple, auditable rules a scientist can
read and argue with.

---

## Install

Until the package is published on PyPI, install it directly from this repository:

```bash
pip install "biophys_interop[batch] @ git+https://github.com/xingaobio/biophys_interop.git"
```

From source (this repository):

```bash
pip install -e ".[batch,test]"
```

> **Note.** `biophys_interop` is not yet on PyPI. Once it is published, the equivalent command will be
> `pip install "biophys_interop[batch]"`.

---

## 60-second quickstart

```python
from biophys_interop import standardize, qc, featurize

raw = {
    "record_id": "r1", "modality": "SPR", "entity_id": "P00519",
    "assay_type": "SPR", "temperature_C": 25,
    "measurement": {"KD": {"value": 2.0, "unit": "nM"},
                    "trace_conc": {"value": 5.0, "unit": "nM"}},
}

rec = standardize(raw, "SPR")   # KD -> 2e-9 M, temperature -> 298.15 K
rec = qc(rec)                   # rec["qc"]["flag"] == "fail"
fx  = featurize(rec)            # fx["vector"]: 64-dim; fx["mask"]: trustworthy fields
```

This SPR record is flagged **`fail`**, with the top reason `titration_regime`: the tested concentration (5 nM) is not
far below the reported K_D (2 nM), so this registry check raises a titration-regime flag for review. The flag is a heuristic screening result, not an independently verified experimental error. The layer always says *why*.

A full, runnable walkthrough (SPR, a method-aware ITC consistency check, and a batch run on real ChEMBL records) is in
[`notebooks/biophys_interop_quickstart.ipynb`](notebooks/biophys_interop_quickstart.ipynb) — open it in Colab and press
*Run all*.

---

## Command line

The package installs a `biophys-interop` console command with three sub-commands:

```bash
biophys-interop validate record.json          # schema + unit sanity check on one record
biophys-interop run      record.json          # standardize + qc + featurize one record
biophys-interop batch    data.csv \
    --modality SPR --outdir out/              # whole CSV/TSV -> canonical + qc_report + manifest
```

`batch` is the typical entry point for a dataset. Given any flat CSV/TSV with a `value_nM` column, it runs every row
through `standardize → qc` and writes three files to `--outdir`:

- `canonical.parquet` (or `canonical.jsonl` if `pyarrow` is not installed) — the standardized records;
- `qc_report.json` — per-flag counts and which rules fired;
- `manifest.json` — the input SHA-256 and the tool version, so a cleaned dataset can be regenerated and audited later.

Try it on the bundled 200-row sample:

```bash
biophys-interop batch examples/demo_input.csv --outdir out/
```

---

## QC registry and benchmark evidence

The 72 rules are documented in [`docs/rule_cards.md`](docs/rule_cards.md) (human-readable) and
[`docs/rule_cards.json`](docs/rule_cards.json) (machine-readable). Each rule carries its modality, severity, literature
basis, and the action it triggers. The registry and the manuscript benchmark operations have different scopes:

- **Benchmark operations (not general validation).** Two affinity-data operations were compared with ChEMBL annotation
  proxies in the manuscript benchmarks. The R1 analysis is a post-hoc restricted range analysis; R5b is a
  source-order-dependent exact-value duplicate operation and is **not** one of the public 72 registry rules. Neither
  comparison validates an equivalent public rule against independently source-verified error labels.
- **Literature-grounded registry (72 rules).** The public rules — thermodynamic consistency for
  ITC, titration-regime checks for SPR/BLI/MST, Guinier-quality checks for SAXS, and so on — are grounded in the
  measurement literature but are **not** claimed as empirically validated here, because rule-level source-confirmed error labels were not
  evaluated here. Treat them as a transparent, executable registry, not as
  validated detectors.

---

## What the benchmark comparisons showed

The manuscript benchmarks use ChEMBL annotations as **proxies**, not independently verified source errors. On 175,387
real ChEMBL affinity records across 30 targets, the historical leave-one-target-out comparisons gave MCC 0.612 for the
R1 range analysis and 0.648 for R5b. Simple semantic baselines performed equally well or better, so these results do
not establish algorithmic superiority.

A prospectively frozen 12-target evaluation (50,664 records; no historical target-ID overlap) gave MCC 0.778 for R1
and 0.670 for R5b. The documented fixed-range proxy (0.901) and relation-preserving duplicate baseline (0.673) again
performed as well or better. The fresh-target split still has molecule overlap with the historical cache, and its labels
remain ChEMBL annotations.

The cross-repository comparison identifies review candidates, rather than automatically verified errors: among 1,714
shared ChEMBL–BindingDB keys, 38 differed by at least 100-fold and 34 lacked a ChEMBL validity flag. Primary-paper
evidence is currently available for six enriched historical cases (five database unit/value problems and one
construct-collapse interoperability flag); the remaining cases are unresolved at source level.

The v1 preprint is available at
[ChemRxiv DOI 10.26434/chemrxiv.15006416/v1](https://doi.org/10.26434/chemrxiv.15006416/v1). A revised manuscript and
its public-limited companion is available at [10.5281/zenodo.23097835](https://doi.org/10.5281/zenodo.23097835).
ChemRxiv v2 and JCIM submissions were reported by the author on 2 October 2026; public v2 approval and journal
acceptance are not confirmed. The v1 link remains the preprint entry until v2 publication is verified.
Numbers above are traceable to the analysis records, and the stated limitations are part of the result.

---

## Reproduce the cached statistics

The [public-limited companion](https://zenodo.org/records/23097835) contains retained tables and an offline checker.
Download `chemrxiv_v2_companion_limited_2026-09-16.zip`, extract it, and run from the extracted directory:

```bash
python3 tools/recalculate_public_limited_companion.py
```

The published archive passes 100 cached-statistics checks. Its SHA-256 is
`e37cb0fbcf0020563cba5be183b83ba4272c5fbaaa9f41710f76e7fac989a7a3`.
This reconstructs statistics from cached inputs; it does not reacquire all raw data or rerun hosted models.
Hosted MAPK14 outputs, Figure 8 and related derivatives are excluded; see the archive's
`EXCLUDED_HOSTED_MATERIALS.csv` for all 11 exclusions. The Colab notebook demonstrates basic toolkit use and
processes 200 sample rows; it does not reproduce the manuscript analyses.

Default uncertainty from `qc()` is an **estimated heuristic**, not calibrated error. The maintenance update labels it
`source="estimated", method="heuristic"`; its numeric calculation is unchanged. A fitted calibrator can be supplied
explicitly, but the measured metadata-to-error predictor did not generalize (held-out R² approximately 0.025).
See [CHANGELOG.md](CHANGELOG.md) for the output-label migration.

## Repository layout

```
src/biophys_interop/     the package (standardize, qc, featurize, adapter, cli, schema)
  examples/*.json        one worked record per modality
  tests/test_pipeline.py assert-based smoke tests
notebooks/               runnable Colab/Jupyter quickstart (+ its own README)
examples/demo_input.csv  200-row real-ChEMBL sample for the batch command
docs/rule_cards.{md,json} the 72-rule QC registry, human- and machine-readable
pyproject.toml           build + dependency metadata
LICENSE                  MIT (code)
```

Run the tests:

```bash
python src/biophys_interop/tests/test_pipeline.py
python tools/verify_quickstart.py --local-checkout
```

---

## Data sources and licensing

- **Code:** MIT (this repository).
- **Validation data:** ChEMBL (release ChEMBL_37) under CC BY-SA 3.0; the independent cross-database comparison uses
  BindingDB (release BindingDB_All 202606) under CC BY 3.0 US. The bundled `examples/demo_input.csv` is a small sample
  of ChEMBL records included for demonstration.

Please cite the original databases when you use the validation data.

---

## Citation

If you use `biophys_interop`, cite the software using [`CITATION.cff`](CITATION.cff) and its version DOI:
[10.5281/zenodo.21446585](https://doi.org/10.5281/zenodo.21446585). The reproducibility dataset and QC rule registry
for the original release are archived separately at [10.5281/zenodo.21446602](https://doi.org/10.5281/zenodo.21446602).
The revised public-limited companion has its own DOI: [10.5281/zenodo.23097835](https://doi.org/10.5281/zenodo.23097835).
The preprint is [ChemRxiv v1](https://doi.org/10.26434/chemrxiv.15006416/v1). These identifiers refer to distinct
archived objects; current GitHub maintenance is identified by its commit, not a replacement archive DOI.

---

## Status and scope

This is a v0.1.0 research release. The standardization layer is the mature core. The 72 rules are a transparent,
literature-grounded registry; the benchmark comparisons described above do not make the registry a collection of
empirically validated detectors. A curated, flag-annotated biophysical benchmark is still needed for direct rule-level
evaluation. Issues and pull requests are welcome.
