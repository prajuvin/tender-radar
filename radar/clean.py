"""Turn one raw CanadaBuys CSV row into a small, plain-language tender record."""
import html
import re
from datetime import datetime, timezone

CATEGORY = {
    "GD": "Goods",
    "SRV": "Services",
    "CNST": "Construction",
}

F = {
    "title": "title-titre-eng",
    "ref": "referenceNumber-numeroReference",
    "published": "publicationDate-datePublication",
    "closes": "tenderClosingDate-appelOffresDateCloture",
    "status": "tenderStatus-appelOffresStatut-eng",
    "category": "procurementCategory-categorieApprovisionnement",
    "method": "procurementMethod-methodeApprovisionnement-eng",
    "delivery": "regionsOfDelivery-regionsLivraison-eng",
    "buyer": "contractingEntityName-nomEntitContractante-eng",
    "city": "contractingEntityAddressCity-entiteContractanteAdresseVille-eng",
    "province": "contractingEntityAddressProvince-entiteContractanteAdresseProvince-eng",
    "url": "noticeURL-URLavis-eng",
    "description": "tenderDescription-descriptionAppelOffres-eng",
    "email": "contactInfoEmail-informationsContactCourriel",
}

NOTICE_PAGE = "https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/"
# Reference prefixes whose notice page is known to exist at NOTICE_PAGE + lowercase ref (checked 2026-09-23)
PAGE_PREFIXES = ("cb-", "ws")

TAG = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")


def plain_text(raw):
    """Strip HTML tags and entities, collapse whitespace."""
    text = html.unescape(TAG.sub(" ", raw or ""))
    return SPACE.sub(" ", text.replace("\xa0", " ")).strip()


def star_list(raw):
    """CanadaBuys packs lists as '*A\\n*B'. Return ['A', 'B']."""
    return [p.strip().lstrip("*").strip() for p in (raw or "").split("\n") if p.strip().lstrip("*").strip()]


def short_summary(text, limit=260):
    """First sentence or two, cut at a word boundary."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("? "))
    if end > 80:
        return cut[: end + 1]
    return cut[: cut.rfind(" ")].rstrip(",;:") + "…"


def parse_close(raw):
    try:
        return datetime.fromisoformat((raw or "").strip())
    except ValueError:
        return None


def link_for(url, ref):
    """Return (link, is_exact). Falls back to the CanadaBuys notice page when the feed has no link."""
    if url:
        # A few published links use plain http; the same pages load over https.
        return ("https://" + url[7:] if url.startswith("http://") else url), True
    if ref.lower().startswith(PAGE_PREFIXES):
        return NOTICE_PAGE + ref.lower(), True
    return "https://canadabuys.canada.ca/en/tender-opportunities", False


def specific_regions(regions):
    """'Canada' alongside a province means the work is in that province."""
    named = [r for r in regions if r not in ("Canada", "World", "Foreign")]
    return named


def where_label(regions):
    named = specific_regions(regions)
    if named:
        return ", ".join(r.replace(" (except NCR)", "").replace("National Capital Region (NCR)", "Ottawa-Gatineau area") for r in named)
    if "Canada" in regions:
        return "Anywhere in Canada"
    return "Not listed"


def clean_row(row, now=None):
    """Return a tender dict, or None if it is not open or already closed."""
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    get = lambda k: (row.get(F[k]) or "").strip()
    if get("status").lower() != "open":
        return None
    closes = parse_close(get("closes"))
    if closes is None or closes < now:
        return None
    title = plain_text(get("title"))
    if not title:
        return None
    description = plain_text(get("description"))
    if description.lower().startswith(title.lower()):
        description = description[len(title):].lstrip(" .:-–")
    kinds = set()
    for c in star_list(get("category")):
        kinds.update({"SRVTGD": {"Services", "Goods"}}.get(c, {CATEGORY.get(c, c)}))
    order = ["Goods", "Services", "Construction"]
    cats = [k for k in order if k in kinds] + sorted(kinds - set(order))
    url, exact = link_for(get("url"), get("ref"))
    return {
        "id": get("ref"),
        "title": title,
        "buyer": get("buyer"),
        "place": ", ".join(p for p in (get("city"), get("province")) if p),
        "regions": star_list(get("delivery")),
        "category": " and ".join(cats) or "Not listed",
        "where": where_label(star_list(get("delivery"))),
        "method": get("method"),
        "published": get("published")[:10],
        "closes": closes.isoformat(timespec="minutes"),
        "url": url,
        "exactLink": exact,
        "contact": "" if exact else get("email"),
        "summary": short_summary(description) if description else "No description was published. Open the notice for details.",
        "text": (title + " " + description[:1500]).lower(),
    }
