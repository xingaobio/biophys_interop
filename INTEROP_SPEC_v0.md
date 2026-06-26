---
title: "Biophysical Data Interoperability Spec (INTEROP_SPEC_v0)"
version: "0.1.0 (DRAFT)"
owner: "Dr. Xin Gao"
date: "2026-06-08"
status: "DESIGN DRAFT — not yet implemented. Defines the terminal deliverable contract."
purpose: >
  Define how heterogeneous, non-standardized biophysical experimental data (collected from public
  literature/databases) is standardized so that the project's outputs can (1) be concatenated directly
  into an enterprise's PRIVATE dataset, and (2) plug into the enterprise's AI protein-design pipeline —
  WITHOUT the enterprise exposing its private data.
---

# Biophysical Data Interoperability Spec — v0

> **North star.** The terminal asset of this program is **not** a model or a dataset; it is this
> *standard + reference toolkit*: a way to represent SPR / BLI / ITC / SAXS / MST / NMR / XL-MS /
> cryo-EM / DMS measurements as **calibrated, uncertainty-aware, model-agnostic** records and features
> that a biotech can merge into proprietary data and bolt onto an existing foundation model.
> Think "middleware / connector for biophysical→AI data", not "another end-to-end model".

---

## 1. Design principles (the five contracts that make outputs "drop-in")

1. **Shared schema.** Every measurement uses the same envelope, units, and controlled vocabulary.
   Schema-aligned data merges by concatenation (§4).
2. **Uncertainty + QC as first-class fields.** Public *and* private data are noisy; a consistent
   `uncertainty` + `qc` representation is what lets them be pooled into one training set (§5). This is
   the program's core differentiator (Gap 4).
3. **Units & ontology normalization.** Map to existing ontologies, never invent ad-hoc vocab (§2, §3).
4. **Clean provenance & licensing.** Each record carries source + license so enterprise legal can
   ingest without IP contamination. (Project policy: open-access only for full text.)
5. **Model-agnostic + privacy-preserving interface.** Ship a *featurization spec* + a *frozen reference
   encoder* + a *thin adapter contract* (§6–§7). The enterprise fine-tunes the adapter **locally** on
   private data; raw data never leaves their environment (§8).

---

## 2. Alignment to existing standards (ride adoption — do NOT reinvent)

A solo new standard rarely gets adopted. v0 is positioned as an **extension layer** over frameworks
biotech/pharma already use. We adopt their identifiers, units, and serialization wherever possible and
only add the "experimental-readout → AI feature" layer that is missing.

| Layer | Existing standard we align to | What we reuse |
|---|---|---|
| FAIR data principles | FAIR (Findable/Accessible/Interoperable/Reusable) | overall governance + metadata discipline |
| Pharma/lab analytical data | **Allotrope (ADF)**, **SiLA 2** | enterprise data-model + instrument-integration alignment |
| Structures | **mmCIF / PDBx**, AlphaFoldDB | entity/structure identifiers, coordinate refs |
| SAXS | **SASBDB** | profile format, Rg/Dmax/I0 conventions |
| NMR | **BMRB / NMR-STAR** | chemical shifts, restraint conventions |
| Mass spec / XL-MS | **mzML / PRIDE**, mzIdentML | spectra refs, crosslink reporting |
| Affinity / mutation | **SKEMPI 2.0**, SAbDab, AB-Bind | field names for KD/ΔΔG, mutation syntax |
| Ontologies | **OBI** (assays), **UO** (units), **ChEBI** (chemicals), **PSI-MI** (interactions) | controlled vocab |
| Minimum-information + metadata templates | **MIABE** (bioactive entity), **MIMIx** (molecular interaction), with **MIAME/MINSEQE** as precedent; **CEDAR** templates + **FAIRSharing** (300+ reporting guidelines) | our record = reporting-guideline attributes with ontology-bound values (cf. Musen 2025 `wiley-aaai-70048`, Wilson 2021 `wiley-1873-3468-14067`) |
| ML dataset metadata | **MLCommons Croissant** | dataset-level card for ML consumption |

> Conformance rule: a field that already exists in one of the above MUST use that source's term/format;
> v0 only defines the *cross-modality envelope* and the *AI featurization/adapter contract*.

---

## 3. The canonical record (envelope shared by all modalities)

