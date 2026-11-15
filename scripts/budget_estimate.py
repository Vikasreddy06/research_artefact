#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from driver.schedule import build  # noqa: E402

OK_BILLED_MS = 200     # estimated billed time of a delivery that does not time out
REINIT_MS = 500        # estimated start-up time after a timeout
WORKERS = 1            # Makefile WORKERS; warm-up waves are rounds x workers per run
EVALUATION_RUNS = 3    # Makefile evaluation-runs
SENSITIVITY_RUNS = 3   # Makefile sensitivity-runs


# Write units of one request delivered m times
def write_units(path: str, m: int, inject: str) -> float:
    if path in ("P1", "P2"):
        return float(m)                  # P1 writes every time; P2 writes once + (m-1) failed conditions at one unit each by rule
    if inject == "p3_between":
        return 2.0 * (m - 1) + 3         # claim + business write before each timeout, the full path at the end
    return 3.0 + (m - 1)                 # claim, business write, complete + (m-1) failed claims


# Count requests, invocations, timeouts and write units of one phase
def phase_counts(cfg: dict, phase: str, n: int | None = None) -> dict:
    reqs = build(cfg, phase, n)
    inv = sum(r["multiplicity"] for r in reqs)
    tmo = sum(r["injected_retries"] for r in reqs)
    wru = sum(write_units(r["path"], r["multiplicity"], r["inject_mode"]) for r in reqs)
    return {"phase": phase, "requests": len(reqs), "invocations": inv, "timeouts": tmo, "wru": wru}


# Estimate the cost in USD of the pilot, evaluation and sensitivity runs, and in total
def estimate(cfg: dict, n: int) -> tuple[list[dict], float]:
    prices = yaml.safe_load(open(ROOT / "config/prices.yaml"))
    versions = yaml.safe_load(open(ROOT / "config/versions.yaml"))
    gb = versions["lambda"]["memory_mb"] / 1024
    timeout_s = versions["lambda"]["timeout_s"]
    ev = phase_counts(cfg, "evaluation", n)
    ev = {k: v if k == "phase" else v * EVALUATION_RUNS for k, v in ev.items()} | {"phase": f"evaluation x{EVALUATION_RUNS}"}
    se = phase_counts(cfg, "sensitivity", n)
    se = {k: v if k == "phase" else v * SENSITIVITY_RUNS for k, v in se.items()} | {"phase": f"sensitivity x{SENSITIVITY_RUNS}"}
    rows = [phase_counts(cfg, "pilot"), ev, se]
    warm = (1 + EVALUATION_RUNS + SENSITIVITY_RUNS) * cfg.get("warmup_rounds", 0) * WORKERS
    rows.append({"phase": "warm-up", "requests": 0, "invocations": warm, "timeouts": 0, "wru": 0.0})
    total = 0.0
    for r in rows:
        ok = r["invocations"] - r["timeouts"]
        r["gb_s"] = gb * (r["timeouts"] * timeout_s + ok * OK_BILLED_MS / 1000 + r["timeouts"] * REINIT_MS / 1000)
        r["usd"] = (r["invocations"] * prices["lambda_request"] + r["gb_s"] * prices["lambda_gb_second"]
                    + r["wru"] * prices["dynamodb_write_request_unit"])
        total += r["usd"]
    return rows, total


# Invocations of the largest single run, warm-up included (the driver's cap is per run)
def largest_run(cfg: dict, n: int) -> int:
    runs = [phase_counts(cfg, "pilot"), phase_counts(cfg, "evaluation", n), phase_counts(cfg, "sensitivity", n)]
    return max(r["invocations"] for r in runs) + cfg.get("warmup_rounds", 0) * WORKERS


# Print the cost estimate and check the largest run against the cap
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, help="evaluation requests per cell (default: the configured size)")
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(open(ROOT / "config/experiment.yaml"))
    n = args.n or cfg["evaluation"]["requests_per_cell"]
    rows, total = estimate(cfg, n)
    print(f"{'phase':12s} {'requests':>9s} {'invocations':>12s} {'timeouts':>9s} {'write units':>12s} "
          f"{'GB-s':>9s} {'USD':>8s}")
    for r in rows:
        print(f"{r['phase']:12s} {r['requests']:9d} {r['invocations']:12d} {r['timeouts']:9d} {r['wru']:12.0f} "
              f"{r['gb_s']:9.0f} {r['usd']:8.3f}")
    inv, big, cap = sum(r["invocations"] for r in rows), largest_run(cfg, n), cfg["budget"]["max_invocations"]
    print(f"pilot, evaluation and sensitivity runs: USD {total:.2f} for {inv} invocations; largest single run {big} (cap per run {cap}); "
          f"logs, stream reads and free tier not included")
    return 0 if big <= cap else 1


if __name__ == "__main__":
    raise SystemExit(main())
