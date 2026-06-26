"""featurize(record, encoder='ref-v0') -> fixed-dim, model-agnostic feature vector.

Implements INTEROP_SPEC §6. Output is a plain numpy vector (no LLM/backbone dependency) so any consumer
can project it onto their own model via the Adapter contract (§7). The reference encoder 'ref-v0' is
deterministic. Layout (D=64): dims 0-27 modality one-hot (28 fixed slots so adding modalities never shifts
scalars), 28-51 scalar features (kinetics, thermodynamics, SAXS shape, DMS, conditions, calibrated
uncertainty + QC, and solution-state size/shape/dispersity), 52-63 reserved for a learned curve/profile
embedding.
Upgrade path: replace this with a learned encoder while keeping the {vector, mask, meta} interface.
"""
from __future__ import annotations
import math
import numpy as np
from . import schema

D = 64
ENCODER = "ref-v0"
MOD_SLOTS = 28                                                # fixed one-hot capacity (>= len(MODALITIES))
_MOD_INDEX = {m: i for i, m in enumerate(schema.MODALITIES)}  # modalities -> dims 0..MOD_SLOTS-1
assert len(schema.MODALITIES) <= MOD_SLOTS, "MODALITIES exceeds one-hot capacity; raise MOD_SLOTS"


def _log10p(x):
    try:
        x = float(x)
        return math.log10(x) if x > 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def featurize(record: dict, encoder: str = ENCODER) -> dict:
    v = np.zeros(D, dtype=np.float32)
    mask = np.zeros(D, dtype=bool)
    m = record.get("measurement", {})
    cond = record.get("conditions", {})
    unc = record.get("uncertainty", {})
    qc = record.get("qc", {})

    def put(i, val, present=True):
        v[i] = float(val) if val is not None else 0.0
        mask[i] = present and (val is not None)

    # 0-27: modality one-hot (28 fixed slots)
    mi = _MOD_INDEX.get(record.get("modality"), _MOD_INDEX["other"])
    v[mi] = 1.0; mask[mi] = True

    # 28-30: affinity/kinetics (log10)
    put(28, _log10p(m.get("KD")), "KD" in m)
    put(29, _log10p(m.get("kon")), "kon" in m)
    put(30, _log10p(m.get("koff")), "koff" in m)
    # 31-33: ITC thermodynamics
    put(31, m.get("dH"), "dH" in m)
    put(32, m.get("dS"), "dS" in m)
    put(33, m.get("n"), "n" in m)
    # 34-36: SAXS shape
    put(34, m.get("Rg"), "Rg" in m)
    put(35, m.get("Dmax"), "Dmax" in m)
    put(36, _log10p(m.get("I0")), "I0" in m)
    # 37-38: DMS
    put(37, m.get("fitness"), "fitness" in m)
    put(38, m.get("ddG"), "ddG" in m)
    # 39-40: conditions
    put(39, cond.get("temperature_K"), cond.get("temperature_K") is not None)
    put(40, cond.get("pH"), cond.get("pH") is not None)
    # 41-45: calibrated signal-quality block (the Gap-4 value)
    put(41, unc.get("value"), unc.get("value") is not None)
    put(42, unc.get("inflation_factor"), unc.get("inflation_factor") is not None)
    put(43, qc.get("score"), qc.get("score") is not None)
    put(44, qc.get("n_warn", 0) + qc.get("n_fail", 0), True)
    put(45, 1.0 if qc.get("flag") == "fail" else 0.0, True)   # hard-fail gate -> Route 2 can reject pre-redesign
    # 46-51: solution-state size/shape/dispersity (AUC/FIDA/DLS/SEC-MALS/nDSF/MP/native_MS)
    put(46, m.get("Rh"), "Rh" in m)
    put(47, m.get("PDI"), "PDI" in m)
    put(48, m.get("s_value"), "s_value" in m)
    put(49, _log10p(m.get("MW")), "MW" in m)
    put(50, m.get("Tm"), "Tm" in m)
    put(51, m.get("helix_pct"), "helix_pct" in m)
    # 52-63: reserved for a learned curve/profile embedding (kept zero/masked in ref-v0)

    return {"vector": v, "mask": mask,
            "meta": {"encoder": encoder, "dim": D, "schema_version": schema.SCHEMA_VERSION,
                     "work_or_record": record.get("record_id")}}
