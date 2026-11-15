#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from pathlib import Path

import boto3
import yaml

ROOT = Path(__file__).resolve().parents[1]

# Delete every item from the experiment table
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config/experiment.yaml"))
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))
    region = yaml.safe_load(open(ROOT / "config/versions.yaml"))["region"]
    table = cfg["table_name"]
    ddb = boto3.client("dynamodb", region_name=region)
    deleted = 0
    # scan again until a consistent scan finds nothing left
    for _ in range(10):
        found, ek = 0, None
        while True:
            kw = {"TableName": table, "ProjectionExpression": "pk", "ConsistentRead": True}
            if ek:
                kw["ExclusiveStartKey"] = ek
            resp = ddb.scan(**kw)
            items = resp.get("Items", [])
            for i in range(0, len(items), 25):
                todo = {table: [{"DeleteRequest": {"Key": {"pk": it["pk"]}}} for it in items[i:i+25]]}
                # retry deletes DynamoDB did not process
                while todo:
                    todo = ddb.batch_write_item(RequestItems=todo).get("UnprocessedItems") or None
                    if todo:
                        time.sleep(0.5)
            found += len(items)
            ek = resp.get("LastEvaluatedKey")
            if not ek:
                break
        deleted += found
        if not found:
            print(f"cleared {deleted} items from {table}")
            return 0
    print(f"items still left in {table} after 10 passes")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
