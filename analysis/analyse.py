from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis import metrics, stats  # noqa: E402
from analysis.tables import md_table, source_label  # noqa: E402

PATHS = ["P1", "P2", "P3"]
PAIRS = [("P1", "P2"), ("P1", "P3"), ("P2", "P3")]


# z-tests of the duplicate rate: P1 against P2 and P3, and P2 against P3
def dup_tests(cells: pd.DataFrame, alpha: float) -> pd.DataFrame:
    c = cells.set_index(["path", "multiplicity"])
    rows = []
    for m in sorted(cells.loc[cells["injected_retries"] > 0, "multiplicity"].unique()):
        for a, b, alt in (("P1", "P2", "greater"), ("P1", "P3", "greater"), ("P2", "P3", "two-sided")):
            if (a, m) not in c.index or (b, m) not in c.index:
                continue
            x, y = c.loc[(a, m)], c.loc[(b, m)]
            k1, n1, k2, n2 = (int(x["dup_mutations"]), int(x["injected_retries"]), int(y["dup_mutations"]),
                              int(y["injected_retries"]))
            z, p = stats.two_prop_z(k1, n1, k2, n2, alt)
            d, lo, hi = stats.newcombe_diff(k1, n1, k2, n2, alpha)
            rows.append({"multiplicity": int(m), "comparison": f"{a} vs {b}",
                         "alternative": "one-sided (P1 higher)" if alt == "greater" else "two-sided (exploratory)",
                         "rate_a": k1 / n1, "rate_b": k2 / n2, "diff": d, "ci_lo": lo, "ci_hi": hi, "z": z, "p": p})
    df = pd.DataFrame(rows)
    if len(df):
        hyp = df["alternative"].str.startswith("one-sided")
        df["p_holm"] = np.nan
        for part in (hyp, ~hyp):
            if part.any():
                df.loc[part, "p_holm"] = stats.holm(df.loc[part, "p"])
        df["reject_h0"] = df["p_holm"] < alpha
    return df


# Chi-square tests of duplicate yes/no over all cells and per delivery count
def chi2_tests(cells: pd.DataFrame) -> pd.DataFrame:
    sub = cells[cells["injected_retries"] > 0]
    tables = [("path x multiplicity", sub)] + [(f"paths at multiplicity {m}", s) for m, s in sub.groupby("multiplicity")]
    rows = []
    for name, s in tables:
        t = [[r.dup_mutations, r.injected_retries - r.dup_mutations] for r in s.itertuples()]
        rows.append({"table": name, "cells": len(s), **stats.chi2_table(t)})
    return pd.DataFrame(rows)


# latency tests between each pair of write paths
def cont_tests(req: pd.DataFrame, metric: str, alpha: float, B: int, seed: int) -> pd.DataFrame:
    rows = []
    for m in sorted(req["multiplicity"].unique()):
        for a, b in PAIRS:
            x = req.loc[(req["path"] == a) & (req["multiplicity"] == m), metric].dropna()
            y = req.loc[(req["path"] == b) & (req["multiplicity"] == m), metric].dropna()
            if len(x) < 2 or len(y) < 2:
                continue
            rows.append({"metric": metric, "multiplicity": int(m), "comparison": f"{a} vs {b}",
                         **stats.compare(x, y, alpha=alpha, B=B, seed=seed)})
    df = pd.DataFrame(rows)
    if len(df):
        df["p_holm"] = stats.holm(df["p"])
        df["reject_h0"] = df["p_holm"] < alpha
    return df


# Turn the CI and point-estimate checks into a decision label
def _decide(ok: bool, point_ok: bool) -> str:
    return "supported" if ok else ("inconclusive (point estimate meets it, CI does not)" if point_ok else "not supported")


