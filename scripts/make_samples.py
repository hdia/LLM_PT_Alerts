# scripts/make_samples.py
import argparse, glob, os, re, random
import pandas as pd

KEPT_COLS = [
    "created_at_iso",
    "route_id",
    "route_short_name",
    "route_long_name",
    "summary_en",
    "plain_en",
    "text",
]

TEXT_COLS = ["summary_en", "plain_en", "text"]

def scrub_text(s: str) -> str:
    if not isinstance(s, str):
        return s
    # Remove emails and phone-like strings (belt-and-braces, even though GTFS-RT rarely has PII)
    s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted-email]", s)
    s = re.sub(r"\b(\+?\d[\d\s\-()]{7,})\b", "[redacted-phone]", s)
    return s

def load_trim(path, rows, seed):
    df = pd.read_csv(path, encoding="utf-8")
    # keep intersection of available KEPT_COLS
    cols = [c for c in KEPT_COLS if c in df.columns]
    if cols:
        df = df[cols]
    # scrub possible PII in text columns
    for c in TEXT_COLS:
        if c in df.columns:
            df[c] = df[c].astype(str).apply(scrub_text)
    # deterministic sample/shuffle then head
    random.seed(seed)
    if len(df) > rows:
        df = df.sample(n=rows, random_state=seed)
    df = df.sort_index(kind="stable")
    return df

def main():
    ap = argparse.ArgumentParser(description="Create small, anonymised samples from full alert CSVs.")
    ap.add_argument("--glob", required=True, help="Input glob pattern (e.g., out\\alerts_*.csv)")
    ap.add_argument("--city", required=True, choices=["MEL","SEQ","SYD"], help="City tag for output filenames")
    ap.add_argument("--rows", type=int, default=80, help="Max rows per sample file (default 80)")
    ap.add_argument("--count", type=int, default=2, help="How many sample files to create (default 2)")
    ap.add_argument("--outdir", default="data/sample_alerts", help="Output directory")
    ap.add_argument("--seed", type=int, default=2025, help="Deterministic seed")
    args = ap.parse_args()

    files = sorted(glob.glob(args.glob))
    if not files:
        raise SystemExit(f"No files matched: {args.glob}")

    os.makedirs(args.outdir, exist_ok=True)

    picked = files[:args.count] if len(files) >= args.count else files
    for i, f in enumerate(picked, start=1):
        df = load_trim(f, args.rows, args.seed + i)
        out = os.path.join(args.outdir, f"{args.city.lower()}_sample_{i}.csv")
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"Wrote {out} ({len(df)} rows) from {os.path.basename(f)}")

if __name__ == "__main__":
    main()