One measurement = one record. Modality-specific values live under `measurement` (validated by `oneOf`).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/biophys-record-v0.schema.json",
  "title": "BiophysicalMeasurementRecord",
  "type": "object",
  "required": ["record_id","schema_version","entity","modality","measurement",
               "conditions","uncertainty","qc","provenance"],
  "properties": {
    "record_id":    { "type": "string", "description": "stable unique id" },
    "schema_version": { "const": "0.1.0" },
    "entity": {
      "type": "object",
      "required": ["kind","id"],
      "properties": {
        "kind":      { "enum": ["protein","complex","antibody","peptide","mutant"] },
        "id":        { "type": "string", "description": "construct/accession id" },
        "sequence":  { "type": "string" },
        "structure_ref": { "type": "string", "description": "PDB/mmCIF/AlphaFoldDB id or hash" },
        "mutations": { "type": "array", "items": { "type": "string" },
                       "description": "HGVS-like, e.g. A:T28Y" }
      }
    },
    "modality":   { "enum": ["SPR","BLI","ITC","SAXS","MST","NMR","XL-MS","cryoEM","DMS",
                              "AUC","FIDA","DLS","SEC-MALS","CD","nDSF",
                              "mass_photometry","GCI",
                              "fluorescence_polarization","native_MS","HDX-MS","smFRET","DSC","switchSENSE",
                              "other"] },
    "assay_type": { "type": "string", "description": "OBI term where available" },
    "measurement": { "type": "object", "description": "modality-specific; see §3.1 (oneOf)" },
    "conditions": {
      "type": "object",
      "properties": {
        "temperature_K": { "type": "number" },
        "pH":            { "type": "number" },
        "buffer":        { "type": "string" },
        "concentration": { "type": "object",
                           "properties": { "value": {"type":"number"}, "unit_uo": {"type":"string"} } }
      }
    },
    "uncertainty": {
      "type": "object",
      "required": ["value","type","source"],
      "properties": {
        "value":  { "type": "number" },
        "type":   { "enum": ["std","sem","ci95","range"] },
        "source": { "enum": ["reported","estimated","calibrated"] }
      }
    },
    "qc": {
      "type": "object",
      "required": ["flag"],
      "properties": {
        "flag":    { "enum": ["pass","warn","fail"] },
        "score":   { "type": "number", "minimum": 0, "maximum": 1 },
        "reasons": { "type": "array", "items": { "type": "string" },
                     "description": "controlled QC reason codes, see §5" }
      }
    },
    "provenance": {
      "type": "object",
      "required": ["source_db","license","retrieval_date","derivation"],
      "properties": {
        "source_db":      { "type": "string" },
        "doi":            { "type": "string" },
        "url":            { "type": "string" },
        "license":        { "type": "string" },
        "retrieval_date": { "type": "string", "format": "date" },
        "parser":         { "type": "string" },
        "derivation":     { "enum": ["measured","derived","simulated"],
                            "description": "simulated signals MUST be flagged here" }
      }
    }
  }
}
```

### 3.1 Modality payloads (`measurement`, selected by `oneOf`)

| Modality | Required fields (units via UO) | Optional raw-signal ref |
|---|---|---|
| **SPR / BLI** | `KD`, `kon`, `koff`, `Rmax` | `sensorgram_ref` (time, response) |
| **ITC** | `KD`, `dH`, `dS`, `n` (stoichiometry) | `thermogram_ref` |
| **SAXS** | `Rg`, `Dmax`, `I0` | `profile_ref` (q, I(q), σ) — SASBDB format |
| **MST** | `KD`, `response_amplitude` | `trace_ref` |
| **NMR** | `restraint_type`, `value` | `shifts_ref` (BMRB/NMR-STAR) |
| **XL-MS** | `residue_a`, `residue_b`, `max_distance` | `spectra_ref` (PRIDE) |
| **cryoEM** | `resolution`, `map_ref` (EMDB) | — |
| **DMS** | `mutation`, `fitness` or `ddG` | `assay_ref` |
| **AUC** (sedimentation) | `s_value`, `MW`, `n_species`, `oligomeric_state` | `c(s)_ref` |
| **FIDA / TDA** (Taylor dispersion, label-free, in-solution) | `Rh`, `KD` | `taylorgram_ref` |
| **DLS** | `Rh`, `PDI` (polydispersity) | — |
| **SEC-MALS** | `MW`, `Rh`, `oligomeric_state` | `chromatogram_ref` |
| **CD / nDSF** | `helix_pct` / `Tm` | `spectrum_ref` / `melt_ref` |

> **Solution-state size/shape/dispersity** methods (AUC, FIDA/TDA, DLS, SEC-MALS) capture oligomeric state,
> hydrodynamic radius, polydispersity, and (FIDA) label-free in-solution affinity — orthogonal *quality* signals
> that feed the QC layer (§5) and avoid SPR immobilization/mass-transport artifacts.

> Raw-signal refs point to a stored array (Parquet/HDF5) so the *curve itself* — not just summary
> scalars — is available to the featurizer (§6). This is what enables Route 2's experimental modality.

---

## 4. The "drop-in merge" guarantee

Because a public record and a private record share the **same envelope, units, ontology, and QC
fields**, merging is `concat(public_df, private_df)` on the canonical schema. Conformance is checked by:

- `validate(record)` against the JSON Schema above → structural pass.
- `units_ok(record)` → all units resolve to UO terms.
- `provenance_complete(record)` → license + derivation present (so legal can filter `derivation != simulated`).

Serialization: **Parquet/Arrow** (tabular records) + **HDF5** (raw curves) + a dataset-level
**Croissant** card. These are formats enterprise stacks already consume.

---

## 5. QC & uncertainty spec (the differentiator / Gap 4)

A controlled vocabulary of QC reason codes per modality, e.g. for SPR/BLI:
`baseline_drift`, `bulk_shift`, `mass_transport_limited`, `regeneration_loss`, `aggregation`,
`steric_hindrance`, `non_1to1_kinetics`. For SAXS: `guinier_upward_curvature` (aggregation),
`radiation_damage`, `interparticle_repulsion`. Each code maps to (a) a deterministic heuristic or a
small classifier, and (b) a documented action (`distrust` / `re-measure` / `down-weight`).

`uncertainty.source = calibrated` means the value came from this layer's calibration model (not the
paper's reported error). Calibration is fit on real or **documented-simulated** signals; the simulation
protocol is versioned and `derivation = simulated` is set so it can be excluded from clean splits.

This layer is consumable two ways: as **training-sample weights** and as **active-learning filters**.

---

## 6. Featurization contract (model-agnostic)

```
featurize(record, reference_encoder) -> {
  "vector":  float[D],          # fixed dim per modality family
  "mask":    bool[D],           # which dims are populated
  "meta":    { "encoder": "<name>@<version>", "weights_sha256": "...", "schema_version": "0.1.0" }
}
```

- `D` is fixed and documented per modality family; scalars + a downsampled/encoded curve are concatenated.
- The **reference encoder** is shipped with frozen weights + a content hash, so a feature vector is
  reproducible and portable across consumers.
- Output is a plain tensor — it carries **no dependency on any specific LLM/backbone**.

---

## 7. Adapter contract (plug into THEIR pipeline)

```
adapter(backbone_embedding: float[H], experimental_feature: float[D]) -> conditioning: float[H]
```

- The enterprise's **backbone is frozen**; only the projection/cross-attention **adapter** is trainable.
- Documented tensor shapes (`H` = backbone hidden size; `D` = §6) + a reference PyTorch module so it
  bolts onto ESM-2 / a 7–9B LLM / their proprietary model alike.
- We ship: (a) the frozen reference encoder (§6), (b) a pretrained adapter as a warm start, (c) the
  training recipe to fine-tune the adapter on the consumer's data.

> **The fine-tuning is a co-primary contribution, not just plumbing.** In the paper, the trained adapter
> (Route 2 experimental-readout adapter + Route 1 LoRA decision agent) and its **with/without-experiment
> ablation** + benchmark wins are headline results — they are the existence proof that the standardized
> signal carries usable information. Present it as a **transferable adaptation *method*** (LoRA + adapter
> contract), not a one-off checkpoint, so it survives base-model churn and is what enterprises re-train on
> private data. Standard ⇄ fine-tuning are mutually reinforcing: the standard makes the model reusable;
> the model proves the standard is useful.

---

## 8. Privacy / federation (data never leaves the enterprise)

The whole stack is designed so the consumer runs `standardize → qc → featurize → adapter-finetune`
**inside their own environment**. We distribute the *spec + code + frozen encoder + warm-start adapter*;
they keep the raw private data and the fine-tuned adapter. No private data is transmitted to us. This is
what makes "merge into their dataset + plug into their pipeline" realistic for IP-sensitive biotech.

---

## 9. Reference toolkit (what gets built & released)

A single pip-installable library exposing four contracts:

```python
from biophys_interop import standardize, qc, featurize, Adapter
rec = standardize(raw, modality="SPR")   # -> canonical record (§3)
rec = qc(rec)                            # -> + qc/uncertainty (§5)
fx  = featurize(rec, encoder="ref-v0")   # -> tensor (§6)
cond = Adapter()(backbone_emb, fx.vector) # -> conditioning (§7)
```

Plus a CLI validator (`biophys-validate file.parquet`) and golden conformance examples.

---

## 10. Versioning & governance

- SemVer on `schema_version`; v0.x is unstable, breaking changes allowed; freeze at v1.0.0.
- Spec + reference toolkit released under a permissive license; the calibration *rules* are the
  maintained core contribution, published openly.
- A conformance test suite is the source of truth for "is this v0-compliant".
- Pressure-test the schema against real private-data shapes with an early adopter — adoption, not
  elegance, decides whether this becomes a standard.

---

## 11. Validation that the standard works (end-to-end interoperability check)

Run one public dataset **and** one simulated "private" dataset through the **same** pipeline; show that
(a) they merge under the schema, and (b) an adapter trained on the pooled set beats training on either
alone. This single experiment validates the interoperability claim end-to-end.

---
### END v0 — implement the toolkit (§9) against this contract; align fields to §2 before adding any new vocab.
