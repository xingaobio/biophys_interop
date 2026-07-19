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


def _row_to_raw(row, default_modality):
    """Map a flat CSV/TSV row (affinity measurement) into a raw pipeline record.

    Recognized columns (case-insensitive, all optional except an affinity value):
      modality, record_id/id, entity_id/target, molecule, assay_type/type,
      value_nM|KD_nM|affinity_nM (nanomolar) OR value+unit, relation, doi, source_db,
      n_replicates, temperature_C, pH, buffer.
    """
    g = {k.lower(): v for k, v in row.items()}

    def pick(*names, default=None):
        for n in names:
            if n in g and g[n] not in (None, "", "nan"):
                return g[n]
        return default

    modality = pick("modality", default=default_modality)
    val_nM = pick("value_nm", "kd_nm", "affinity_nm")
    meas = {}
    # Emit KD as a flat molar float: this survives both the affinity-modality _to_molar path
    # and the generic "other" branch (which keeps only non-dict measurement values).
    if val_nM is not None:
        meas["KD"] = float(val_nM) * 1e-9
    elif pick("value") is not None:
        _unit = str(pick("unit", default="nM")).lower()
        _scale = {"m": 1.0, "mm": 1e-3, "um": 1e-6, "µm": 1e-6, "nm": 1e-9, "pm": 1e-12}.get(_unit, 1e-9)
        meas["KD"] = float(pick("value")) * _scale
    raw = {
        "record_id": pick("record_id", "id", default=None),
        "modality": modality,
        "entity_id": pick("entity_id", "target", default="unknown"),
        "assay_type": pick("assay_type", "type", default=None),
        "doi": pick("doi"),
        "source_db": pick("source_db", default="input"),
        "measurement": meas,
    }
    for opt, cast in (("n_replicates", int), ("temperature_C", float), ("pH", float)):
        v = pick(opt.lower())
        if v is not None:
            try:
                raw[opt] = cast(v)
            except (TypeError, ValueError):
                pass
    if pick("buffer") is not None:
        raw["buffer"] = pick("buffer")
    # pass through identity columns for the output table
    passthrough = {k: g[k] for k in ("molecule", "relation", "pchembl", "target", "type") if k in g}
    return raw, modality, passthrough


def cmd_batch(path, modality="other", outdir="biophys_interop_out"):
    """CSV/TSV -> canonical Parquet + QC report JSON + manifest JSON."""
    import csv as _csv
    import hashlib
    import datetime
    import os

    # read CSV or TSV by extension/sniff
    delim = "\t" if path.lower().endswith((".tsv", ".tab")) else ","
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(_csv.DictReader(f, delimiter=delim))
    if not rows:
        print(f"[batch] no rows in {path}")
        return 1

    os.makedirs(outdir, exist_ok=True)
    out_records = []
    flag_counts, rule_counts = {}, {}
    for i, row in enumerate(rows):
        raw, mod, extra = _row_to_raw(row, modality)
        rec = qc(standardize(raw, mod))
        flag = rec["qc"]["flag"]
        flag_counts[flag] = flag_counts.get(flag, 0) + 1
        for r in rec["qc"]["reasons"]:
            rule_counts[r["code"]] = rule_counts.get(r["code"], 0) + 1
        m = rec.get("measurement", {})
        out_records.append({
            "record_id": rec.get("record_id"),
            "modality": mod,
            "entity_id": rec.get("entity", {}).get("id"),
            **{k: extra[k] for k in extra},
            "KD_M": m.get("KD"),
            "value_nM": (m.get("KD") * 1e9) if isinstance(m.get("KD"), (int, float)) else None,
            "qc_flag": flag,
            "qc_score": rec["qc"]["score"],
            "qc_reasons": ";".join(r["code"] for r in rec["qc"]["reasons"]),
            "uncertainty_value": rec.get("uncertainty", {}).get("value"),
            "uncertainty_inflation": rec.get("uncertainty", {}).get("inflation_factor"),
        })

    # canonical output: Parquet if pandas+pyarrow present, else JSONL fallback
    canon_path = os.path.join(outdir, "canonical.parquet")
    wrote_parquet = True
    try:
        import pandas as pd
        pd.DataFrame(out_records).to_parquet(canon_path, index=False)
    except Exception:
        wrote_parquet = False
        canon_path = os.path.join(outdir, "canonical.jsonl")
        with open(canon_path, "w", encoding="utf-8") as f:
            for r in out_records:
                f.write(json.dumps(r) + "\n")

    # QC report
    report = {
        "input": path,
        "n_records": len(out_records),
        "flag_counts": flag_counts,
        "rule_trigger_counts": dict(sorted(rule_counts.items(), key=lambda kv: -kv[1])),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    report_path = os.path.join(outdir, "qc_report.json")
    json.dump(report, open(report_path, "w"), indent=2)

    # manifest (input hash + tool version)
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    from . import __version__ as _ver
    manifest = {
        "tool": "biophys_interop", "version": _ver,
        "input_file": path, "input_sha256": h, "input_records": len(rows),
        "outputs": {"canonical": os.path.basename(canon_path), "qc_report": "qc_report.json"},
        "generated_at": report["generated_at"],
    }
    manifest_path = os.path.join(outdir, "manifest.json")
    json.dump(manifest, open(manifest_path, "w"), indent=2)

    print(f"[batch] {len(out_records)} records -> {outdir}/")
    print(f"  canonical : {os.path.basename(canon_path)} ({'parquet' if wrote_parquet else 'jsonl fallback'})")
    print(f"  qc_report : qc_report.json  (flags: {flag_counts})")
    print(f"  manifest  : manifest.json   (input sha256 {h[:16]}…)")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="biophys_interop")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "run"):
        s = sub.add_parser(name); s.add_argument("path")
    b = sub.add_parser("batch", help="CSV/TSV -> canonical Parquet + QC report + manifest")
    b.add_argument("path")
    b.add_argument("--modality", default="other", help="default modality for rows without a modality column")
    b.add_argument("--outdir", default="biophys_interop_out")
    a = p.parse_args(argv)
    if a.cmd == "batch":
        return cmd_batch(a.path, a.modality, a.outdir)
    return {"validate": cmd_validate, "run": cmd_run}[a.cmd](a.path)


if __name__ == "__main__":
    sys.exit(main())