# Check expectations E1-E3 against the cell results
def expectations(cells: pd.DataFrame, req: pd.DataFrame, alpha: float, B: int = 2000, seed: int = 0) -> pd.DataFrame:
    c = cells.set_index(["path", "multiplicity"])
    rows = []
    retried = sorted(cells.loc[cells["injected_retries"] > 0, "multiplicity"].unique())
    for m in retried:  # E1: P1 duplicates on a majority of injected retries
        if ("P1", m) not in c.index:
            continue
        r = c.loc[("P1", m)]
        bt = st.binomtest(int(r["dup_mutations"]), int(r["injected_retries"]), 0.5, alternative="greater")
        ok = r["dup_ci_lo"] > 0.5 and r["dup_cluster_ci_lo"] > 0.5
        rows.append({"expectation": "E1", "multiplicity": int(m), "subject": "P1 duplicate rate",
                     "estimate": r["dup_rate"], "ci_lo": r["dup_ci_lo"], "ci_hi": r["dup_ci_hi"], "p": bt.pvalue,
                     "rule": "Wilson and cluster-bootstrap lower bounds > 0.5",
                     "decision": _decide(ok, r["dup_rate"] > 0.5)})
    for m in retried:  # E2: P2 and P3 cut the P1 rate by more than 90 %
        for g in ("P2", "P3"):
            if ("P1", m) not in c.index or (g, m) not in c.index:
                continue
            b, x = c.loc[("P1", m)], c.loc[(g, m)]
            red, lo, hi = stats.relative_reduction(int(b["dup_mutations"]), int(b["injected_retries"]),
                                                   int(x["dup_mutations"]), int(x["injected_retries"]), alpha)
            rows.append({"expectation": "E2", "multiplicity": int(m), "subject": f"{g} reduction vs P1",
                         "estimate": red, "ci_lo": lo, "ci_hi": hi, "p": np.nan,
                         "rule": "lower bound of the relative reduction > 0.90",
                         "decision": _decide(lo > 0.90, red > 0.90) if not np.isnan(red) else "not testable (P1 had no duplicates)"})
    for m in sorted(cells["multiplicity"].unique()):  # E3: P3 costs more capacity than P2
        x = req.loc[(req["path"] == "P3") & (req["multiplicity"] == m), "capacity_total"].dropna()
        y = req.loc[(req["path"] == "P2") & (req["multiplicity"] == m), "capacity_total"].dropna()
        if not len(x) or not len(y):
            continue
        # E3: the capacity difference is reported, not tested
        rows.append({"expectation": "E3", "multiplicity": int(m), "subject": "P3 - P2 capacity per request",
                     "estimate": float(x.mean() - y.mean()), "ci_lo": np.nan, "ci_hi": np.nan, "p": np.nan,
                     "rule": "reported as a count, not tested",
                     "decision": "reported, not tested"})
    return pd.DataFrame(rows)


# Count planned, missing and unexpected deliveries and other data checks
def checks(req: pd.DataFrame, dl: pd.DataFrame) -> pd.DataFrame:
    inj = dl[dl["inject"] == "after_commit"]
    items = [
        ("planned deliveries", int(req["multiplicity"].sum())),
        ("observed deliveries", len(dl)),
        ("missing deliveries", int(req["missing_deliveries"].sum())),
        ("deliveries with status error", int((dl["status"] == "error").sum())),
        ("after-commit injections that did not time out", int((inj["status"] != "timeout").sum())),
        ("deliveries with no function record (no capacity)", int(pd.to_numeric(dl["consumed_capacity"]).isna().sum())),
        ("requests with no business mutation", int(req["no_mutation"].sum())),
        ("requests where stream and self-report disagree", int(req["stream_self_mismatch"].sum())),
        ("final deliveries that were cold starts", int((req["cold_final"] == True).sum())),  # noqa: E712
        ("mutation ground truth", req["mutation_source"].iloc[0]),
    ]
    return pd.DataFrame(items, columns=["check", "value"])


DUP_COLS = ["path", "multiplicity", "requests", "injected_retries", "dup_mutations", "dup_rate", "dup_ci_lo",
            "dup_ci_hi", "dup_cluster_ci_lo", "dup_cluster_ci_hi", "dup_request_share",
            "dup_request_ci_lo", "dup_request_ci_hi", "ccf_per_retry", "successful_retry_rate"]
COST_COLS = ["path", "multiplicity", "capacity_mean", "capacity_mean_ci_lo", "capacity_mean_ci_hi",
             "capacity_rule_mean", "latency_mean_ms", "latency_mean_ms_ci_lo", "latency_mean_ms_ci_hi",
             "e2e_mean_ms", "e2e_mean_ms_ci_lo", "e2e_mean_ms_ci_hi",
             "latency_p95_ms", "latency_p95_ms_ci_lo", "latency_p95_ms_ci_hi", "latency_warm_mean_ms",
             "cold_final_share", "ddb_mean_ms"]
TEST_COLS = ["multiplicity", "comparison", "test", "estimate", "diff", "ci_lo", "ci_hi", "effect_name",
             "effect", "p", "p_holm", "reject_h0"]


