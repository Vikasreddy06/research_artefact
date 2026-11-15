#!/usr/bin/env python
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CHUNK = dt.timedelta(minutes=1440)  # GetMetricStatistics returns at most 1440 points per call


# Sum a CloudWatch metric over a time window, one day per GetMetricStatistics query
def metric_sum(cw, namespace: str, name: str, dims: dict, start: dt.datetime, end: dt.datetime) -> float:
    total, t = 0.0, start
    while t < end:
        stop = min(t + CHUNK, end)
        resp = cw.get_metric_statistics(Namespace=namespace, MetricName=name, StartTime=t, EndTime=stop, Period=60,
                                        Dimensions=[{"Name": k, "Value": v} for k, v in dims.items()],
                                        Statistics=["Sum"])
        total += sum(p["Sum"] for p in resp["Datapoints"])
        t = stop
    return float(total)


# Totals of deliveries, errors and capacity logged by the driver in a window
def driver_totals(run: Path, start: dt.datetime, end: dt.datetime) -> dict:
    dl = pd.read_json(run / "deliveries.jsonl", lines=True)
    dl = dl[(dl["t_start"] >= start.timestamp()) & (dl["t_start"] < end.timestamp())]
    return {"deliveries": len(dl),
            "timeouts": int((dl["status"] == "timeout").sum()), "errors": int((dl["status"] == "error").sum()),
            "wcu_reported": float(dl["wcu"].fillna(0).sum()), "wcu_rule": float(dl["wcu_ccf_rule"].fillna(0).sum()),
            "rcu_reported": float(dl["rcu"].fillna(0).sum())}


# Compare CloudWatch totals with the driver's own totals for one run
def cross_check(cw, run: Path, table: str, function: str) -> dict:
    info = json.loads((run / "run_info.json").read_text())
    # whole minutes inside the run: the first full minute after the start, up to the last minute boundary
    start = dt.datetime.fromtimestamp(info["t_start"] // 60 * 60 + 60, dt.timezone.utc)
    end = dt.datetime.fromtimestamp(info["t_end"] // 60 * 60, dt.timezone.utc)
    cwt = {
        "wcu": metric_sum(cw, "AWS/DynamoDB", "ConsumedWriteCapacityUnits", {"TableName": table}, start, end),
        "rcu": metric_sum(cw, "AWS/DynamoDB", "ConsumedReadCapacityUnits", {"TableName": table}, start, end),
        "invocations": metric_sum(cw, "AWS/Lambda", "Invocations", {"FunctionName": function}, start, end),
        "errors": metric_sum(cw, "AWS/Lambda", "Errors", {"FunctionName": function}, start, end),
    }
    d = driver_totals(run, start, end)
    return {"window_utc": [start.isoformat(), end.isoformat()], "cloudwatch": cwt, "driver": d, "compare": {
        "wcu_cloudwatch_minus_reported": cwt["wcu"] - d["wcu_reported"],
        "wcu_cloudwatch_minus_reported_plus_rule": cwt["wcu"] - d["wcu_reported"] - d["wcu_rule"],
        "invocations_minus_driver": cwt["invocations"] - d["deliveries"],
        "errors_minus_timeouts_and_errors": cwt["errors"] - d["timeouts"] - d["errors"]}}


# Run the CloudWatch cross-check and save it as cloudwatch.json
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    args = ap.parse_args(argv)
    import boto3

    cfg = yaml.safe_load(open(ROOT / "config/experiment.yaml"))
    region = yaml.safe_load(open(ROOT / "config/versions.yaml"))["region"]
    res = cross_check(boto3.client("cloudwatch", region_name=region), Path(args.run), cfg["table_name"],
                      cfg["function_name"])
    (Path(args.run) / "cloudwatch.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res["compare"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
