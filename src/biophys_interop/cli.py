"""CLI: validate or run the pipeline on a raw record JSON.

    python -m biophys_interop.cli validate examples/spr.json
    python -m biophys_interop.cli run      examples/spr.json
"""
from __future__ import annotations
import argparse, json, sys
from . import standardize, qc, featurize, validate


def _load(path):
    raw = json.load(open(path, encoding="utf-8"))
    return raw, raw.get("modality", "other")


def cmd_validate(path):
    raw, mod = _load(path)
    rec = qc(standardize(raw, mod))
    rec.pop("_qc_inputs", None)
    ok, errs = validate(rec)
    print(f"[{'OK' if ok else 'INVALID'}] {path}")
    for e in errs:
        print("  -", e)
    return 0 if ok else 1


def cmd_run(path):
    raw, mod = _load(path)
    rec = qc(standardize(raw, mod))
    fx = featurize(rec)
    print(f"== {path} ({mod}) ==")
    print(f"  qc.flag   : {rec['qc']['flag']}  (score {rec['qc']['score']})")
    for r in rec["qc"]["reasons"]:
        print(f"    - [{r['severity']}] {r['code']}: {r['message']}  (basis: {r['basis']})")
    u = rec["uncertainty"]
    print(f"  uncertainty: {u['value']} (calibrated, x{u['inflation_factor']} of reported {u['reported']})")
    print(f"  feature   : dim={fx['meta']['dim']}, nonzero={int((fx['vector']!=0).sum())}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="biophys_interop")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "run"):
        s = sub.add_parser(name); s.add_argument("path")
    a = p.parse_args(argv)
    return {"validate": cmd_validate, "run": cmd_run}[a.cmd](a.path)


if __name__ == "__main__":
    sys.exit(main())
