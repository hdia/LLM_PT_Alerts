import os
import pandas as pd

REQ_COLS = [
    "Run ID",
    "Date/Time (local)",
    "Alerts processed",
    "Train alerts",
    "Tram/Light rail alerts",
    "Bus alerts",
    "Route names resolved (%)",
]

def test_sample_summaries_exist():
    # These are the default paths from settings.yaml (results you ship as examples)
    paths = [
        "results/tables/_runs_summary_MEL.csv",
        "results/tables/_runs_summary_SYD.csv",
        "results/tables/_runs_summary_SEQ.csv",
    ]
    for p in paths:
        assert os.path.exists(p), f"Missing example summary: {p}"

def test_columns_present_and_types():
    for p in [
        "results/tables/_runs_summary_MEL.csv",
        "results/tables/_runs_summary_SYD.csv",
        "results/tables/_runs_summary_SEQ.csv",
    ]:
        df = pd.read_csv(p)
        for c in REQ_COLS:
            assert c in df.columns, f"{p} missing column {c}"
        assert df["Alerts processed"].dtype.kind in "if"
        assert df["Route names resolved (%)"].dtype.kind in "if"
