from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis import stats

NUMERIC = ["consumed_capacity", "wcu_ccf_rule", "ccf", "business_writes", "rtt_ms", "ddb_ms"]


# Read a JSON-lines file into a data frame
def read_jsonl(path: str | Path) -> pd.DataFrame:
    with open(path, encoding="utf-8") as fh:
        return pd.DataFrame([json.loads(line) for line in fh if line.strip()])


# Load the ground truth, deliveries, stream and run info of one run folder
def load_run(folder: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None, dict]:
    folder = Path(folder)
    gt = read_jsonl(folder / "ground_truth.jsonl")
    dl = read_jsonl(folder / "deliveries.jsonl")
    st = read_jsonl(folder / "stream.jsonl") if (folder / "stream.jsonl").exists() else None
    info = json.loads((folder / "run_info.json").read_text()) if (folder / "run_info.json").exists() else {}
    return gt, dl, st, info


# Keep stream events that fall inside the run's wall-clock window
def _stream_in_run_window(st: pd.DataFrame, info: dict | None, skew_s: float = 120.0) -> pd.DataFrame:
    if not info or "t_start" not in info or "t_end" not in info:
        return st
    if "approx_created_s" not in st.columns or st["approx_created_s"].isna().all():
        return st
    lo, hi = float(info["t_start"]) - skew_s, float(info["t_end"]) + skew_s
    ts = pd.to_numeric(st["approx_created_s"], errors="coerce")
    return st[ts.between(lo, hi)].copy()


# Build one row per request with mutations, duplicates, capacity and latency
def per_request(gt: pd.DataFrame, dl: pd.DataFrame, st: pd.DataFrame | None = None,
                info: dict | None = None) -> pd.DataFrame:
    dl = dl.copy()
    for c in NUMERIC:
        dl[c] = pd.to_numeric(dl[c], errors="coerce")
    g = dl.groupby("request_id")
    agg = pd.DataFrame({
        "observed_deliveries": g.size(),
        "capacity_reported": g["consumed_capacity"].sum(min_count=1),
        "capacity_rule": g["wcu_ccf_rule"].sum(),
        "ccf": g["ccf"].sum(),
        "timeouts": g["status"].agg(lambda s: int((s == "timeout").sum())),
        "errors": g["status"].agg(lambda s: int((s == "error").sum())),
        "lost_records": g["consumed_capacity"].agg(lambda s: int(s.isna().sum())),
        "self_mutations": g["business_writes"].sum(),
        "e2e_ms": g["rtt_ms"].sum(min_count=1),
    })
    final = dl[dl["delivery"] == dl["multiplicity"]].drop_duplicates("request_id").set_index("request_id")
    agg = agg.join(final[["status", "outcome", "rtt_ms", "ddb_ms", "cold_start"]].rename(columns={
        "status": "final_status", "outcome": "final_outcome", "rtt_ms": "latency_ms", "ddb_ms": "ddb_ms",
        "cold_start": "cold_final"}))
    keep = ["phase", "path", "multiplicity", "inject_mode", "injected_retries"]
    if "order" in gt.columns:
        keep = keep + ["order"]
    out = gt.set_index("request_id")[keep].join(agg)
    out["observed_deliveries"] = out["observed_deliveries"].fillna(0).astype(int)
    if "order" not in out.columns:
        out["order"] = list(range(len(out)))
    else:
        out["order"] = pd.to_numeric(out["order"], errors="coerce")

    if st is not None and len(st):
        st_win = _stream_in_run_window(st, info)
        b = st_win[(st_win["kind"] == "business") & st_win["event"].isin(["INSERT", "MODIFY"])].copy()
        # keep only changes made by this run's deliveries; any others are counted in unlogged_mutations
        unlogged = b.iloc[0:0]
        if "exec_id" in dl.columns and "exec_id" in b.columns:
            known = set(dl["exec_id"].dropna().astype(str))
            unlogged = b[~b["exec_id"].astype(str).isin(known)]
            b = b[b["exec_id"].astype(str).isin(known)]
        out["unlogged_mutations"] = unlogged.groupby("request_id").size().reindex(out.index).fillna(0).astype(int)
        out["mutations"] = b.groupby("request_id").size().reindex(out.index).fillna(0).astype(int)
        out["mutation_source"] = "stream"
        out["stream_windowed"] = len(st_win) < len(st)
    else:
        out["mutations"] = out["self_mutations"].fillna(0).astype(int)
        out["mutation_source"] = "self_report"
        out["stream_windowed"] = False
        out["unlogged_mutations"] = 0
    out["dup_mutations"] = (out["mutations"] - 1).clip(lower=0)
    # a request cannot have more duplicates than retries; dup_clamped flags a request where this applied
    out["dup_clamped"] = out["dup_mutations"] > out["injected_retries"]
    out["dup_mutations"] = out[["dup_mutations", "injected_retries"]].min(axis=1).astype(int)
    out["successful_retries"] = (out["injected_retries"] - out["dup_mutations"]).clip(lower=0)
    out["capacity_total"] = out["capacity_reported"] + out["capacity_rule"]
    out.loc[out["path"] == "P1", ["ccf", "capacity_rule"]] = np.nan  # P1 has no conditional write: N/A, not 0
    out["missing_deliveries"] = out["multiplicity"] - out["observed_deliveries"]
    out["no_mutation"] = out["mutations"] == 0
    out["stream_self_mismatch"] = out["mutations"] != out["self_mutations"].fillna(-1)
    return out.reset_index()


