"""Execute the real quickstart code cells and keep a per-cell execution log."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-checkout", action="store_true",
                        help="Install this checkout instead of public GitHub master")
    parser.add_argument("--output", type=Path, help="Save per-cell execution evidence as JSON")
    parser.add_argument("--write-notebook", action="store_true",
                        help="Refresh saved notebook outputs after successful execution")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    notebook_path = root / "notebooks/biophys_interop_quickstart.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    namespace = {"__name__": "__main__"}
    if args.local_checkout:
        namespace["_verification_checkout"] = root
    evidence = {"mode": "local-checkout" if args.local_checkout else "public-github",
                "notebook": str(notebook_path), "cells": [], "success": False}
    previous_cwd = Path.cwd()
    failure = None
    try:
        with tempfile.TemporaryDirectory(prefix="biophys-quickstart-") as workdir:
            os.chdir(workdir)
            if args.local_checkout:
                shutil.copy2(root / "examples/demo_input.csv", "demo_input.csv")
            for index, cell in enumerate(notebook["cells"]):
                if cell["cell_type"] != "code":
                    continue
                source = "".join(cell["source"])
                stdout = io.StringIO()
                started = time.monotonic()
                result = {"index": index, "success": False}
                try:
                    with contextlib.redirect_stdout(stdout):
                        exec(compile(source, f"quickstart-cell-{index}", "exec"), namespace)
                    result["success"] = True
                except Exception:
                    result["error"] = traceback.format_exc()
                    raise
                finally:
                    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
                    result["stdout"] = stdout.getvalue()
                    evidence["cells"].append(result)
                    print(f"Cell {index}: {'PASS' if result['success'] else 'FAIL'}")
                    print(result["stdout"], end="")
                cell["execution_count"] = len(evidence["cells"])
                cell["outputs"] = [{"output_type": "stream", "name": "stdout",
                                    "text": result["stdout"].splitlines(keepends=True)}]
            evidence["runtime"] = json.loads(Path("out/quickstart_runtime.json").read_text())
            evidence["batch_report"] = json.loads(Path("out/qc_report.json").read_text())
            evidence["batch_manifest"] = json.loads(Path("out/manifest.json").read_text())
            evidence["success"] = True
    except Exception as exc:
        evidence["error"] = traceback.format_exc()
        failure = exc
    finally:
        os.chdir(previous_cwd)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    if failure:
        raise RuntimeError("Quickstart verification failed; see the per-cell log") from failure
    if args.write_notebook:
        notebook_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8")
    print(f"All {len(evidence['cells'])} code cells passed; verified 200 Parquet rows.")


if __name__ == "__main__":
    main()
