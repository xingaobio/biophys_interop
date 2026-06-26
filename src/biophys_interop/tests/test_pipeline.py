"""End-to-end test: standardize -> validate -> qc -> featurize -> Adapter, on the golden examples.

Run: python src/biophys_interop/tests/test_pipeline.py   (asserts; exits non-zero on failure)
"""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # repo root
sys.path.insert(0, os.path.join(ROOT, "src"))

from biophys_interop import standardize, qc, featurize, validate, Adapter, FEATURE_DIM
from biophys_interop.qc import RULES, RULE_COUNT

EX = os.path.join(os.path.dirname(HERE), "examples")


def run_one(name):
    raw = json.load(open(os.path.join(EX, name)))
    mod = raw["modality"]
    rec = standardize(raw, mod)
    # units normalized: no nested {value,unit} survive in measurement
    assert all(not isinstance(v, dict) or "value" not in v for v in rec["measurement"].values()), "units not normalized"
    rec = qc(rec)
    chk = dict(rec); chk.pop("_qc_inputs", None)
    ok, errs = validate(chk)
    assert ok, f"{name} invalid: {errs}"
    assert rec["uncertainty"]["source"] == "calibrated"
    fx = featurize(rec)
    assert fx["vector"].shape == (FEATURE_DIM,)
    assert fx["mask"].any()
    cond = Adapter(backbone_dim=128, feature_dim=FEATURE_DIM)(np.zeros(128, np.float32), fx["vector"])
    assert cond.shape == (128,)
    return rec


def main():
    assert RULE_COUNT >= 50, f"expected >=50 QC rules, have {RULE_COUNT}"
    assert len({r['code'] for r in RULES}) == RULE_COUNT, "duplicate rule codes"
    spr = run_one("spr.json")
    assert spr["qc"]["flag"] == "fail", "SPR example should fail QC (titration + equilibration)"
    codes = {r["code"] for r in spr["qc"]["reasons"]}
    assert {"titration_regime", "equilibration"} <= codes, codes
    assert spr["uncertainty"]["value"] > spr["uncertainty"]["reported"] if spr["uncertainty"]["reported"] else True

    saxs = run_one("saxs.json")
    assert saxs["qc"]["flag"] == "fail", "SAXS example should fail QC (aggregation)"
    assert any(r["code"] == "guinier_upward_curvature" for r in saxs["qc"]["reasons"])

    dms = run_one("dms.json")
    assert {"low_read_count", "simulated"} <= {r["code"] for r in dms["qc"]["reasons"]}

    dls = run_one("dls.json")
    assert {"high_polydispersity", "rh_mw_inconsistent"} <= {r["code"] for r in dls["qc"]["reasons"]}
    fida = run_one("fida.json")   # solution-state, label-free affinity; should validate + featurize cleanly

    print("ALL TESTS PASSED:")
    for nm, rec in (("SPR", spr), ("SAXS", saxs), ("DMS", dms), ("DLS", dls), ("FIDA", fida)):
        print(f"  {nm}: qc={rec['qc']['flag']} score={rec['qc']['score']} "
              f"reasons={[r['code'] for r in rec['qc']['reasons']]}")


if __name__ == "__main__":
    main()
