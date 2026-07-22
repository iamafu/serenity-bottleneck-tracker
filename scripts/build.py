#!/usr/bin/env python3
"""
Daily data pipeline for serenity-bottleneck-tracker.

Pulls the public Serenity (@aleabitoreddit) tweet-mention archive from
yan-labs/serenity-aleabitoreddit, merges each top ticker's mention stats
with live price/momentum data (scripts/price.analyze), and writes
docs/data/tickers.json for the static dashboard in docs/index.html.
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(__file__))
from price import analyze

ARCHIVE_REPO = "https://github.com/yan-labs/serenity-aleabitoreddit.git"
TOP_N = 60  # cap so the daily run stays fast and the Pages payload stays small


def fetch_ticker_stats():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["git", "clone", "--depth", "1", ARCHIVE_REPO, tmp],
            check=True, capture_output=True, text=True,
        )
        stats_path = os.path.join(tmp, "data", "ticker_stats.txt")
        with open(stats_path, encoding="utf-8") as f:
            lines = f.read().splitlines()

    rows = []
    for line in lines[4:]:  # skip 2 summary lines + blank line + header
        parts = line.split()
        if len(parts) != 4:
            continue
        ticker, mentions, first_seen, last_seen = parts
        if not mentions.isdigit():
            continue
        rows.append({
            "ticker": ticker,
            "mentions": int(mentions),
            "first_seen": first_seen,
            "last_seen": last_seen,
        })
    rows.sort(key=lambda r: r["mentions"], reverse=True)
    return rows[:TOP_N]


def main():
    rows = fetch_ticker_stats()
    out = []
    for row in rows:
        try:
            price = analyze(row["ticker"])
        except Exception as e:
            price = {"error": str(e)}
        out.append({**row, "price": price})
        print(f"  {row['ticker']:<8} mentions={row['mentions']:<5} "
              f"stage={price.get('stage', price.get('error', '?'))}")

    payload = {
        "generated_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source": "yan-labs/serenity-aleabitoreddit (public tweet-mention archive)",
        "disclaimer": "Research/education only. Not financial advice. Not affiliated with Serenity/@aleabitoreddit.",
        "tickers": out,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "tickers.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(out)} tickers -> {out_path}")


if __name__ == "__main__":
    main()