# Run all tests and write the CSV tables and summary.md for one run
def analyse(evaluation, out, sensitivity=None, alpha: float = 0.05, B: int = 2000, seed: int = 0,
            sensitivity_out=None) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    gt, dl, st_, info = metrics.load_run(evaluation)
    tag = source_label(info.get("backend"))
    req = metrics.per_request(gt, dl, st_, info)
    cells = metrics.cell_summary(req, alpha, B, seed)
    dups, chi = dup_tests(cells, alpha), chi2_tests(cells)
    lat = cont_tests(req, "latency_ms", alpha, B, seed)  # capacity per request is a count: reported, not tested
    exp = expectations(cells, req, alpha, B, seed)
    chk = checks(req, dl)
    for name, df in (("requests", req), ("cells", cells), ("dup_tests", dups), ("chi2", chi),
                     ("latency_tests", lat), ("expectations", exp), ("checks", chk)):
        df.to_csv(out / f"{name}.csv", index=False, na_rep="N/A")
    sens_md = ["Not part of these runs."]
    if sensitivity:
        sg, sd, ss, sinfo = metrics.load_run(sensitivity)
        sreq = metrics.per_request(sg, sd, ss, sinfo)
        scells = metrics.cell_summary(sreq, alpha, B, seed)
        souts = sreq.groupby(["multiplicity", "final_outcome"]).size().rename("requests").reset_index()
        sout = Path(sensitivity_out) if sensitivity_out else out  # sensitivity tables in their own folder
        sout.mkdir(parents=True, exist_ok=True)
        scells.to_csv(sout / "sensitivity_cells.csv", index=False, na_rep="N/A")
        souts.to_csv(sout / "sensitivity_outcomes.csv", index=False, na_rep="N/A")
        sens_md = [f"Source: {source_label(sinfo.get('backend'))}. P3 only, timeout between the business write "
                   "and marking the key COMPLETED.", "", md_table(scells[DUP_COLS]), "", md_table(souts)]

    fam = lambda df: f"{len(df)} tests, Holm-Bonferroni within this family"  # noqa: E731
    md = [
        "# Evaluation analysis", "",
        "**N/A** means the metric is not applicable or was not computed. A recorded 0 is a measured zero.", "",
        f"- Source: **{tag}**",
        f"- Run: {info.get('t_start_utc', '?')}, {info.get('requests', '?')} requests, "
        f"{info.get('invocations', '?')} invocations, workers: {info.get('workers', '?')}",
        f"- alpha = {alpha}, bootstrap B = {B}, seed = {seed}", "",
        "## Data checks", "", md_table(chk), "",
        "## Duplicate mutation per injected retry (95 % Wilson and cluster-bootstrap CIs)", "",
        md_table(cells[DUP_COLS]), "",
        "### Two-proportion z-tests (4 one-sided and 2 exploratory tests, Holm-Bonferroni within each group)", "",
        md_table(dups) if len(dups) else "No retried cells.", "",
        "### Chi-square, duplicate yes/no by cell", "", md_table(chi), "",
        "## Capacity and latency per request (95 % bootstrap CIs)", "",
        "`latency_mean_ms` is the final invocation only. `e2e_mean_ms` sums every delivery's client round trip, including injected timeouts.", "",
        md_table(cells[COST_COLS]), "",
        f"### Latency tests ({fam(lat)})", "", md_table(lat[TEST_COLS]) if len(lat) else "-", "",
        "## Expectations stated before the runs (E1-E3)", "", md_table(exp), "",
        "## Sensitivity: timeout after P3's business-item write", "", *sens_md, ""]
    (out / "summary.md").write_text("\n".join(md))
    run = {"source": info.get("backend"), "evaluation": str(evaluation), "sensitivity": str(sensitivity or ""),
           "alpha": alpha, "B": B, "seed": seed}
    (out / "analysis_info.json").write_text(json.dumps(run, indent=2) + "\n")
    return {"cells": cells, "expectations": exp, "dup_tests": dups}


# Read the arguments and config, then run the analysis
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluation", required=True)
    ap.add_argument("--sensitivity")
    ap.add_argument("--out", required=True)
    ap.add_argument("--sensitivity-out", help="folder for the sensitivity tables (default: --out)")
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--config", default=str(ROOT / "config/experiment.yaml"))
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(open(args.config))
    res = analyse(args.evaluation, args.out, args.sensitivity, cfg["alpha"], args.bootstrap,
                  sensitivity_out=args.sensitivity_out)
    print(res["expectations"][["expectation", "multiplicity", "subject", "decision"]].to_string(index=False))
    print("->", Path(args.out) / "summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