# Summarise each path and delivery-count cell with rates, means and CIs
def cell_summary(req: pd.DataFrame, alpha: float = 0.05, B: int = 2000, seed: int = 0) -> pd.DataFrame:
    rows = []
    for (phase, path, m), g in req.groupby(["phase", "path", "multiplicity"], sort=True):
        retries, dups = int(g["injected_retries"].sum()), int(g["dup_mutations"].sum())
        p, lo, hi = stats.wilson(dups, retries, alpha)
        clo, chi = stats.cluster_rate_ci(g["dup_mutations"], g["injected_retries"], B, alpha, seed)
        # share of requests with any duplicate: keeps a width where the bootstrap has none
        rp, rlo, rhi = stats.wilson(int((g["dup_mutations"] > 0).sum()), int((g["injected_retries"] > 0).sum()), alpha)
        cap = g["capacity_total"].dropna()
        lat = g["latency_ms"].dropna()
        e2e = g["e2e_ms"].dropna()
        warm = g.loc[g["cold_final"] == False, "latency_ms"].dropna()  # noqa: E712 - column may hold None
        rows.append({
            "phase": phase, "path": path, "multiplicity": int(m), "requests": len(g), "injected_retries": retries,
            "dup_mutations": dups, "dup_rate": p, "dup_ci_lo": lo, "dup_ci_hi": hi,
            "dup_cluster_ci_lo": clo, "dup_cluster_ci_hi": chi,
            "dup_request_share": rp, "dup_request_ci_lo": rlo, "dup_request_ci_hi": rhi,
            "ccf_per_retry": g["ccf"].sum(min_count=1) / retries if retries else np.nan,
            "successful_retry_rate": g["successful_retries"].sum() / retries if retries else np.nan,
            "capacity_mean": cap.mean(), **_ci("capacity_mean", cap, "mean", B, alpha, seed),
            "capacity_reported_mean": g["capacity_reported"].mean(), "capacity_rule_mean": g["capacity_rule"].mean(),
            "latency_mean_ms": lat.mean(), **_ci("latency_mean_ms", lat, "mean", B, alpha, seed),
            "e2e_mean_ms": e2e.mean() if len(e2e) else np.nan,
            **_ci("e2e_mean_ms", e2e, "mean", B, alpha, seed),
            "latency_p95_ms": lat.quantile(0.95) if len(lat) else np.nan,
            **_ci("latency_p95_ms", lat, "p95", B, alpha, seed),
            "latency_warm_mean_ms": warm.mean() if len(warm) else np.nan,
            "cold_final_share": float((g["cold_final"] == True).mean()),  # noqa: E712
            "ddb_mean_ms": g["ddb_ms"].mean(),
            "missing_deliveries": int(g["missing_deliveries"].sum()), "errors": int(g["errors"].sum()),
            "lost_records": int(g["lost_records"].sum()), "stream_self_mismatch": int(g["stream_self_mismatch"].sum()),
            "no_mutation": int(g["no_mutation"].sum()), "mutation_source": g["mutation_source"].iloc[0],
        })
    return pd.DataFrame(rows)


# Bootstrap CI of one column, returned as named lower and upper bounds
def _ci(name: str, x: pd.Series, stat: str, B: int, alpha: float, seed: int) -> dict:
    lo, hi = stats.bootstrap_ci(x.to_numpy(float), stat, B, alpha, seed) if len(x) else (np.nan, np.nan)
    return {f"{name}_ci_lo": lo, f"{name}_ci_hi": hi}
