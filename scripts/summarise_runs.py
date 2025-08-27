#! python summarise_runs.py "out\alerts_*.csv"
#!/usr/bin/env python3
# summarise_runs.py
import sys, glob, os, re
import pandas as pd

# -------- Exclusive mode classifier (Train > Tram/Light rail > Bus) --------
TRAIN_PAT = re.compile(r"\btrain(s)?\b|\bt[1-9]\b|\b(line|rail line)\b", re.I)
TRAM_PAT  = re.compile(r"\b(tram|light\s*rail)\b|\bl[1-3]\b", re.I)
BUS_PAT   = re.compile(r"\bbus(es)?\b|\broute\s*[a-z]?\d{1,4}\b", re.I)

def classify_mode_exclusive(text: str) -> str:
    s = (text or "").lower()
    if ("replace" in s or "replacement" in s) and (re.search(r"\btrain(s)?\b|\bt[1-9]\b", s) or "rail" in s):
        return "train"
    if ("replace" in s or "replacement" in s) and (re.search(r"\btram\b|\blight\s*rail\b|\bl[1-3]\b", s)):
        return "tram"
    if TRAIN_PAT.search(s):
        return "train"
    if TRAM_PAT.search(s):
        return "tram"
    if BUS_PAT.search(s):
        return "bus"
    return "bus"

# -------- Helpers --------
FNAME_STAMP = re.compile(r"(\d{8})_(\d{4})")  # YYYYMMDD_HHMM

def derive_dt_from_filename(basename: str, tz_offset="+10:00") -> str:
    """
    Try to parse YYYYMMDD_HHMM from the run id / filename.
    Return ISO-like local string 'YYYY-MM-DDTHH:MM:00+10:00' if found,
    else empty string so caller can fall back to created_at_iso.
    """
    m = FNAME_STAMP.search(basename)
    if not m:
        return ""
    ymd, hm = m.group(1), m.group(2)
    y, mo, d = ymd[0:4], ymd[4:6], ymd[6:8]
    hh, mm = hm[0:2], hm[2:4]
    return f"{y}-{mo}-{d}T{hh}:{mm}:00{tz_offset}"

def first_text_series(df: pd.DataFrame):
    for c in ["summary_en", "plain_en", "text"]:
        if c in df.columns:
            return df[c].fillna("").astype(str)
    return pd.Series([""] * len(df))

def derive_city_tag(files):
    joined = " ".join(files).upper()
    if "SEQ" in joined:
        return "SEQ"
    if "MEL" in joined or "ALERTS_" in joined:
        return "MEL"
    return "RUNS"

def summarise_one(csv_file: str):
    df = pd.read_csv(csv_file, encoding="utf-8")
    run_id = os.path.splitext(os.path.basename(csv_file))[0]

    # Prefer filename timestamp; fall back to created_at_iso if needed
    dt_local = derive_dt_from_filename(run_id)
    if not dt_local:
        if "created_at_iso" in df.columns and not df["created_at_iso"].isna().all():
            dt_local = str(df["created_at_iso"].iloc[0])
        else:
            dt_local = ""

    total = int(len(df))

    # Exclusive mode classification
    txt = first_text_series(df)
    modes = txt.apply(classify_mode_exclusive)
    trains = int((modes == "train").sum())
    trams  = int((modes == "tram").sum())
    buses  = int((modes == "bus").sum())
    assert trains + trams + buses == total, "Mode counts must equal Alerts processed"

    # Simple, proven route resolution (MEL/SEQ)
    resolved_mask = df.get("route_short_name", pd.Series([""] * len(df))).astype(str).str.strip().ne("")
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
        sys.exit('Usage: python summarise_runs.py "out\\alerts_*.csv"  OR  "out\\seq_alerts_*.csv"')

    files = []
    for pattern in sys.argv[1:]:
        files.extend(glob.glob(pattern))
    files = sorted(files)
    if not files:
        sys.exit("No matching CSV files found for the given pattern.")

    rows = [summarise_one(f) for f in files]
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

    city_tag = derive_city_tag(files)
    out_path = f"_runs_summary_RUNS_{city_tag}.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))
    print(f"\nSaved: {out_path}")

if __name__ == "__main__":
    main()
