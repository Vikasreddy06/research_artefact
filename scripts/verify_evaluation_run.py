#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analysis import metrics  # noqa: E402


# Deliveries that did not behave as scheduled
def schedule_deviations(dl) -> tuple[int, int]:
    planned_timeout = dl["inject"] != "none"
    return int((~planned_timeout & (dl["status"] == "timeout")).sum()), int((planned_timeout & (dl["status"] != "timeout")).sum())


# Run the integrity checks on one run and write verify.json
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--out-json")
    args = ap.parse_args()
    folder = Path(args.run)
    gt, dl, st, info = metrics.load_run(folder)
    if info.get("backend") != "live":
        print("WARN: backend is not AWS Lambda:", info.get("backend"), file=sys.stderr)
    req = metrics.per_request(gt, dl, st, info)
    cells = metrics.cell_summary(req, B=200, seed=0)
    report = {
        "run": str(folder),
        "backend": info.get("backend"),
        "requests": int(len(req)),
        "invocations": info.get("invocations"),
        "stream_self_mismatch": int(req.stream_self_mismatch.sum()),
        "no_mutation": int(req.no_mutation.sum()),
        "missing_deliveries": int(req.missing_deliveries.sum()),
        "errors": int(req.errors.sum()),
        "lost_records": int(req.lost_records.sum()),
        "unlogged_mutations": int(req.unlogged_mutations.sum()),
        "dup_clamped": int(req.dup_clamped.sum()),
        "unplanned_timeouts": schedule_deviations(dl)[0],
        "injections_not_timed_out": schedule_deviations(dl)[1],
        "resent_deliveries": int(dl["resent_after"].map(bool).sum()),
        "cells": cells[["path","multiplicity","requests","injected_retries","dup_mutations","dup_rate",
                        "ccf_per_retry","successful_retry_rate","capacity_mean","latency_mean_ms"]].to_dict(orient="records"),
    }
    problems = []
    if report["missing_deliveries"]:
        problems.append(f"missing_deliveries={report['missing_deliveries']}")
    if report["errors"]:
        problems.append(f"errors={report['errors']}")
    if report["stream_self_mismatch"]:
        problems.append(f"stream_self_mismatch={report['stream_self_mismatch']}")
    if report["no_mutation"]:
        problems.append(f"no_mutation={report['no_mutation']}")
    for k in ("unlogged_mutations", "dup_clamped", "unplanned_timeouts", "injections_not_timed_out", "resent_deliveries"):
        if report[k]:
            problems.append(f"{k}={report[k]}")
    report["problems"] = problems
    report["ok"] = not problems
    out = Path(args.out_json) if args.out_json else folder / "verify.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"ok": report["ok"], "problems": problems, "requests": report["requests"]}, indent=2))
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
