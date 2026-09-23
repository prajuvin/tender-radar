"""Match tenders to a vendor's plain words and region. Mirrors docs/app.js."""
import re

from radar.clean import specific_regions

REGIONS = {
    "anywhere": None,
    "ontario": ["Ontario", "National Capital Region", "Ottawa"],
    "ncr": ["National Capital Region", "Ottawa"],
}


def word_pattern(word):
    # "clean" matches clean, cleaning, cleaners; always at the start of a word
    return re.compile(r"\b" + re.escape(word.strip().lower()))


def in_region(tender, region):
    wanted = REGIONS.get(region)
    if not wanted:
        return True
    named = specific_regions(tender.get("regions") or [])
    if not named:
        return True  # Canada-wide or location not listed: shown, and labelled on screen
    return any(w in r for r in named for w in wanted)


def is_local(tender, region):
    """True when the tender names a place inside the chosen region (used to sort local work first)."""
    wanted = REGIONS.get(region)
    named = specific_regions(tender.get("regions") or [])
    return bool(wanted and named and any(w in r for r in named for w in wanted))


def match(tenders, words, region="anywhere"):
    words = [w.strip().lower() for w in words if w and w.strip()]
    if not words:
        return []
    pats = [(w, word_pattern(w)) for w in words]
    out = []
    for t in tenders:
        if not in_region(t, region):
            continue
        hits = [w for w, p in pats if p.search(t["text"])]
        if hits:
            in_title = any(p.search(t["title"].lower()) for _, p in pats)
            out.append({**t, "hits": hits, "in_title": in_title})
    # Local work first, then tenders whose title mentions the word, then soonest deadline
    out.sort(key=lambda t: (not is_local(t, region), not t["in_title"], t["closes"]))
    return out
