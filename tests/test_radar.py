from datetime import datetime, date

from radar.clean import clean_row, plain_text, short_summary, star_list
from radar.fetch import build
from radar.match import match
from radar.digest import render

NOW = datetime(2026, 9, 23, 12, 0)


def row(**kw):
    base = {
        "title-titre-eng": "Janitorial cleaning services for an office",
        "referenceNumber-numeroReference": "PW-1",
        "publicationDate-datePublication": "2026-09-01",
        "tenderClosingDate-appelOffresDateCloture": "2026-10-15T14:00:00",
        "tenderStatus-appelOffresStatut-eng": "Open",
        "procurementCategory-categorieApprovisionnement": "*SRV",
        "procurementMethod-methodeApprovisionnement-eng": "Competitive - Open bidding",
        "regionsOfDelivery-regionsLivraison-eng": "*Ontario (except NCR)",
        "contractingEntityName-nomEntitContractante-eng": "Public Services and Procurement Canada",
        "contractingEntityAddressCity-entiteContractanteAdresseVille-eng": "Toronto",
        "contractingEntityAddressProvince-entiteContractanteAdresseProvince-eng": "Ontario",
        "noticeURL-URLavis-eng": "https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/pw-1",
        "tenderDescription-descriptionAppelOffres-eng": "<p>Cleaning&nbsp;of one office building. Three evenings a week.</p>",
    }
    base.update(kw)
    return base


def test_plain_text_strips_html_and_entities():
    assert plain_text("<p>A&nbsp;&amp;&nbsp;B</p>") == "A & B"


def test_star_list():
    assert star_list("*Ontario (except NCR)\n*Quebec") == ["Ontario (except NCR)", "Quebec"]
    assert star_list("") == []


def test_short_summary_cuts_at_sentence():
    text = "First sentence is here and it is long enough to matter. " * 8
    s = short_summary(text)
    assert len(s) <= 260 and s.endswith(".")


def test_clean_row_basic():
    t = clean_row(row(), now=NOW)
    assert t["category"] == "Services"
    assert t["regions"] == ["Ontario (except NCR)"]
    assert "&nbsp;" not in t["summary"] and "<p>" not in t["summary"]


def test_clean_row_drops_past_closing_date_even_if_marked_open():
    # Real data contains rows still marked Open whose closing date has passed.
    assert clean_row(row(**{"tenderClosingDate-appelOffresDateCloture": "2025-09-04T14:00:00"}), now=NOW) is None


def test_clean_row_drops_closed_and_bad_dates():
    assert clean_row(row(**{"tenderStatus-appelOffresStatut-eng": "Cancelled"}), now=NOW) is None
    assert clean_row(row(**{"tenderClosingDate-appelOffresDateCloture": ""}), now=NOW) is None


def test_build_skips_duplicates():
    import csv, io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(row().keys()))
    w.writeheader(); w.writerow(row()); w.writerow(row())
    tenders, skipped = build(buf.getvalue(), now=NOW)
    assert len(tenders) == 1 and skipped == 1


def test_match_prefix_and_region():
    ont = clean_row(row(), now=NOW)
    bc = clean_row(row(**{"referenceNumber-numeroReference": "PW-2", "regionsOfDelivery-regionsLivraison-eng": "*British Columbia"}), now=NOW)
    national = clean_row(row(**{"referenceNumber-numeroReference": "PW-3", "regionsOfDelivery-regionsLivraison-eng": "*Canada"}), now=NOW)
    got = match([ont, bc, national], ["clean"], "ontario")
    assert {t["id"] for t in got} == {"PW-1", "PW-3"}
    assert got[0]["hits"] == ["clean"]


def test_match_is_word_start_not_substring():
    t = clean_row(row(**{"title-titre-eng": "Unclean areas survey", "tenderDescription-descriptionAppelOffres-eng": ""}), now=NOW)
    assert match([t], ["clean"]) == []


def test_match_no_words():
    assert match([clean_row(row(), now=NOW)], ["  "]) == []


def test_digest_text():
    t = match([clean_row(row(), now=NOW)], ["cleaning"])
    out = render(t, ["cleaning"], date(2026, 9, 23))
    assert "1 open tender for cleaning" in out and "Closes in 22 days" in out
    assert render([], ["x"], date(2026, 9, 23)).startswith("No open tenders")


def test_province_plus_canada_is_that_province():
    t = clean_row(row(**{"regionsOfDelivery-regionsLivraison-eng": "*Quebec (except NCR)\n*Canada"}), now=NOW)
    assert match([t], ["clean"], "ontario") == []
    assert t["where"] == "Quebec"


def test_canada_wide_is_kept_and_labelled_and_local_sorts_first():
    local = clean_row(row(**{"tenderClosingDate-appelOffresDateCloture": "2026-12-01T14:00:00"}), now=NOW)
    wide = clean_row(row(**{"referenceNumber-numeroReference": "PW-9", "regionsOfDelivery-regionsLivraison-eng": "*Canada"}), now=NOW)
    got = match([wide, local], ["clean"], "ontario")
    assert [t["id"] for t in got] == ["PW-1", "PW-9"]
    assert wide["where"] == "Anywhere in Canada"


def test_link_fallbacks():
    cb = clean_row(row(**{"referenceNumber-numeroReference": "cb-1-2", "noticeURL-URLavis-eng": ""}), now=NOW)
    assert cb["url"].endswith("/tender-notice/cb-1-2") and cb["exactLink"] and cb["contact"] == ""
    ssc = clean_row(row(**{"referenceNumber-numeroReference": "SSC-1:T", "noticeURL-URLavis-eng": "",
                           "contactInfoEmail-informationsContactCourriel": "buyer@example.gc.ca"}), now=NOW)
    assert not ssc["exactLink"] and ssc["contact"] == "buyer@example.gc.ca"


def test_mixed_categories_are_tidy():
    t = clean_row(row(**{"procurementCategory-categorieApprovisionnement": "*SRVTGD\n*GD"}), now=NOW)
    assert t["category"] == "Goods and Services"


def test_summary_does_not_repeat_title():
    t = clean_row(row(**{"title-titre-eng": "Service gates", "tenderDescription-descriptionAppelOffres-eng": "Service gates This requirement is for a fence."}), now=NOW)
    assert t["summary"] == "This requirement is for a fence."


def test_title_hits_rank_before_description_hits():
    body = clean_row(row(**{"title-titre-eng": "Gate installation", "tenderDescription-descriptionAppelOffres-eng": "At the training centre.",
                            "tenderClosingDate-appelOffresDateCloture": "2026-10-01T14:00:00"}), now=NOW)
    titled = clean_row(row(**{"referenceNumber-numeroReference": "PW-7", "title-titre-eng": "Training for staff",
                              "tenderClosingDate-appelOffresDateCloture": "2026-11-01T14:00:00"}), now=NOW)
    got = match([body, titled], ["training"], "ontario")
    assert [t["id"] for t in got] == ["PW-7", "PW-1"]


def test_http_links_upgraded():
    t = clean_row(row(**{"noticeURL-URLavis-eng": "http://discovery.ariba.com/rfx/1"}), now=NOW)
    assert t["url"] == "https://discovery.ariba.com/rfx/1"
