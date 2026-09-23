"""Download today's open tenders from CanadaBuys and write docs/data/tenders.json.

Data: Government of Canada, CanadaBuys tender notices, Open Government Licence - Canada.
Run: python -m radar.fetch
"""
import csv
import io
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from radar.clean import clean_row

SOURCE = "https://canadabuys.canada.ca/opendata/pub/openTenderNotice-ouvertAvisAppelOffres.csv"
OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "tenders.json"


def download(url=SOURCE):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) tender-radar/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8-sig")


def build(csv_text, now=None):
    rows = csv.DictReader(io.StringIO(csv_text))
    seen, tenders, skipped = set(), [], 0
    for row in rows:
        t = clean_row(row, now=now)
        if t is None or t["id"] in seen:
            skipped += 1
            continue
        seen.add(t["id"])
        tenders.append(t)
    tenders.sort(key=lambda t: t["closes"])
    return tenders, skipped


def main():
    tenders, skipped = build(download())
    if not tenders:
        print("No open tenders found; keeping the previous file.", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "source": SOURCE,
        "licence": "Open Government Licence - Canada",
        "count": len(tenders),
        "tenders": tenders,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(tenders)} open tenders ({skipped} closed, duplicate or empty rows skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
