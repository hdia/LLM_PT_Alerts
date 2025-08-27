import argparse, json, os
import pandas as pd
from pathlib import Path

def load_yaml(path):
    try:
        import yaml
    except ImportError:
        raise SystemExit("Please `pip install pyyaml` to use compute_averages.py")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def compute(city_name, csv_path):
    df = pd.read_csv(csv_path)
    # Expect columns used in paper
    cols = [
        "Alerts processed",
        "Train alerts",
        "Tram/Light rail alerts",
        "Bus alerts",
        "Route names resolved (%)",
    ]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{city_name}: missing columns: {missing}")
    avg = {
        "City": city_name,
        "Avg alerts processed": round(df["Alerts processed"].mean(), 1),
        "Avg train alerts": round(df["Train alerts"].mean(), 1),
        "Avg tram/light rail alerts": round(df["Tram/Light rail alerts"].mean(), 1),
        "Avg bus alerts": round(df["Bus alerts"].mean(), 1),
        "Avg route names resolved (%)": round(df["Route names resolved (%)"].mean(), 1),
    }
    return avg

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="config/settings.yaml")
    args = ap.parse_args()

    cfg = load_yaml(args.settings)
    paths = cfg["summaries"]
    Path("results/tables").mkdir(parents=True, exist_ok=True)

    rows = []
    rows.append(compute("Melbourne", paths["mel_summary"]))
    rows.append(compute("Sydney", paths["syd_summary"]))
    rows.append(compute("SEQ", paths["seq_summary"]))

    out = pd.DataFrame(rows)
    out.to_csv(paths["averages_out"], index=False)
    print(f"Wrote {paths['averages_out']}")
    print(out.to_string(index=False))

if __name__ == "__main__":
    main()
