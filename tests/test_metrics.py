import numpy as np
import pandas as pd

from analysis import metrics
from tests.conftest import moto_run


def test_duplicates_are_counted_from_the_stream(ddb, tmp_path):
    gt, dl, st, _ = metrics.load_run(moto_run(ddb, tmp_path, "evaluation", 3))
    req = metrics.per_request(gt, dl, st)
    by = req.groupby(["path", "multiplicity"])["dup_mutations"].sum()
    assert by[("P1", 5)] == 12 and by[("P1", 2)] == 3 and by[("P1", 1)] == 0
    assert by[("P2", 5)] == 0 and by[("P3", 5)] == 0
    assert (req["mutation_source"] == "stream").all() and not req["stream_self_mismatch"].any()
    assert (req["missing_deliveries"] == 0).all() and not req["no_mutation"].any()


def test_self_report_fallback_gives_the_same_counts(ddb, tmp_path):
    gt, dl, st, _ = metrics.load_run(moto_run(ddb, tmp_path, "evaluation", 2))
    a, b = metrics.per_request(gt, dl, st), metrics.per_request(gt, dl, None)
    assert (b["mutation_source"] == "self_report").all()
    assert a["dup_mutations"].tolist() == b["dup_mutations"].tolist()


def test_cell_summary_rates_and_capacity(ddb, tmp_path):
    gt, dl, st, _ = metrics.load_run(moto_run(ddb, tmp_path, "evaluation", 3))
    c = metrics.cell_summary(metrics.per_request(gt, dl, st), B=200).set_index(["path", "multiplicity"])
    assert c.loc[("P1", 5), "dup_rate"] == 1.0 and c.loc[("P2", 5), "dup_rate"] == 0.0
    assert c.loc[("P2", 5), "ccf_per_retry"] == 1.0 and c.loc[("P3", 5), "successful_retry_rate"] == 1.0
    assert c.loc[("P2", 5), "capacity_rule_mean"] == 4.0  # four failed conditions, one unit each by rule
    assert np.isnan(c.loc[("P1", 1), "dup_rate"]) and np.isnan(c.loc[("P1", 1), "dup_request_share"])  # no retry
    # request-level Wilson keeps a non-zero width where every request has the same outcome
    assert c.loc[("P2", 5), "dup_request_share"] == 0 and c.loc[("P2", 5), "dup_request_ci_hi"] > 0
    assert c.loc[("P2", 5), "dup_cluster_ci_hi"] == 0.0
    assert c.loc[("P1", 5), "dup_request_share"] == 1.0 and c.loc[("P1", 5), "dup_request_ci_lo"] < 1.0


def test_timeout_between_writes_is_a_duplicate_for_p3(ddb, tmp_path):
    gt, dl, st, _ = metrics.load_run(moto_run(ddb, tmp_path, "sensitivity", 3))
    c = metrics.cell_summary(metrics.per_request(gt, dl, st), B=200).set_index(["path", "multiplicity"])
    assert c.loc[("P3", 2), "dup_rate"] == 1.0 and c.loc[("P3", 5), "dup_rate"] == 1.0


def test_a_lost_log_record_is_counted_not_hidden():
    gt = pd.DataFrame([{"request_id": "r", "phase": "evaluation", "path": "P1", "multiplicity": 2,
                        "inject_mode": "after_commit", "injected_retries": 1}])
    base = {"request_id": "r", "path": "P1", "multiplicity": 2, "ccf": 0, "wcu_ccf_rule": 0.0, "ddb_ms": 3.0,
            "cold_start": False, "outcome": "APPLIED"}
    dl = pd.DataFrame([{**base, "delivery": 1, "status": "timeout", "consumed_capacity": None, "business_writes": None,
                        "rtt_ms": 2100.0},
                       {**base, "delivery": 2, "status": "ok", "consumed_capacity": 1.0, "business_writes": 1,
                        "rtt_ms": 40.0}])
    req = metrics.per_request(gt, dl)
    assert req["lost_records"].iloc[0] == 1 and req["latency_ms"].iloc[0] == 40.0
    assert req["e2e_ms"].iloc[0] == 2140.0


