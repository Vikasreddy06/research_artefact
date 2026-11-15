#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analysis import analyse, metrics  # noqa: E402

OUT = ROOT / "results/evaluation_runs/all_runs"


# Analyse each run folder and write the per-run and aggregated tables
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*", help="run folders, in run order")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--name", default="evaluation_runs", help="file prefix, e.g. sensitivity_runs")
    args = ap.parse_args(argv)
    alpha = yaml.safe_load(open(ROOT / "config/experiment.yaml"))["alpha"]
    rows, tests = [], []
    for number, folder in enumerate(args.runs, start=1):
        gt, dl, st, info = metrics.load_run(folder)
        req = metrics.per_request(gt, dl, st, info)
        cells = metrics.cell_summary(req, B=2000, seed=0)  # as in analyse.py
        t = pd.concat([analyse.dup_tests(cells, alpha).assign(metric="duplicate-mutation rate"),
                       analyse.cont_tests(req, "latency_ms", alpha, 2000, 0)], ignore_index=True)
        t.insert(0, "run", number)
        tests.append(t)
        cells.insert(0, "run", number)
        cells.insert(1, "seed", json.loads((Path(folder) / "run_info.json").read_text())["seed"])
        rows.append(cells)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    all_cells = pd.concat(rows, ignore_index=True)
    all_cells.to_csv(out / f"{args.name}_cells.csv", index=False, na_rep="N/A")
    all_tests = pd.concat(tests, ignore_index=True)
    if len(all_tests):  # sensitivity runs have no comparisons
        all_tests.to_csv(out / f"{args.name}_tests.csv", index=False, na_rep="N/A")
    agg = all_cells.groupby(["path", "multiplicity"], sort=True).agg(
        runs=("run", "nunique"),
        dup_rate_mean=("dup_rate", "mean"), dup_rate_min=("dup_rate", "min"), dup_rate_max=("dup_rate", "max"),
        capacity_mean=("capacity_mean", "mean"), capacity_min=("capacity_mean", "min"),
        capacity_max=("capacity_mean", "max"),
        latency_mean=("latency_mean_ms", "mean"), latency_min=("latency_mean_ms", "min"),
        latency_max=("latency_mean_ms", "max"),
    ).reset_index()
    agg.to_csv(out / f"{args.name}_aggregate.csv", index=False, na_rep="N/A")
    print(agg[["path", "multiplicity", "dup_rate_mean", "capacity_mean", "latency_min", "latency_max"]]
          .round(1).to_string(index=False, na_rep="N/A"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
