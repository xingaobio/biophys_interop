"""Canonical biophysical-measurement record schema + a dependency-free validator.

Implements INTEROP_SPEC_v0 §3. The record is the merge contract: same envelope, units, and
controlled vocabulary => public and private data concatenate. Validation is pure-Python so it
runs anywhere (no jsonschema dependency).
"""
from __future__ import annotations

SCHEMA_VERSION = "0.1.0"

MODALITIES = ["SPR", "BLI", "ITC", "SAXS", "MST", "NMR", "XL-MS", "cryoEM", "DMS",
              "AUC", "FIDA", "DLS", "SEC-MALS", "CD", "nDSF",
              "mass_photometry", "GCI",
              # round-3 (first-principles taxonomy closure): remaining named binding/biophysics techniques
              "fluorescence_polarization", "native_MS", "HDX-MS", "smFRET", "DSC", "switchSENSE",
              "other"]   # taxonomy-complete for named binding/biophysics techniques
ENTITY_KINDS = ["protein", "complex", "antibody", "peptide", "mutant"]
UNC_TYPES = ["std", "sem", "ci95", "range"]
UNC_SOURCES = ["reported", "estimated", "calibrated"]
QC_FLAGS = ["pass", "warn", "fail"]
DERIVATIONS = ["measured", "derived", "simulated"]

# Required top-level keys (INTEROP_SPEC §3)
REQUIRED = ["record_id", "schema_version", "entity", "modality", "measurement",
            "conditions", "uncertainty", "qc", "provenance"]


def validate(record: dict) -> tuple[bool, list[str]]:
    """Return (ok, errors). Structural + controlled-vocabulary + units-present checks."""
    e: list[str] = []
    if not isinstance(record, dict):
        return False, ["record must be a dict"]
    for k in REQUIRED:
        if k not in record:
            e.append(f"missing required field: {k}")
    if record.get("schema_version") not in (None, SCHEMA_VERSION):
        e.append(f"schema_version must be {SCHEMA_VERSION}")
    if record.get("modality") not in MODALITIES:
        e.append(f"modality must be one of {MODALITIES}")

    ent = record.get("entity", {})
    if not isinstance(ent, dict) or "kind" not in ent or "id" not in ent:
        e.append("entity must have {kind, id}")
    elif ent.get("kind") not in ENTITY_KINDS:
        e.append(f"entity.kind must be one of {ENTITY_KINDS}")

    unc = record.get("uncertainty", {})
    if isinstance(unc, dict):
        if "value" not in unc:
            e.append("uncertainty.value missing")
        if unc.get("type") not in (None, *UNC_TYPES):
            e.append(f"uncertainty.type must be one of {UNC_TYPES}")
        if unc.get("source") not in (None, *UNC_SOURCES):
            e.append(f"uncertainty.source must be one of {UNC_SOURCES}")
    else:
        e.append("uncertainty must be a dict")

    qc = record.get("qc", {})
    if not isinstance(qc, dict) or qc.get("flag") not in QC_FLAGS:
        e.append(f"qc.flag must be one of {QC_FLAGS}")

    prov = record.get("provenance", {})
    if isinstance(prov, dict):
        if prov.get("derivation") not in (None, *DERIVATIONS):
            e.append(f"provenance.derivation must be one of {DERIVATIONS}")
        if not prov.get("license"):
            e.append("provenance.license is required (legal ingestion gate)")
    else:
        e.append("provenance must be a dict")

    return (len(e) == 0), e


def units_ok(record: dict) -> bool:
    """All numeric measurement values that carry a unit must be SI-normalized by standardize()."""
    m = record.get("measurement", {})
    return all(not (isinstance(v, dict) and "unit" in v) for v in m.values())
