import argparse
import pandas as pd
from pathlib import Path

REQ_COLS = [
    "Run ID",
    "Date/Time (local)",
    "Alerts processed",
    "Train alerts",
    "Tram/Light rail alerts",
    "Bus alerts",
    "Route names resolved (%)",
]

def validate_file(path: str) -> int:
    df = pd.read_csv(path)
    missing = [c for c in REQ_COLS if c not in df.columns]
    if missing:
        print(f"[FAIL] {path}: missing columns {missing}")
        return 1

    # Basic type checks
    for c in ["Alerts processed", "Train alerts", "Tram/Light rail alerts", "Bus alerts", "Route names resolved (%)"]:
        if not pd.api.types.is_numeric_dtype(df[c]):
            print(f"[FAIL] {path}: column not numeric -> {c}")
            return 1

    # Sanity checks
    bad_rows = df[
        (df["Route names resolved (%)"] < 0) | (df["Route names resolved (%)"] > 100)
    ]
    if len(bad_rows):
        print(f"[FAIL] {path}: route resolution out of [0,100] in {len(bad_rows)} row(s)")
        return 1

    # (Optional) If you're in "exclusive mode counts", ensure the three modes sum to total
    sums = df["Train alerts"] + df["Tram/Light rail alerts"] + df["Bus alerts"]
    mismatch = (sums != df["Alerts processed"])
    if mismatch.any():
        n = mismatch.sum()
        print(f"[FAIL] {path}: {n} row(s) where Train+Tram+Bus != Alerts processed")
        return 1

    print(f"[OK] {path}")
    return 0

def main():
    ap = argparse.ArgumentParser(description="Validate summary CSVs.")
    ap.add_argument("paths", nargs="+", help="Paths to _runs_summary_*.csv")
    args = ap.parse_args()

    rc = 0
    for p in args.paths:
        rc |= validate_file(p)
    raise SystemExit(rc)

if __name__ == "__main__":
    main()
