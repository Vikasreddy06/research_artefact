# The driver on in-memory DynamoDB (moto)
import json

import pytest
import yaml

from driver import run, schedule
from tests.conftest import TABLE

CFG = yaml.safe_load(open("config/experiment.yaml"))
QUIET = {"log": lambda *_: None}


def rows(folder):
    return [json.loads(line) for line in (folder / "deliveries.jsonl").read_text().splitlines()]


def test_record_is_found_in_a_lambda_log_tail():
    tail = ("START RequestId: abc Version: $LATEST\n"
            '2026-01-01T00:00:00.000Z\tabc\tINFO\t{"type": "delivery", "request_id": "r", "wcu": 1.0}\n'
            "2026-01-01T00:00:03.100Z abc Task timed out after 3.00 seconds\nEND RequestId: abc\n")
    assert run.last_record(tail)["wcu"] == 1.0
    assert run.last_record("Task timed out after 2.00 seconds") is None


def test_every_delivery_is_logged_with_its_capacity(ddb, tmp_path):
    reqs = schedule.build(CFG, "evaluation", n_per_cell=2)
    info = run.run_phase(reqs, run.LocalBackend("moto"), tmp_path, max_invocations=1000, warmup_rounds=1, **QUIET)
    got = rows(tmp_path)
    assert len(got) == sum(r["multiplicity"] for r in reqs) == info["invocations"]
    assert info["warmup"] == {"calls": 1, "cold": 1}
    assert (tmp_path / "ground_truth.jsonl").exists() and (tmp_path / "schedule.csv").exists()
    assert {r["status"] for r in got if r["inject"] == "after_commit"} == {"timeout"}
    assert {r["status"] for r in got if r["inject"] == "none"} == {"ok"}
    assert all(r["consumed_capacity"] is not None for r in got)  # kept for timed-out deliveries too


def test_final_outcomes_per_path(ddb, tmp_path):
    reqs = schedule.build(CFG, "evaluation", n_per_cell=2)
    run.run_phase(reqs, run.LocalBackend("moto"), tmp_path, max_invocations=1000, **QUIET)
    final = {(r["path"], r["multiplicity"]): r["outcome"] for r in rows(tmp_path) if r["delivery"] == r["multiplicity"]}
    assert final[("P1", 5)] == "APPLIED" and final[("P2", 5)] == "SUPPRESSED" and final[("P3", 5)] == "REPLAYED"
    assert {final[(p, 1)] for p in ("P1", "P2", "P3")} == {"APPLIED"}


def test_budget_is_checked_before_anything_is_written(ddb, tmp_path):
    reqs = schedule.build(CFG, "pilot", n_per_cell=2)
    with pytest.raises(RuntimeError):
        run.run_phase(reqs, run.LocalBackend(), tmp_path / "a", max_invocations=3, **QUIET)
    assert not (tmp_path / "a").exists()


def test_reused_request_ids_are_detected(ddb, tmp_path):
    reqs = schedule.build(CFG, "pilot", n_per_cell=2)
    assert not run.ids_already_used(ddb, TABLE, reqs)
    run.run_phase(reqs, run.LocalBackend(), tmp_path, max_invocations=100, **QUIET)
    assert run.ids_already_used(ddb, TABLE, reqs)  # same seed again -> refused by main()
    assert not run.ids_already_used(ddb, TABLE, schedule.build(CFG, "pilot", n_per_cell=2, seed=7))


def test_a_run_folder_is_never_reused(ddb, tmp_path):
    reqs = schedule.build(CFG, "pilot", n_per_cell=1)
    run.run_phase(reqs, run.LocalBackend(), tmp_path, max_invocations=100, **QUIET)
    with pytest.raises(FileExistsError):
        run.run_phase(reqs, run.LocalBackend(), tmp_path, max_invocations=100, **QUIET)


def test_a_driver_resend_is_logged_with_the_error_before_it(monkeypatch):
    import io

    from botocore.exceptions import ConnectionClosedError

    replies = iter([ConnectionClosedError(endpoint_url="x"), {"Payload": io.BytesIO(b'{"outcome": "APPLIED"}')}])

    class Lam:
        def invoke(self, **_):
            r = next(replies)
            if isinstance(r, Exception):
                raise r
            return r

    backend = run.LambdaBackend.__new__(run.LambdaBackend)
    backend.fn, backend.lam, backend._reset_client = "fn", Lam(), lambda: None
    monkeypatch.setattr(run.time, "sleep", lambda _: None)
    res = backend.invoke({})
    assert res["status"] == "ok" and res["resent_after"] == ["ConnectionClosedError"]


def test_connection_pool_grows_with_the_workers():
    assert run.LambdaBackend("fn", "eu-west-1")._cfg.max_pool_connections == 10
    assert run.LambdaBackend("fn", "eu-west-1", workers=900)._cfg.max_pool_connections == 900


def test_clear_table_leaves_no_item(ddb, tmp_path, monkeypatch):
    from scripts import clear_table
    for i in range(60):
        ddb.put_item(TableName=TABLE, Item={"pk": {"S": f"REQ#{i}"}})
    cfg = tmp_path / "experiment.yaml"
    cfg.write_text(yaml.safe_dump({**CFG, "table_name": TABLE}))
    monkeypatch.setattr("sys.argv", ["clear_table", "--config", str(cfg)])
    assert clear_table.main() == 0
    assert ddb.scan(TableName=TABLE)["Count"] == 0
