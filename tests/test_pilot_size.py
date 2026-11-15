import numpy as np
import pandas as pd
import yaml

from analysis import pilot_size

CFG = yaml.safe_load(open("config/experiment.yaml"))


def pilot(cap_cv=0.0, n=50, seed=1):
    rng = np.random.default_rng(seed)
    cap = {"P1": 2.0, "P2": 2.0, "P3": 4.0}
    return pd.DataFrame([{"path": p, "injected_retries": 1, "dup_mutations": int(p == "P1"),
                          "capacity_total": rng.normal(cap[p], cap[p] * cap_cv)}
                         for p in cap for _ in range(n)])


def choose(req):
    return pilot_size.choose_n(pilot_size.sizing_table(req, CFG), CFG)


def test_quiet_pilot_keeps_the_configured_n():
    c = choose(pilot())
    assert c["N"] == 1000 and "meets" in c["reason"]


def test_noisy_capacity_raises_n():
    c = choose(pilot(cap_cv=1.0))
    assert 1000 < c["N"] <= c["budget_max_n"] and "capacity" in c["binding"]


def test_sizing_covers_duplicate_rate_and_capacity():
    assert set(pilot_size.sizing_table(pilot(), CFG)["metric"]) == {"duplicate rate", "capacity"}


def test_budget_caps_n():
    c = choose(pilot(cap_cv=5.0))
    assert c["N"] == c["budget_max_n"] == 2499 and "budget" in c["reason"]


def test_wilson_sizing():
    assert pilot_size.n_for_wilson(0.0, 0.01) == 189
    assert 9590 <= pilot_size.n_for_wilson(0.5, 0.01) <= 9610


def test_report_is_labelled(tmp_path):
    s = pilot_size.sizing_table(pilot(), CFG)
    text = pilot_size.write_report(s, pilot_size.choose_n(s, CFG), {"backend": "moto"}, CFG, tmp_path).read_text()
    assert "NOT an AWS measurement" in text
