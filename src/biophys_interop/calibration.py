"""Calibrator — turn QC features into a *fitted* uncertainty estimate (INTEROP_SPEC §5).

Upgrades qc()'s heuristic inflation into a model fitted to data: log(relative measurement error)
~ ridge-linear(QC features). Pure numpy (no sklearn). When a fitted Calibrator is passed to qc(),
the calibrated uncertainty comes from the model instead of the hand-tuned multiplier.

Honesty: this is the *machinery*. Fitting on REAL labels (e.g. replicate spreads from SKEMPI/AbAgym,
inter-lab reproducibility) is the production step. `experiments/.../fit_calibration.py` demonstrates the
fit on a DOCUMENTED SYNTHETIC dataset (flagged), recovering a known relationship — a methods check, not a
biological result.
"""
from __future__ import annotations
import json, math
import numpy as np

MODS = ["SPR", "BLI", "ITC", "SAXS", "MST", "NMR", "XL-MS", "cryoEM", "DMS", "other"]
# database-metadata signals that actually VARY on real repository data (ChEMBL etc.) and carry
# information about measurement reliability — populated via rec["_calib"] by the dataset loader.
CALIB_META = ["censored", "functional_assay", "db_flagged", "has_pchembl",
              "type_Ki", "type_Kd", "type_IC50", "log_group_size"]
FEATURE_NAMES = ["bias", "n_warn", "n_fail", "is_titration_fail", "is_equilibration_fail",
                 "qc_score", "log10_value"] + [f"mod_{m}" for m in MODS] + CALIB_META


def _primary_abs_value(rec):
    m = rec.get("measurement", {})
    for k in ("KD", "ddG", "fitness", "Rg", "I0"):
        v = m.get(k)
        if isinstance(v, (int, float)):
            return abs(float(v))
    return None


def feature_row(rec) -> np.ndarray:
    qc = rec.get("qc", {})
    codes = {r.get("code") for r in qc.get("reasons", [])}
    val = _primary_abs_value(rec)
    base = [
        1.0,
        float(qc.get("n_warn", 0)),
        float(qc.get("n_fail", 0)),
        1.0 if "titration_regime" in codes else 0.0,
        1.0 if "equilibration" in codes else 0.0,
        float(qc.get("score", 1.0) if qc.get("score") is not None else 1.0),
        math.log10(val) if (val and val > 0) else 0.0,
    ]
    onehot = [1.0 if rec.get("modality") == m else 0.0 for m in MODS]
    cm = rec.get("_calib", {})
    st = (cm.get("std_type") or "").lower()
    meta = [
        1.0 if cm.get("censored") else 0.0,
        1.0 if cm.get("functional_assay") else 0.0,
        1.0 if cm.get("db_flagged") else 0.0,
        1.0 if cm.get("has_pchembl") else 0.0,
        1.0 if st == "ki" else 0.0,
        1.0 if st == "kd" else 0.0,
        1.0 if st == "ic50" else 0.0,
        math.log10(float(cm["group_size"])) if cm.get("group_size") else 0.0,
    ]
    return np.array(base + onehot + meta, dtype=float)


class Calibrator:
    """Ridge-regression model: features -> log(relative error). predict() returns relative error."""

    def __init__(self, w=None, ridge=1e-2):
        self.w = None if w is None else np.asarray(w, dtype=float)
        self.ridge = ridge

    def fit(self, X, y_log_rel_error):
        X = np.asarray(X, dtype=float); y = np.asarray(y_log_rel_error, dtype=float)
        A = X.T @ X + self.ridge * np.eye(X.shape[1])
        self.w = np.linalg.solve(A, X.T @ y)
        return self

    def predict_rel_error(self, X):
        X = np.asarray(X, dtype=float)
        return np.exp(X @ self.w)

    def predict_uncertainty(self, rec):
        """Return (absolute_uncertainty, relative_error) for one record."""
        rel = float(self.predict_rel_error(feature_row(rec).reshape(1, -1))[0])
        val = _primary_abs_value(rec)
        return ((val * rel) if val is not None else None), rel

    def save(self, path):
        json.dump({"w": self.w.tolist(), "ridge": self.ridge, "features": FEATURE_NAMES},
                  open(path, "w"))

    @classmethod
    def load(cls, path):
        d = json.load(open(path))
        return cls(w=d["w"], ridge=d.get("ridge", 1e-2))
