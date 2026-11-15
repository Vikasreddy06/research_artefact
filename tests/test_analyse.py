# The whole analysis on a small moto run
import pandas as pd

from analysis import analyse
from tests.conftest import moto_run


def test_analysis_end_to_end_on_moto(ddb, tmp_path):
    # 8 requests per cell
    moto_run(ddb, tmp_path / "evaluation", "evaluation", 8)
    moto_run(ddb, tmp_path / "sensitivity", "sensitivity", 3)
    out = tmp_path / "out"
    analyse.analyse(tmp_path / "evaluation", out, sensitivity=tmp_path / "sensitivity", B=200)
    for f in ("requests", "cells", "dup_tests", "chi2", "latency_tests", "expectations", "checks",
              "sensitivity_cells", "sensitivity_outcomes"):
        assert (out / f"{f}.csv").exists(), f
    summary = (out / "summary.md").read_text()
    assert "NOT an AWS measurement" in summary

    e = pd.read_csv(out / "expectations.csv")
    assert set(e["expectation"]) == {"E1", "E2", "E3"}
    assert e.query("expectation == 'E1' and multiplicity == 5")["decision"].iloc[0] == "supported"
    e3 = e.query("expectation == 'E3'")
    assert (e3["decision"] == "reported, not tested").all() and (e3["estimate"] > 0).all()  # 3 writes vs 1 on the first delivery
    d = pd.read_csv(out / "dup_tests.csv")
    t = d.dropna(subset=["p"])  # a test with both rates at 0 cannot be computed
    assert len(d) == 6 and t["p_holm"].ge(t["p"]).all()
    assert (pd.read_csv(out / "sensitivity_cells.csv")["dup_rate"] == 1.0).all()
    chk = pd.read_csv(out / "checks.csv").set_index("check")["value"]
    assert chk["missing deliveries"] == "0" or chk["missing deliveries"] == 0
