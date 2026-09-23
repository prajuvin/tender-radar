# Tender Radar

**The Government of Canada posts hundreds of open tenders a day. Tender Radar finds the ones that match what your small business sells, and explains each in plain words.**

**Try it:** https://prajuvin.github.io/tender-radar/ *(live once GitHub Pages is on)*

It uses real data. Every morning a robot downloads the Government's open tender list (about 900 notices) and the page searches it for your words.

## How to use it (no sign-up)

1. **Your work:** type what you sell, like "cleaning" or "printing", and pick where you can work.
2. **Matches:** each tender shows the deadline, what kind of work it is, where it is, a short summary, and a link to the official notice. Work in your area and tenders with your word in the title come first.
3. **Keep it:** copy a link that remembers your words, or a list you can paste into an email.

## Why

Government work can be steady income for small businesses, but finding the right tender means digging through a huge feed. In the Canadian Federation of Independent Business's Q4 2025 survey, 54% of small business owners named government regulation and paperwork a top concern ([source](https://www.cfib-fcei.ca/en/research-economic-analysis/our-members-opinions)). Whether owners actually miss tenders because of this is **not proven yet**, and finding out is the next step.

## What it does and doesn't do

| Does | Doesn't (yet) |
| --- | --- |
| Reads the real open tender list every day | Send daily emails |
| Matches words at the start of any word ("clean" finds cleaning, cleaners) | Understand meaning (it won't know "janitorial" means cleaning) |
| Drops tenders that are past their deadline, even if the feed still says open | Help you write a bid |
| Links to the official notice, or shows the reference number and buyer contact when there's no link | Cover provincial or city tenders |

Always read the official notice before you bid. Tender Radar is not a government service.

## How it works

```
CanadaBuys open data (CSV, daily)
   → radar/fetch.py    download, clean, drop closed tenders   (GitHub Action, 7:17am Toronto)
   → docs/data/tenders.json
   → docs/index.html + app.js    matching in the browser       (GitHub Pages)
```

Why this design: [`decisions/ADR-001-how-tender-radar-runs.md`](decisions/ADR-001-how-tender-radar-runs.md).

## Run it yourself

```bash
python -m radar.fetch                                  # download today's tenders
python -m radar.digest cleaning printing --where ontario   # plain-text list in the terminal
python -m http.server -d docs 8000                     # open http://localhost:8000
```

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q          # 18 unit tests on cleaning and matching
python tests/e2e_check.py    # browser test on real data at phone and desktop width;
                             # checks the website's matches equal the Python matcher's
```

Last full check (2026-09-23): 839 open tenders loaded, 18 unit tests passed, browser matches equal Python on every test search, and an axe accessibility scan found no WCAG A or AA issues on any screen.

## Roadmap

| When | What | Status |
| --- | --- | --- |
| Now | Real daily data, plain-language matches, shareable link | Done |
| Now | Show it to 3 Ontario vendors: what would they have missed? | Not started |
| Next | Free daily email for saved words | Not started (waits on vendor feedback) |
| Next | Smarter matching: related words ("janitorial" for cleaning) | Not started |
| Later | Short AI summaries of long notices | Not started |
| Later | Ontario and city tenders | Not started |

## Data and licence

Contains information licensed under the [Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada). Source: [CanadaBuys tender notices](https://open.canada.ca/data/en/dataset/6abd20d4-7a1c-4b38-baa2-9525d0bb2fd2).

Part of the [Ontario SMB Problem Atlas](https://github.com/prajuvin/ontario-smb-problem-atlas). Built by Praju at YHWH Digital, Toronto. *We refresh businesses. We rise together.*
