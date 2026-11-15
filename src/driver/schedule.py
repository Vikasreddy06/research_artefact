from __future__ import annotations

import csv
import json
import random
import uuid
from functools import cache
from pathlib import Path

AMOUNTS_FILE = Path(__file__).resolve().parents[2] / "data/workload/amounts_cents.txt"


# Card-payment amounts in cents from a public dataset (scripts/fetch_amounts.py)
@cache
def amounts() -> tuple[int, ...]:
    with open(AMOUNTS_FILE, encoding="utf-8") as fh:
        return tuple(int(line) for line in fh if line.strip() and not line.startswith("#"))


# Synthetic payment request with a dataset amount
def payload(rng: random.Random, kb: int = 1) -> dict:
    p = {"amount_cents": rng.choice(amounts()),
         "note": "x" * max(0, kb * 1024 - 233)}  # pads the business item to just under 1 KB, one write unit
    return p


# Random request id from the seeded generator
def _rid(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


# Build the shuffled list of requests for a phase
def build(cfg: dict, phase: str, n_per_cell: int | None = None, seed: int | None = None) -> list[dict]:
    rng = random.Random(f"{seed if seed is not None else cfg['evaluation']['seed']}-{phase}")
    kb = cfg["payload_kb"]
    cells: list[tuple[str, int, str]] = []
    if phase == "pilot":
        n = n_per_cell or cfg["pilot"]["requests_per_path"]
        cells = [(p, cfg["pilot"]["multiplicity"], cfg["injection"]["primary"]) for p in cfg["paths"]]
    elif phase == "evaluation":
        n = n_per_cell or cfg["evaluation"]["requests_per_cell"]
        cells = [(p, m, cfg["injection"]["primary"]) for p in cfg["paths"] for m in cfg["multiplicities"]]
    elif phase == "sensitivity":
        n = n_per_cell or cfg["evaluation"]["requests_per_cell"]  # same size as the evaluation runs
        cells = [("P3", m, cfg["injection"]["sensitivity"]) for m in cfg["multiplicities"] if m > 1]
    else:
        raise ValueError(f"unknown phase {phase}")
    reqs = []
    for path, mult, inject in cells:
        for _ in range(n):
            reqs.append({"request_id": _rid(rng), "phase": phase, "path": path, "multiplicity": mult,
                         "inject_mode": inject, "injected_retries": mult - 1, "payload": payload(rng, kb)})
    rng.shuffle(reqs)
    for i, r in enumerate(reqs):
        r["order"] = i
    return reqs


# Deliveries of one request; all but the last get the injection mode
def deliveries(req: dict) -> list[dict]:
    n = req["multiplicity"]
    return [{"delivery": d, "inject": req["inject_mode"] if d < n else "none"} for d in range(1, n + 1)]


# The explicit injection schedule
def write_schedule(reqs: list[dict], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["order", "request_id", "path", "multiplicity", "delivery", "inject"])
        for r in reqs:
            for d in deliveries(r):
                w.writerow([r["order"], r["request_id"], r["path"], r["multiplicity"], d["delivery"], d["inject"]])
    return path


# Write one JSON line per request with its intended deliveries
def write_ground_truth(reqs: list[dict], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in reqs:
            row = {k: v for k, v in r.items() if k != "payload"}
            row["intended_deliveries"] = r["multiplicity"]
            fh.write(json.dumps(row) + "\n")
    return path
