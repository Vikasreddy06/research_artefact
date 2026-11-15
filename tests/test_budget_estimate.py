import yaml

from scripts import budget_estimate

CFG = yaml.safe_load(open("config/experiment.yaml"))


def test_write_units_per_request():
    assert budget_estimate.write_units("P1", 5, "after_commit") == 5
    assert budget_estimate.write_units("P2", 5, "after_commit") == 5  # failed conditions counted at one unit each by rule
    assert budget_estimate.write_units("P3", 1, "after_commit") == 3
    assert budget_estimate.write_units("P3", 5, "after_commit") == 7
    assert budget_estimate.write_units("P3", 5, "p3_between") == 11


def test_evaluation_counts():
    c = budget_estimate.phase_counts(CFG, "evaluation", 1000)
    assert c["requests"] == 9000 and c["invocations"] == 24000
    assert c["timeouts"] == 15000 and c["wru"] == 30000


def test_three_evaluation_runs_and_each_run_fits_the_cap():
    rows, total = budget_estimate.estimate(CFG, 1000)
    ev = next(r for r in rows if r["phase"].startswith("evaluation"))
    assert ev["invocations"] == 3 * 24000 and total > 0
    assert budget_estimate.largest_run(CFG, 1000) <= CFG["budget"]["max_invocations"]
