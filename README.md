# biophys_interop

**Standardize biophysical measurements. Flag quality concerns. Keep the evidence attached.**

`biophys_interop` is a Python toolkit for preparing heterogeneous bioactivity measurements for curation,
comparison and downstream analysis. It converts reported values into a shared schema, applies explicit
quality-control (QC) rules, and produces records and features that another pipeline can consume.

[![Quickstart checks](https://github.com/xingaobio/biophys_interop/actions/workflows/quickstart.yml/badge.svg)](https://github.com/xingaobio/biophys_interop/actions/workflows/quickstart.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/xingaobio/biophys_interop/blob/master/notebooks/biophys_interop_quickstart.ipynb)

[Quickstart](#quickstart) · [Batch processing](#process-a-csv-or-tsv) · [QC rules](docs/rule_cards.md) ·
[Companion materials](https://zenodo.org/records/23097835) · [Preprint](https://doi.org/10.26434/chemrxiv.15006416/v1)

![Biophysical measurements become canonical records through standardization and transparent quality control](assets/biophys-interop-flow-light.png)

## What you can do

- **Standardize measurements across 24 modalities.** Normalize supported units and assay conditions in one schema.
- **Inspect 72 explicit QC rules.** Each applicable check returns a reason, severity, literature basis and suggested action.
- **Prepare features for another model.** Generate a 64-dimensional vector and a mask identifying available fields.
- **Audit a batch.** Export canonical rows, QC counts and an input-hash manifest from a CSV or TSV.

QC is deterministic and model-free. Flags identify issues to review; they are not proof that a measurement is wrong.
The toolkit's reference `Adapter` is untrained and does not provide structure or affinity predictions.

## Quickstart

**Try it in your browser:** [open the Colab notebook](https://colab.research.google.com/github/xingaobio/biophys_interop/blob/master/notebooks/biophys_interop_quickstart.ipynb)
and choose **Runtime → Run all**. No GPU is required. The notebook covers illustrative SPR/ITC records and a real
200-row ChEMBL sample, verifies the batch output, and saves the source commit and runtime package versions.

**Install locally:** use Python 3.9 or newer with Git available. The `batch` extra adds pandas and pyarrow for Parquet output;
the core package depends only on NumPy.

```bash
python -m pip install "biophys_interop[batch] @ git+https://github.com/xingaobio/biophys_interop.git@master"
```

Then run this illustrative surface-plasmon-resonance (SPR) record:

```python
from biophys_interop import standardize, qc, featurize

raw = {
    "record_id": "r1", "modality": "SPR", "entity_id": "P00519",
    "assay_type": "SPR", "temperature_C": 25,
    "measurement": {
        "KD": {"value": 2.0, "unit": "nM"},
        "trace_conc": {"value": 5.0, "unit": "nM"},
    },
}

record = qc(standardize(raw, "SPR"))
features = featurize(record)

print(record["measurement"]["KD"])
print(record["conditions"]["temperature_K"])
print(record["qc"]["flag"], record["qc"]["reasons"][0]["code"])
print(record["uncertainty"]["source"], record["uncertainty"]["method"])
print(features["vector"].shape)
```

Expected output:

```text
2e-09
298.15
fail titration_regime
estimated heuristic
(64,)
```

The value and temperature are normalized to molar units and kelvin. The tested concentration exceeds the reported
`KD`, so the titration-regime rule flags the record for review. Missing assay metadata produces additional reasons.
Default uncertainty is a **heuristic estimate**, not a calibrated error or confidence interval.

## Process a CSV or TSV

To run the bundled sample, clone the repository and install from that checkout:

```bash
git clone https://github.com/xingaobio/biophys_interop.git
cd biophys_interop
python -m pip install -e ".[batch]"
biophys-interop batch examples/demo_input.csv --outdir out/
```

The sample produces **200 canonical rows**, all flagged `warn` because experimental metadata is incomplete.
Batch processing writes:

- `out/canonical.parquet`: standardized values, identifiers, QC flags and reasons for each input row.
- `out/qc_report.json`: record counts, flag counts and rule-trigger counts.
- `out/manifest.json`: input SHA-256, tool version, record count and output filenames.

If Parquet dependencies are unavailable, the CLI writes `canonical.jsonl`. The Colab notebook also writes
`quickstart_runtime.json` with the resolved Git commit and Python/package versions.

For your own data, replace the sample path. Accepted affinity columns include `value_nM`, `KD_nM`, `affinity_nM`,
or a `value`/`unit` pair. Optional columns include `record_id`, `target`, `modality`, `assay_type`, `temperature_C`,
`pH`, `buffer`, `n_replicates`, `doi` and `source_db`. Set `--modality SPR`, for example, when the method is known;
otherwise the default is `other`. A row's `modality` column takes precedence over this default.

For individual JSON records, the same command-line interface provides:

```bash
biophys-interop validate src/biophys_interop/examples/spr.json
biophys-interop run src/biophys_interop/examples/spr.json
```

## Understand the evidence

The [human-readable rule cards](docs/rule_cards.md), [JSON registry](docs/rule_cards.json) and
[CSV registry](docs/rule_cards.csv) describe the 72 public rules. They are grounded in measurement literature and
curation conventions; this study does not establish their rule-level accuracy against independently verified errors.

The manuscript's ChEMBL benchmarks evaluate two separate affinity-data operations against **database annotation
proxies**. R1 is a post-hoc restricted range analysis; R5b is a source-order-dependent dataset operation outside the
public registry. Their results do not validate equivalent registry rules:

- **Historical benchmark:** 175,387 records across 30 targets; R1/R5b MCC 0.612/0.648.
- **Prospective fresh-target benchmark:** 50,664 records across 12 targets; R1/R5b MCC 0.778/0.670 versus
  semantic baselines 0.901/0.673. Target IDs are disjoint, but molecule overlap remains.
- **Source review:** six of 24 enriched convenience cases have primary-paper support: five unit/value problems and
  one construct-collapse flag. The other 18 remain unresolved; this is not a population precision estimate.

Simple semantic baselines performed as well or better, so these comparisons do not establish algorithmic superiority.
The optional learned metadata-to-error predictor also did not generalize (held-out R² approximately 0.025).
Use the rules to support review, and retain their reasons and source information with downstream data.

## Reproduce cached manuscript statistics

Download the [public-limited companion](https://zenodo.org/records/23097835), extract
`chemrxiv_v2_companion_limited_2026-09-16.zip`, and run from its extracted directory:

```bash
python3 tools/recalculate_public_limited_companion.py
```

The published archive passes **100 offline cached-statistics checks**. Its SHA-256 is:

```text
e37cb0fbcf0020563cba5be183b83ba4272c5fbaaa9f41710f76e7fac989a7a3
```

This reconstructs statistics from retained tables. It does not reacquire all raw data or rerun hosted models.
Hosted MAPK14 outputs, Figure 8 and related derivatives are excluded; `EXCLUDED_HOSTED_MATERIALS.csv` lists all
11 exclusions. The Colab quickstart demonstrates toolkit use and does not reproduce the manuscript analyses.

## Cite the materials you use

- **Software, archived v0.1.0:** [10.5281/zenodo.21446585](https://doi.org/10.5281/zenodo.21446585);
  structured citation in [CITATION.cff](CITATION.cff).
- **Original-release dataset and registry:** [10.5281/zenodo.21446602](https://doi.org/10.5281/zenodo.21446602).
- **Revised public-limited companion:** [10.5281/zenodo.23097835](https://doi.org/10.5281/zenodo.23097835).
- **Public preprint, ChemRxiv v1:** [10.26434/chemrxiv.15006416/v1](https://doi.org/10.26434/chemrxiv.15006416/v1).

These identifiers refer to different archived objects. ChemRxiv v2 and JCIM submissions were reported by the author
on 2 October 2026; public v2 approval and journal acceptance have not been independently confirmed.

## Development and versioning

From a Git checkout, install the batch dependencies as above, then run:

```bash
python src/biophys_interop/tests/test_pipeline.py
python tools/verify_quickstart.py --local-checkout
```

[GitHub Actions](https://github.com/xingaobio/biophys_interop/actions/workflows/quickstart.yml) runs the pipeline
checks and all seven notebook code cells on Python 3.9, 3.12 and 3.13, saving per-cell execution logs.
See [CONTRIBUTING.md](CONTRIBUTING.md) to propose a rule or report a problem, and [CHANGELOG.md](CHANGELOG.md)
for maintenance changes. Package and schema versions remain 0.1.0; record the Git commit when using current master.
The archived v0.1.0 tag predates the corrected `uncertainty.source="estimated"` label.

Source code is in [src/biophys_interop](src/biophys_interop), the walkthrough in [notebooks](notebooks), and the
batch sample in [examples/demo_input.csv](examples/demo_input.csv).

## Licensing

Code is [MIT licensed](LICENSE). The bundled ChEMBL sample is derived from data licensed CC BY-SA 3.0.
Manuscript comparisons also use BindingDB data under CC BY 3.0 US. Cite the original databases and retain their
applicable license obligations; the code license does not replace upstream data licenses.
