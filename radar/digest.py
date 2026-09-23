"""Print a plain-text daily digest for a set of words. The same text can be emailed later.

Run: python -m radar.digest cleaning printing --where ontario
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

from radar.match import match

DATA = Path(__file__).resolve().parent.parent / "docs" / "data" / "tenders.json"


def days_left(closes, today):
    return (datetime.fromisoformat(closes).date() - today).days


def render(matches, words, today):
    if not matches:
        return f"No open tenders mention {', '.join(words)} today."
    lines = [f"{len(matches)} open tender{'s' if len(matches) != 1 else ''} for {', '.join(words)}:", ""]
    for t in matches:
        d = days_left(t["closes"], today)
        lines.append(f"- {t['title']} ({t['buyer']})")
        lines.append(f"  Closes in {d} day{'s' if d != 1 else ''}. {t['url']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words", nargs="+")
    ap.add_argument("--where", default="anywhere", choices=["anywhere", "ontario", "ncr"])
    a = ap.parse_args()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    print(render(match(data["tenders"], a.words, a.where), a.words, datetime.now().date()))


if __name__ == "__main__":
    main()
