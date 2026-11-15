from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from driver.schedule import build, deliveries, write_ground_truth, write_schedule  # noqa: E402

FIELDS = ["request_id", "phase", "path", "multiplicity", "delivery", "inject", "status", "outcome", "wcu", "rcu",
          "wcu_ccf_rule", "consumed_capacity", "ccf", "calls", "business_writes", "latency_ms", "ddb_ms", "rtt_ms",
          "cold_start", "exec_id", "function_error", "resent_after", "t_start"]


# Last delivery record found in a Lambda log tail
def last_record(log_text: str) -> dict | None:
    for line in reversed(log_text.splitlines()):
        start = line.find('{"type": "delivery"')
        if start >= 0:
            try:
                return json.loads(line[start:].strip())
            except json.JSONDecodeError:
                continue
    return None


class LambdaBackend:
    source = "live"

    # Create a Lambda client with SDK retries off
    def __init__(self, function_name: str, region: str, workers: int = 1):
        import boto3
        from botocore.config import Config

        self.fn = function_name
        self.region = region
        # no SDK retries, a read timeout longer than the injected timeout, one connection per worker
        self._cfg = Config(connect_timeout=10, read_timeout=120, retries={"total_max_attempts": 1},
                           max_pool_connections=max(10, workers))
        self._boto3 = boto3
        self.lam = boto3.client("lambda", region_name=region, config=self._cfg)

    # Recreate the Lambda client
    def _reset_client(self) -> None:
        self.lam = self._boto3.client("lambda", region_name=self.region, config=self._cfg)

    # Invoke the function once and return status, record and round-trip time
    def invoke(self, event: dict) -> dict:
        # re-sends after throttling, a Lambda service error or a network error, and logs each re-send
        from botocore.exceptions import (
            ClientError,
            ConnectionClosedError,
            ConnectTimeoutError,
            EndpointConnectionError,
            ReadTimeoutError,
            SSLError,
        )
        transient = (SSLError, EndpointConnectionError, ConnectionClosedError,
                     ConnectTimeoutError, ReadTimeoutError, OSError)
        resend_codes = {"TooManyRequestsException", "ThrottlingException", "ServiceException"}
        last_exc: Exception | None = None
        resent_after: list[str] = []  # error before each re-send; logged with the delivery
        for attempt in range(8):
            t0 = time.perf_counter()
            try:
                resp = self.lam.invoke(FunctionName=self.fn, Payload=json.dumps(event).encode(), LogType="Tail")
                rtt = (time.perf_counter() - t0) * 1000
                body = json.loads(resp["Payload"].read() or b"null")
                tail = base64.b64decode(resp.get("LogResult") or b"").decode("utf-8", "replace")
                if resp.get("FunctionError"):
                    msg = body.get("errorMessage", "") if isinstance(body, dict) else ""
                    status = "timeout" if "timed out" in msg.lower() else "error"
                    return {"status": status, "record": last_record(tail), "rtt_ms": rtt, "function_error": msg[:200],
                            "resent_after": resent_after}
                return {"status": "ok", "record": body, "rtt_ms": rtt, "function_error": "", "resent_after": resent_after}
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code", "")
                if code not in resend_codes:
                    raise
                last_exc = exc
                resent_after.append(code)
                time.sleep(min(1.5 ** attempt, 20))
                self._reset_client()
            except transient as exc:
                last_exc = exc
                resent_after.append(type(exc).__name__)
                # Back off and recreate the HTTPS session.
                time.sleep(min(1.5 ** attempt, 20))
                self._reset_client()
        assert last_exc is not None
        raise last_exc


# The two things the handler reads from a Lambda context
class LocalContext:

    # Store a fake request id and the remaining time
    def __init__(self, remaining_ms: int = -1):
        self.aws_request_id = f"local-{uuid.uuid4()}"
        self.remaining_ms = remaining_ms

    # Remaining time in milliseconds, as in a Lambda context
    def get_remaining_time_in_millis(self) -> int:
        return self.remaining_ms


# The handler in this process (used with moto)
class LocalBackend:

    # Load the handler with the injected timeout raised as an exception
    def __init__(self, source: str = "local", remaining_ms: int = -1):
        os.environ["INJECT_MODE"] = "raise"
        from lambda_fn import handler

        self.h = handler
        self.source = source
        self.remaining_ms = remaining_ms

    # Run the handler in this process and return status, record and time
    def invoke(self, event: dict) -> dict:
        t0 = time.perf_counter()
        try:
            rec = self.h.lambda_handler(event, LocalContext(self.remaining_ms))
            return {"status": "ok", "record": rec, "rtt_ms": (time.perf_counter() - t0) * 1000, "function_error": ""}
        except self.h.InjectedTimeout as exc:
            return {"status": "timeout", "record": json.loads(str(exc)), "rtt_ms": (time.perf_counter() - t0) * 1000,
                    "function_error": "injected timeout"}


# Send warm-up waves and count cold starts
def warm_up(backend, workers: int, rounds: int) -> dict:
    calls = cold = 0
    for _ in range(rounds):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            res = list(pool.map(lambda _: backend.invoke({"warmup": True}), range(workers)))
        calls += len(res)
        cold += sum(bool((r["record"] or {}).get("cold_start")) for r in res)
    return {"calls": calls, "cold": cold}


