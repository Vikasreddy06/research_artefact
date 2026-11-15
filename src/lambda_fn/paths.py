from __future__ import annotations

import json
import math
import time

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError

CCF = "ConditionalCheckFailedException"
_SER, _DES = TypeSerializer(), TypeDeserializer()


# Convert a plain dict to DynamoDB typed attributes
def typed(d: dict) -> dict:
    return {k: _SER.serialize(v) for k, v in d.items()}


# Convert DynamoDB typed attributes to a plain dict
def plain(d: dict) -> dict:
    return {k: _DES.deserialize(v) for k, v in d.items()}


# Approximate item size in bytes
def item_bytes(item: dict) -> int:
    size = 0
    for k, v in item.items():
        if isinstance(v, bool) or v is None:
            size += len(k) + 1
        elif isinstance(v, int | float):
            size += len(k) + (len(str(abs(v)).replace(".", "")) + 1) // 2 + 1
        else:
            size += len(k) + len(str(v).encode("utf-8"))
    return size


# Write units of an item, one per started KB
def write_units(item: dict) -> float:
    return float(max(1, math.ceil(item_bytes(item) / 1024)))


# Capacity units reported in a DynamoDB response
def _cc(resp: dict) -> float:
    return float((resp.get("ConsumedCapacity") or {}).get("CapacityUnits", 0.0))


# Business item of a payment request for one delivery
def business_item(request_id: str, payload: dict, exec_id: str, delivery: int) -> dict:
    # exec_id differs on every delivery
    return {"pk": f"REQ#{request_id}", "request_id": request_id, **payload, "exec_id": exec_id,
            "delivery": int(delivery), "written_at_ms": int(time.time() * 1000)}


# Result dict with zero defaults and the given fields
def _result(outcome: str, **kw) -> dict:
    base = {"outcome": outcome, "rcu": 0.0, "wcu": 0.0, "wcu_ccf_rule": 0.0, "ccf": 0, "calls": 0,
            "business_writes": 0}
    base.update(kw)
    return base


# P1: plain write of the business item
def p1(client, table, request_id, payload, exec_id, delivery, **_):
    item = business_item(request_id, payload, exec_id, delivery)
    resp = client.put_item(TableName=table, Item=typed(item), ReturnConsumedCapacity="TOTAL")
    return _result("APPLIED", wcu=_cc(resp), calls=1, business_writes=1)


# P2: conditional write that fails if the item already exists
def p2(client, table, request_id, payload, exec_id, delivery, **_):
    item = business_item(request_id, payload, exec_id, delivery)
    try:
        resp = client.put_item(TableName=table, Item=typed(item), ConditionExpression="attribute_not_exists(pk)",
                               ReturnConsumedCapacity="TOTAL")
        return _result("APPLIED", wcu=_cc(resp), calls=1, business_writes=1)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != CCF:
            raise
        reported = _cc(exc.response)
        return _result("SUPPRESSED", wcu=reported, wcu_ccf_rule=0.0 if reported else write_units(item), ccf=1, calls=1)


# P3: claim an idempotency key, write the item, then mark the key completed
def p3(client, table, request_id, payload, exec_id, delivery, now_ms, in_progress_until_ms, ttl_s=3600,
       between=None, **_):
    now_s = now_ms // 1000
    key = {"pk": f"IDEMP#{request_id}", "status": "IN_PROGRESS", "in_progress_expiry": int(in_progress_until_ms),
           "expiry": int(now_s + ttl_s), "owner": exec_id}
    try:
        r = client.put_item(
            TableName=table, Item=typed(key),
            ConditionExpression="attribute_not_exists(pk) OR (#s = :inprog AND in_progress_expiry < :now) OR #e < :now_s",
            ExpressionAttributeNames={"#s": "status", "#e": "expiry"},
            ExpressionAttributeValues={":inprog": {"S": "IN_PROGRESS"}, ":now": {"N": str(int(now_ms))},
                                       ":now_s": {"N": str(int(now_s))}},
            ReturnValuesOnConditionCheckFailure="ALL_OLD", ReturnConsumedCapacity="TOTAL")
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != CCF:
            raise
        old = plain(exc.response.get("Item", {}))
        reported = _cc(exc.response)
        rule = 0.0 if reported else write_units(old)
        if old.get("status") == "COMPLETED":
            return _result("REPLAYED", wcu=reported, wcu_ccf_rule=rule, ccf=1, calls=1,
                           replayed_result=json.loads(old.get("result", "{}")))
        return _result("REJECTED_IN_PROGRESS", wcu=reported, wcu_ccf_rule=rule, ccf=1, calls=1)
    wcu = _cc(r)
    item = business_item(request_id, payload, exec_id, delivery)
    r = client.put_item(TableName=table, Item=typed(item), ReturnConsumedCapacity="TOTAL")
    wcu += _cc(r)
    if between is not None:  # sensitivity case: crash after the business write, key still IN_PROGRESS
        between(_result("CRASH_BETWEEN", wcu=wcu, calls=2, business_writes=1))
    result = {"request_id": request_id, "applied_by": exec_id}
    r = client.update_item(
        TableName=table, Key=typed({"pk": key["pk"]}),
        UpdateExpression="SET #s = :done, #r = :res, #e = :exp",
        ExpressionAttributeNames={"#s": "status", "#r": "result", "#e": "expiry"},
        ExpressionAttributeValues={":done": {"S": "COMPLETED"}, ":res": {"S": json.dumps(result)},
                                   ":exp": {"N": str(int(now_s + ttl_s))}},
        ReturnConsumedCapacity="TOTAL")
    wcu += _cc(r)
    return _result("APPLIED", wcu=wcu, calls=3, business_writes=1)


PATHS = {"P1": p1, "P2": p2, "P3": p3}


# Run the chosen write path and add its DynamoDB time
def run(path: str, client, table: str, request_id: str, payload: dict, exec_id: str, delivery: int, **kw) -> dict:
    if path not in PATHS:
        raise ValueError(f"unknown path {path}")
    t0 = time.perf_counter()
    res = PATHS[path](client, table, request_id, payload, exec_id, delivery, **kw)
    res["ddb_ms"] = round((time.perf_counter() - t0) * 1000, 3)
    return res
