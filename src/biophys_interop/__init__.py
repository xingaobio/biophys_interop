"""biophys_interop — calibrated, model-agnostic representation of biophysical experimental data.

The four contracts (INTEROP_SPEC_v0):
    standardize(raw, modality) -> canonical record      (§3, units -> SI)
    qc(record)                 -> + QC flags + calibrated uncertainty   (§5, the moat)
    featurize(record)          -> fixed-dim numpy vector (§6, model-agnostic)
    Adapter(H, D)(emb, feat)   -> conditioning           (§7, bolt-on contract)

Quick start:
    from biophys_interop import standardize, qc, featurize, Adapter
    rec = qc(standardize(raw, "SPR"))
    fx  = featurize(rec)
    cond = Adapter(backbone_dim=1280)(backbone_emb, fx["vector"])
"""
from .schema import validate, units_ok, SCHEMA_VERSION, MODALITIES
from .standardize import standardize
from .qc import qc
from .featurize import featurize, D as FEATURE_DIM
from .adapter import Adapter

__all__ = ["standardize", "qc", "featurize", "Adapter", "validate", "units_ok",
           "SCHEMA_VERSION", "MODALITIES", "FEATURE_DIM"]
__version__ = "0.1.0"
