from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd
import yaml
from scipy import stats as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis import metrics, stats  # noqa: E402
from analysis.tables import md_table, source_label  # noqa: E402


# Smallest n whose Wilson interval half-width is within the target
def n_for_wilson(p_hat: float, half_width: float, alpha: float = 0.05, n_max: int = 10_000_000) -> int:
    # Half-width of the Wilson interval at n
    def half(n: int) -> float:
        _, lo, hi = stats.wilson(p_hat * n, n, alpha)
        return (hi - lo) / 2

    if half(n_max) > half_width:
        return n_max
    lo, hi = 1, n_max
    while lo < hi:
        mid = (lo + hi) // 2
        if half(mid) <= half_width:
            hi = mid
        else:
            lo = mid + 1
    return lo


# Upper confidence bound of a standard deviation
def sd_upper(sd: float, n: int, alpha: float = 0.05) -> float:
    return sd * math.sqrt((n - 1) / st.chi2.ppf(alpha / 2, n - 1)) if n > 1 else float("nan")


# Required requests per cell for each path and metric, from the pilot
def sizing_table(req: pd.DataFrame, cfg: dict, alpha: float = 0.05) -> pd.DataFrame:
    pr = cfg["practical"]
    hw = pr["duplicate_rate_pp"] / 100
    rows = []
    for path, g in req.groupby("path"):
        retries, dups = int(g["injected_retries"].sum()), int(g["dup_mutations"].sum())
        if retries:
            p, lo, hi = stats.wilson(dups, retries, alpha)
            p_cons = lo if lo > 0.5 else hi if hi < 0.5 else 0.5
            rows.append({"path": path, "metric": "duplicate rate", "pilot_n": retries, "mean": p,
                         "sd": math.sqrt(p * (1 - p)), "target": f"+-{pr['duplicate_rate_pp']} pp",
                         "required_n": n_for_wilson(p, hw, alpha),
                         "conservative_n": stats.n_for_proportion(p_cons, hw, alpha)})
        x, pct = g["capacity_total"].dropna().astype(float), pr["capacity_pct"]
        if len(x) >= 2:
            m, sd = float(x.mean()), float(x.std(ddof=1))
            rows.append({"path": path, "metric": "capacity", "pilot_n": len(x), "mean": m, "sd": sd,
                         "target": f"+-{pct} % of mean", "required_n": stats.n_for_mean(sd, m, pct, alpha),
                         "conservative_n": stats.n_for_mean(sd_upper(sd, len(x), alpha), m, pct, alpha)})
    return pd.DataFrame(rows)


# Largest N whose evaluation run, warm-up included, stays within the driver's per-run cap
def budget_max_n(cfg: dict, workers: int = 1) -> int:
    per_n = len(cfg["paths"]) * sum(cfg["multiplicities"])
    warm = workers * cfg.get("warmup_rounds", 0)  # Makefile WORKERS
    return int((cfg["budget"]["max_invocations"] - warm) // per_n)


# Pick N from the configured size, the pilot requirement and the budget cap
def choose_n(sizing: pd.DataFrame, cfg: dict, workers: int = 1) -> dict:
    size = cfg["evaluation"]["requests_per_cell"]
    need = int(sizing["required_n"].max())
    top = sizing.loc[sizing["required_n"].idxmax()]
    cap = budget_max_n(cfg, workers)
    if need <= size:
        n, why = size, f"the configured size meets the pilot requirement (largest requirement {need} <= {size})"
    elif need <= cap:
        n, why = need, f"the pilot requires more than the configured size {size}"
    else:
        n, why = cap, f"capped by the invocation budget ({cap}); evaluation CIs will be wider than the target"
    return {"N": int(n), "required": need, "binding": f"{top['path']} {top['metric']}", "configured": size,
            "budget_max_n": cap, "reason": why}


# Write the pilot report in Markdown
def write_report(sizing: pd.DataFrame, choice: dict, info: dict, cfg: dict, out: str | Path) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    pr = cfg["practical"]
    lines = [
        "# Pilot report", "",
        f"- Source: **{source_label(info.get('backend'))}**",
        f"- Pilot run: {info.get('t_start_utc', '?')}, {info.get('requests', '?')} requests, "
        f"{info.get('invocations', '?')} invocations, multiplicity {cfg['pilot']['multiplicity']}", "",
        "## Rule (fixed before the pilot)", "",
        f"- duplicate-mutation rate: 95 % Wilson interval no wider than +-{pr['duplicate_rate_pp']} pp",
        f"- capacity per request: 95 % CI half-width at most {pr['capacity_pct']} % of the mean",
        f"- N = largest requirement; at least the configured size {choice['configured']}; at most "
        f"{choice['budget_max_n']} (invocation budget {cfg['budget']['max_invocations']})", "",
        "## Pilot estimates and required N", "",
        md_table(sizing), "",
        "`conservative_n` uses the pessimistic end of the pilot's own 95 % interval. "
        "The decision uses `required_n`.", "",
        "## Decision", "",
        f"**N = {choice['N']} requests per path per multiplicity** - {choice['reason']}. "
        f"Binding requirement: {choice['binding']} ({choice['required']}).", ""]
    path = out / "pilot_report.md"
    path.write_text("\n".join(lines))
    return path


# Size the evaluation from a pilot run and write the choice and report
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="pilot run folder")
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=str(ROOT / "config/experiment.yaml"))
    ap.add_argument("--workers", type=int, default=1, help="workers of the evaluation runs (Makefile WORKERS)")
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(open(args.config))
    gt, dl, st_, info = metrics.load_run(args.run)
    sizing = sizing_table(metrics.per_request(gt, dl, st_, info), cfg, cfg["alpha"])
    choice = choose_n(sizing, cfg, args.workers)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sizing.to_csv(out / "pilot_sizing.csv", index=False, na_rep="N/A")
    (out / "pilot_choice.json").write_text(json.dumps({**choice, "source": info.get("backend")}, indent=2) + "\n")
    print(write_report(sizing, choice, info, cfg, out), "->", f"N = {choice['N']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
