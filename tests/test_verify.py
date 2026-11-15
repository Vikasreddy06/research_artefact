import importlib.util
from pathlib import Path

import pandas as pd

spec = importlib.util.spec_from_file_location("verify", Path(__file__).resolve().parents[1] / "scripts/verify_evaluation_run.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


def test_schedule_deviations():
    dl = pd.DataFrame({"inject": ["after_commit", "none", "after_commit", "none"],
                       "status": ["timeout", "ok", "ok", "timeout"]})
    assert verify.schedule_deviations(dl) == (1, 1)  # one final delivery timed out; one injection did not
    assert verify.schedule_deviations(dl.iloc[:2]) == (0, 0)