# Run all requests of a phase and log every delivery to deliveries.jsonl
def run_phase(reqs: list[dict], backend, out: Path, max_invocations: int, workers: int = 1, warmup_rounds: int = 0,
              log=print, meta: dict | None = None) -> dict:
    out = Path(out)
    if (out / "deliveries.jsonl").exists():
        raise FileExistsError(f"{out} already has deliveries - use a new --out")
    planned = sum(r["multiplicity"] for r in reqs) + workers * warmup_rounds
    if planned > max_invocations:
        raise RuntimeError(f"{planned} invocations planned, budget allows {max_invocations}")
    write_schedule(reqs, out / "schedule.csv")  # both written before the first invoke
    write_ground_truth(reqs, out / "ground_truth.jsonl")
    warm = warm_up(backend, workers, warmup_rounds)
    lock = threading.Lock()
    fh = open(out / "deliveries.jsonl", "a", encoding="utf-8", buffering=1)
    t_start = time.time()
    done = [0]

    # Send every delivery of one request and log each result
    def one_request(req: dict) -> None:
        for d in deliveries(req):
            ev = {"request_id": req["request_id"], "path": req["path"], "delivery": d["delivery"],
                  "inject": d["inject"], "payload": req["payload"]}
            t = time.time()
            res = backend.invoke(ev)
            rec = res["record"] or {}
            row = {**rec, "request_id": req["request_id"], "phase": req["phase"], "path": req["path"],
                   "multiplicity": req["multiplicity"], "delivery": d["delivery"], "inject": d["inject"],
                   "status": res["status"], "rtt_ms": round(res["rtt_ms"], 3), "function_error": res["function_error"],
                   "resent_after": res.get("resent_after", []), "t_start": round(t, 3)}
            with lock:
                fh.write(json.dumps({k: row.get(k) for k in FIELDS}) + "\n")
                fh.flush()
                done[0] += 1

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(one_request, reqs))
    finally:
        fh.close()
    info = {"phase": reqs[0]["phase"] if reqs else None, "backend": backend.source, "requests": len(reqs),
            "invocations": done[0], "workers": workers, "warmup": warm, "t_start": t_start, "t_end": time.time(),
            "t_start_utc": dt.datetime.fromtimestamp(t_start, dt.timezone.utc).isoformat(timespec="seconds"),
            "versions": yaml.safe_load(open(ROOT / "config/versions.yaml")), **(meta or {})}
    (out / "run_info.json").write_text(json.dumps(info, indent=2) + "\n")
    log(f"{info['requests']} requests, {info['invocations']} invocations (+{warm['calls']} warm-up) -> {out}")
    return info


# Create the table with a stream and return the stream ARN
def create_local_table(client, name: str) -> str:
    client.create_table(TableName=name, KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
                        AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
                        BillingMode="PAY_PER_REQUEST",
                        StreamSpecification={"StreamEnabled": True, "StreamViewType": "NEW_AND_OLD_IMAGES"})
    return client.describe_table(TableName=name)["Table"]["LatestStreamArn"]


# True if the first requests' business items exist already
def ids_already_used(ddb, table: str, reqs: list[dict], k: int = 5) -> bool:
    for r in reqs[:k]:
        if ddb.get_item(TableName=table, Key={"pk": {"S": f"REQ#{r['request_id']}"}}).get("Item"):
            return True
    return False


# Build the requests and run a phase on Lambda, locally or on moto
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["pilot", "evaluation", "sensitivity"], required=True)
    ap.add_argument("--n", type=int, help="requests per cell (default: config)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--backend", choices=["lambda", "local"], default="lambda")
    ap.add_argument("--moto", action="store_true", help="local backend against in-memory DynamoDB (moto)")
    ap.add_argument("--workers", type=int, default=1, help="requests in parallel (Makefile WORKERS)")
    ap.add_argument("--seed", type=int, help="request-id seed (default: config)")
    ap.add_argument("--config", default=str(ROOT / "config/experiment.yaml"))
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(open(args.config))
    seed = args.seed if args.seed is not None else cfg["evaluation"]["seed"]
    reqs = build(cfg, args.phase, args.n, seed)
    out, cap, rounds = Path(args.out), cfg["budget"]["max_invocations"], cfg.get("warmup_rounds", 0)
    meta = {"seed": seed}
    if args.backend == "lambda":
        import boto3

        region = yaml.safe_load(open(ROOT / "config/versions.yaml"))["region"]
        if ids_already_used(boto3.client("dynamodb", region_name=region), cfg["table_name"], reqs):
            print("these request ids are already in the table - clear it (scripts/clear_table.py) or pass a new --seed", file=sys.stderr)
            return 2
        run_phase(reqs, LambdaBackend(cfg["function_name"], region, args.workers), out, cap, args.workers, rounds, meta=meta)
        print("next: python -m driver.streams --out", out, "(stream records expire after 24 h)")
        return 0
    if not args.moto:
        run_phase(reqs, LocalBackend(), out, cap, args.workers, rounds, meta=meta)
        return 0
    import boto3
    from moto import mock_aws

    from driver.streams import dump_stream

    for k, v in {"AWS_ACCESS_KEY_ID": "testing", "AWS_SECRET_ACCESS_KEY": "testing",
                 "AWS_DEFAULT_REGION": "eu-west-1", "TABLE_NAME": cfg["table_name"]}.items():
        os.environ[k] = v
    with mock_aws():
        arn = create_local_table(boto3.client("dynamodb", region_name="eu-west-1"), cfg["table_name"])
        run_phase(reqs, LocalBackend("moto"), out, cap, args.workers, rounds, meta=meta)
        n = dump_stream(boto3.client("dynamodbstreams", region_name="eu-west-1"), arn, out / "stream.jsonl", pause=0)
    print(f"{n} stream records -> {out / 'stream.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