def test_stream_events_outside_run_window_are_ignored():
    rid = "req-window-1"
    gt = pd.DataFrame([{
        "request_id": rid, "phase": "evaluation", "path": "P1", "multiplicity": 2,
        "inject_mode": "after_commit", "injected_retries": 1,
    }])
    dl = pd.DataFrame([
        {"request_id": rid, "delivery": 1, "multiplicity": 2, "status": "timeout",
         "consumed_capacity": 1.0, "wcu_ccf_rule": 0.0, "ccf": 0, "business_writes": 1,
         "rtt_ms": 100.0, "ddb_ms": 10.0, "cold_start": False, "outcome": "APPLIED"},
        {"request_id": rid, "delivery": 2, "multiplicity": 2, "status": "ok",
         "consumed_capacity": 1.0, "wcu_ccf_rule": 0.0, "ccf": 0, "business_writes": 1,
         "rtt_ms": 100.0, "ddb_ms": 10.0, "cold_start": False, "outcome": "APPLIED"},
    ])
    # two events outside the run window and two inside it, for the same request_id
    st = pd.DataFrame([
        {"kind": "business", "event": "INSERT", "request_id": rid, "approx_created_s": 1000.0},
        {"kind": "business", "event": "MODIFY", "request_id": rid, "approx_created_s": 1001.0},
        {"kind": "business", "event": "INSERT", "request_id": rid, "approx_created_s": 2000.0},
        {"kind": "business", "event": "MODIFY", "request_id": rid, "approx_created_s": 2001.0},
    ])
    info = {"t_start": 2000.0, "t_end": 2100.0}
    req = metrics.per_request(gt, dl, st, info).iloc[0]
    assert int(req["mutations"]) == 2, req["mutations"]
    assert int(req["dup_mutations"]) == 1, req["dup_mutations"]
    assert bool(req["stream_windowed"]) is True


def test_stream_events_from_unlogged_executions_are_ignored():
    rid = "req-exec-1"
    gt = pd.DataFrame([{
        "request_id": rid, "phase": "evaluation", "path": "P1", "multiplicity": 2,
        "inject_mode": "after_commit", "injected_retries": 1, "order": 0,
    }])
    dl = pd.DataFrame([
        {"request_id": rid, "delivery": 1, "multiplicity": 2, "status": "timeout",
         "consumed_capacity": 1.0, "wcu_ccf_rule": 0.0, "ccf": 0, "business_writes": 1,
         "rtt_ms": 100.0, "ddb_ms": 10.0, "cold_start": False, "outcome": "APPLIED",
         "exec_id": "exec-this-1"},
        {"request_id": rid, "delivery": 2, "multiplicity": 2, "status": "ok",
         "consumed_capacity": 1.0, "wcu_ccf_rule": 0.0, "ccf": 0, "business_writes": 1,
         "rtt_ms": 100.0, "ddb_ms": 10.0, "cold_start": False, "outcome": "APPLIED",
         "exec_id": "exec-this-2"},
    ])
    st = pd.DataFrame([
        {"kind": "business", "event": "INSERT", "request_id": rid, "approx_created_s": 2000.0, "exec_id": "exec-other-1"},
        {"kind": "business", "event": "MODIFY", "request_id": rid, "approx_created_s": 2001.0, "exec_id": "exec-other-2"},
        {"kind": "business", "event": "INSERT", "request_id": rid, "approx_created_s": 2002.0, "exec_id": "exec-this-1"},
        {"kind": "business", "event": "MODIFY", "request_id": rid, "approx_created_s": 2003.0, "exec_id": "exec-this-2"},
    ])
    info = {"t_start": 2000.0, "t_end": 2100.0}
    req = metrics.per_request(gt, dl, st, info).iloc[0]
    assert int(req["mutations"]) == 2, req["mutations"]
    assert int(req["dup_mutations"]) == 1


def test_a_stream_change_from_an_unlogged_execution_is_counted_not_hidden():
    gt = pd.DataFrame([{"request_id": "r", "phase": "evaluation", "path": "P1", "multiplicity": 2,
                        "inject_mode": "after_commit", "injected_retries": 1}])
    base = {"request_id": "r", "path": "P1", "multiplicity": 2, "ccf": 0, "wcu_ccf_rule": 0.0, "ddb_ms": 3.0,
            "cold_start": False, "outcome": "APPLIED", "consumed_capacity": 1.0, "business_writes": 1, "rtt_ms": 40.0}
    dl = pd.DataFrame([{**base, "delivery": 1, "status": "timeout", "exec_id": "e1"},
                       {**base, "delivery": 2, "status": "ok", "exec_id": "e2"}])
    st = pd.DataFrame([{"kind": "business", "event": e, "request_id": "r", "exec_id": x}
                       for e, x in [("INSERT", "e1"), ("MODIFY", "e2"), ("MODIFY", "e3")]])
    req = metrics.per_request(gt, dl, st).iloc[0]
    assert req["mutations"] == 2 and req["unlogged_mutations"] == 1
    assert req["dup_mutations"] == 1 and not req["dup_clamped"]
