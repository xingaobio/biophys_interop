"""standardize(raw, modality) -> canonical record (INTEROP_SPEC §3).

Normalizes units to SI (affinities -> molar, temperature -> Kelvin, time -> seconds) and
structures a loose input dict into the canonical envelope. Idempotent on already-canonical input.
"""
from __future__ import annotations
import datetime
from . import schema

# affinity/concentration units -> molar
_MOLAR = {"M": 1.0, "mM": 1e-3, "uM": 1e-6, "µM": 1e-6, "nM": 1e-9, "pM": 1e-12, "fM": 1e-15}
# time -> seconds
_SEC = {"s": 1.0, "sec": 1.0, "min": 60.0, "h": 3600.0, "hr": 3600.0, "hour": 3600.0, "day": 86400.0}


def _to_molar(x):
    if isinstance(x, dict) and "value" in x:
        return float(x["value"]) * _MOLAR.get(x.get("unit", "M"), 1.0)
    return None if x is None else float(x)


def _to_seconds(x):
    if isinstance(x, dict) and "value" in x:
        return float(x["value"]) * _SEC.get(x.get("unit", "s"), 1.0)
    return None if x is None else float(x)


def _temp_K(raw):
    tk = raw.get("temperature_K")
    if tk is not None:
        return float(tk)
    tc = raw.get("temperature_C")
    if tc is not None:
        return float(tc) + 273.15
    return None


def standardize(raw: dict, modality: str) -> dict:
    """Map a loose measurement dict to the canonical record. Units -> SI."""
    modality = modality if modality in schema.MODALITIES else "other"
    m_in = raw.get("measurement", raw)  # accept flat or nested
    meas: dict = {}

    if modality in ("SPR", "BLI", "MST", "GCI",
                    "fluorescence_polarization", "switchSENSE", "smFRET"):
        # affinity/kinetics readouts: SPR/BLI/GCI (RI), MST (thermophoresis), FP (polarization, equilibrium Kd),
        # switchSENSE (DNA-lever kon/koff/Kd/Rh/Tm), smFRET (distance + binding kinetics + Kd)
        for k in ("KD", "limiting_conc", "trace_conc"):
            if k in m_in:
                meas[k] = _to_molar(m_in[k])
        if "kon" in m_in:
            meas["kon"] = float(m_in["kon"]["value"] if isinstance(m_in["kon"], dict) else m_in["kon"])  # 1/Ms
        if "koff" in m_in:
            meas["koff"] = float(m_in["koff"]["value"] if isinstance(m_in["koff"], dict) else m_in["koff"])  # 1/s
        for k in ("Rmax", "incubation_time", "chi2", "response_amplitude"):
            if k in m_in:
                meas[k] = _to_seconds(m_in[k]) if k == "incubation_time" else float(m_in[k])
    elif modality == "ITC":
        if "KD" in m_in:
            meas["KD"] = _to_molar(m_in["KD"])
        for k in ("dH", "dS", "n"):
            if k in m_in:
                meas[k] = float(m_in[k])
    elif modality == "SAXS":
        for k in ("Rg", "Dmax", "I0"):
            if k in m_in:
                meas[k] = float(m_in[k])
        for k in ("guinier_quality", "rg_from_pr"):
            if k in m_in:
                meas[k] = float(m_in[k])
    elif modality in ("AUC", "FIDA", "DLS", "SEC-MALS", "CD", "nDSF", "mass_photometry",
                      "native_MS", "DSC"):
        # solution-state size / shape / dispersity / oligomeric-state / thermal stability / mass.
        # native_MS: MW, stoichiometry n, n_species, KD (gas-phase). DSC: Tm + unfolding enthalpy dH.
        if "KD" in m_in:                       # FIDA / MP / native_MS can measure affinity in solution
            meas["KD"] = _to_molar(m_in["KD"])
        for k in ("Rh", "PDI", "s_value", "MW", "mw_sequence", "Tm", "helix_pct",
                  "n_species", "n", "monomer_fraction", "dH"):   # +dH for DSC unfolding enthalpy
            if k in m_in:
                meas[k] = float(m_in[k])
        if "oligomeric_state" in m_in:
            meas["oligomeric_state"] = m_in["oligomeric_state"]
    elif modality == "HDX-MS":
        # interface/dynamics, not an affinity number: capture protection + peptide coverage for QC
        for k in ("deuterium_uptake", "protection_factor", "n_peptides", "sequence_coverage"):
            if k in m_in:
                meas[k] = float(m_in[k])
        if "protected_regions" in m_in:
            meas["protected_regions"] = m_in["protected_regions"]
    elif modality == "DMS":
        for k in ("mutation", "fitness", "ddG"):
            if k in m_in:
                meas[k] = m_in[k] if k == "mutation" else float(m_in[k])
        if "read_count" in m_in:
            meas["read_count"] = int(m_in["read_count"])
    else:
        meas = {k: v for k, v in m_in.items() if not isinstance(v, dict)}

    # carry through any provided raw curve reference (sensorgram/profile) untouched
    for ref in ("sensorgram_ref", "profile_ref", "thermogram_ref", "trace_ref"):
        if ref in m_in:
            meas[ref] = m_in[ref]

    ent = raw.get("entity") or {"kind": raw.get("entity_kind", "protein"), "id": raw.get("entity_id", "unknown"),
                                "sequence": raw.get("entity_sequence")}
    cond = raw.get("conditions", {})
    rec = {
        "record_id": raw.get("record_id", f"rec-{modality}-{ent.get('id','x')}"),
        "schema_version": schema.SCHEMA_VERSION,
        "entity": ent,
        "modality": modality,
        "assay_type": raw.get("assay_type", modality),
        "measurement": meas,
        "conditions": {
            "temperature_K": _temp_K({**cond, **raw}),
            "pH": (cond.get("pH") if "pH" in cond else raw.get("pH")),
            "buffer": cond.get("buffer", raw.get("buffer")),
        },
        "n_replicates": raw.get("n_replicates"),
        "uncertainty": raw.get("uncertainty", {"value": None, "type": "std", "source": "reported"}),
        "qc": raw.get("qc", {"flag": "pass", "score": None, "reasons": []}),
        "provenance": {
            "source_db": raw.get("source_db", "unknown"),
            "doi": raw.get("doi"),
            "license": raw.get("license", "unspecified"),
            "retrieval_date": raw.get("retrieval_date", datetime.date.today().isoformat()),
            "derivation": raw.get("derivation", "measured"),
        },
        # keep the qc-relevant raw signals so qc() can reason over them
        "_qc_inputs": {k: m_in[k] for k in (
            "active_fraction", "baseline_drift", "aggregation", "radiation_damage", "regeneration_loss",
            "dilution_series", "heat_of_dilution_corrected", "csp_saturation", "referencing_reported",
            "exchange_broadening", "monolink_only", "local_resolution_variation",
            "stop_codon_control", "wt_normalization", "batch_id", "batch_control",
            "replicate_log_range", "sds_test", "labeling_homogeneous") if k in m_in},
    }
    return rec
