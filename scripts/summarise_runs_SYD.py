#! python summarise_runs_syd.py "out\syd_alerts_translated_*.csv"
#!/usr/bin/env python3
# summarise_runs_syd.py
import sys, glob, os, re
import pandas as pd

ROUTES_TXT = "config/routes.txt" # static GTFS routes in working directory

# ---------- Load routes ----------
def load_routes(routes_path: str):
    if not os.path.exists(routes_path):
        raise FileNotFoundError(f"Could not find {routes_path}. Place GTFS routes.txt in the working directory.")
    r = pd.read_csv(routes_path, dtype=str).fillna("")
    r["route_id_norm"] = r["route_id"].str.strip().str.lower()
    r["short_norm"] = r.get("route_short_name", pd.Series([""] * len(r))).str.strip().str.lower()
    r["long_norm"]  = r.get("route_long_name", pd.Series([""] * len(r))).str.strip().str.lower()
    return {
        "short_set": set(x for x in r["short_norm"].tolist() if x),
        "id_set":    set(x for x in r["route_id_norm"].tolist() if x),
        "long_list": r["long_norm"].tolist(),
    }

# ---------- Route resolution (deterministic; SYD-aware) ----------
CODE_PAT = re.compile(r"\b([tlm])\s*([1-9])\b", re.I)
BUS_PAT  = re.compile(r"\broute\s*([a-z]?\d{1,4})\b|\b([a-z]?\d{1,4})\b", re.I)
LONG_FRAGMENTS = [
    "western line", "eastern suburbs", "inner west", "airport line",
    "blue mountains", "south coast", "central coast", "hunter line"
]

def compute_route_resolved_mask(df: pd.DataFrame, routes_idx: dict) -> pd.Series:
    n = len(df)
    resolved = pd.Series([False] * n, index=df.index)

    # 1) route_short_name present
    if "route_short_name" in df.columns:
        resolved |= df["route_short_name"].fillna("").str.strip().ne("")

    # 2) route_id exact match from routes.txt
    if "route_id" in df.columns:
        rid = df["route_id"].fillna("").str.strip().str.lower()
        resolved |= rid.isin(routes_idx["id_set"])

    # 3) Text extraction against GTFS identifiers
    text_cols = [c for c in ["summary_en", "plain_en", "text"] if c in df.columns]
    if text_cols:
        text = df[text_cols].astype(str).agg(" ".join, axis=1).str.lower()

        def text_resolved(s: str) -> bool:
            # Line codes (T, L, M)
            for m in CODE_PAT.finditer(s):
                token = f"{m.group(1).lower()}{m.group(2)}"
                if token in routes_idx["short_set"]:
                    return True
            # Named lines in route_long_name
            for frag in LONG_FRAGMENTS:
                if frag in s and any(frag in ln for ln in routes_idx["long_list"]):
                    return True
            # Bus codes
            for m in BUS_PAT.finditer(s):
                token = (m.group(1) or m.group(2) or "").strip().lower()
                if token and token in routes_idx["short_set"]:
                    return True
            return False

        resolved |= text.apply(text_resolved)

    return resolved

# ---------- Exclusive mode classification (Train > Tram/Light rail > Bus) ----------
TRAIN_PAT = re.compile(r"\btrain(s)?\b|\bt[1-9]\b|\b(line|rail line)\b", re.I)
TRAM_PAT  = re.compile(r"\b(tram|light\s*rail)\b|\bl[1-3]\b", re.I)
BUS_PAT_KW= re.compile(r"\bbus(es)?\b|\broute\s*[a-z]?\d{1,4}\b", re.I)

def classify_mode_exclusive_syd(text: str) -> str:
    s = (text or "").lower()

    # Replacement phrasing goes to affected rail mode
    if ("replace" in s or "replacement" in s) and (re.search(r"\btrain(s)?\b|\bt[1-9]\b", s) or "rail" in s):
        return "train"
    if ("replace" in s or "replacement" in s) and (re.search(r"\btram\b|\blight\s*rail\b|\bl[1-3]\b", s)):
        return "tram"

    if TRAIN_PAT.search(s):
        return "train"
    if TRAM_PAT.search(s):
        return "tram"
    if BUS_PAT_KW.search(s):
        return "bus"

    return "bus"  # residual bucket

# ---------- Helpers ----------
def first_text_series(df: pd.DataFrame):
    for c in ["summary_en", "plain_en", "text"]:
        if c in df.columns:
            return df[c].fillna("").astype(str)
    return pd.Series([""] * len(df))

def summarise_one(csv_file: str, routes_idx: dict):
    df = pd.read_csv(csv_file, encoding="utf-8")
    run_id = os.path.splitext(os.path.basename(csv_file))[0]

    # Timestamp passthrough
    if "created_at_iso" in df.columns and not df["created_at_iso"].isna().all():
        dt_local = str(df["created_at_iso"].iloc[0])
    else:
        dt_local = ""

    total = int(len(df))

    # Exclusive modes
    txt = first_text_series(df)
    modes = txt.apply(classify_mode_exclusive_syd)
    trains = int((modes == "train").sum())
    trams  = int((modes == "tram").sum())
    buses  = int((modes == "bus").sum())
    assert trains + trams + buses == total, "Mode counts must equal Alerts processed"

    # Route resolution
    resolved_mask = compute_route_resolved_mask(df, routes_idx)
    resolved_pct  = round(100 * resolved_mask.mean(), 1) if total else 0.0

    return {
        "Run ID": run_id,
        "Date/Time (local)": dt_local,
        "Alerts processed": total,
        "Train alerts": trains,
        "Tram/Light rail alerts": trams,
        "Bus alerts": buses,
        "Route names resolved (%)": resolved_pct
    }

def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python summarise_runs_syd.py "out\\syd_alerts_translated_*.csv"')
    routes_idx = load_routes(ROUTES_TXT)

    files = []
    for pattern in sys.argv[1:]:
        files.extend(glob.glob(pattern))
    files = sorted(files)
    if not files:
        sys.exit("No matching CSV files found for the given pattern.")

    rows = [summarise_one(f, routes_idx) for f in files]
    out = pd.DataFrame(rows)

    # Totals row
    df_runs = out
    totals = {
        "Run ID": "Total",
        "Date/Time (local)": "—",
        "Alerts processed": int(df_runs["Alerts processed"].sum()),
        "Train alerts": int(df_runs["Train alerts"].sum()),
        "Tram/Light rail alerts": int(df_runs["Tram/Light rail alerts"].sum()),
        "Bus alerts": int(df_runs["Bus alerts"].sum()),
        "Route names resolved (%)": round(df_runs["Route names resolved (%)"].mean(), 1)
    }
    out = pd.concat([out, pd.DataFrame([totals])], ignore_index=True)

    out_path = "_runs_summary_SYD.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))
    print(f"\nSaved: {out_path}")

if __name__ == "__main__":
    main()
