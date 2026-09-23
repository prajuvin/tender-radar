# ADR-001: How Tender Radar runs

**Status:** Accepted
**Date:** 2026-09-23
**Deciders:** Praju

## Context

Tender Radar has to show real, current Government of Canada tenders to small business owners who are not technical. The Government publishes open tenders every day as a CSV file of about 900 rows and 6 MB under the Open Government Licence – Canada. The project has no budget and no users yet, so it must cost nothing to run and need no server to look after.

Things found while testing on the real file:

- Some rows are still marked "Open" after their closing date. They are filtered out by date.
- About half the rows have no notice link. For references starting `cb-` or `ws`, the CanadaBuys page at a standard address works (checked by hand). The rest show the reference number and buyer contact.
- A region of "Canada" next to a province means the work is in that province, not Canada-wide.
- The server refuses requests that don't identify as a browser, so the downloader sends a browser-style user agent that also names the project.

## Decision

A scheduled GitHub Action downloads the file each morning, cleans it into a small JSON file, and commits it. GitHub Pages serves a static page that loads the JSON and does the matching in the visitor's browser.

## Options considered

### A: Static site plus daily GitHub Action (chosen)

| Dimension | Assessment |
| --- | --- |
| Complexity | Low: one Python script, one page |
| Cost | Free |
| Scalability | Fine for thousands of visitors; the JSON is about 1.3 MB |
| Familiarity | High: HTML, JavaScript, Python |

Pros: no server, no secrets, no database; the data history lives in git. Cons: no accounts, so no email alerts yet; matching logic exists twice (Python and JavaScript) and must be kept in step.

### B: Next.js with Supabase and a scheduled job

Pros: accounts, saved searches, and email are straightforward. Cons: more moving parts and ongoing cost before a single user has asked for it.

### C: Email-only service

Pros: matches how owners actually work. Cons: needs an email provider, sign-up, and unsubscribe handling first, and there is nothing to show until it's built.

## Trade-off analysis

Option A proves the core claim (useful matches from real data, in plain words) at no cost. B and C add value only once owners confirm they want alerts, so they wait for that evidence.

## Consequences

- Easier: anyone can use it from a link, and there's nothing to maintain.
- Harder: daily email alerts need a new piece (see roadmap).
- To revisit: if the JSON grows past about 5 MB, split it by region. The Python and JavaScript matchers are kept in step by `tests/e2e_check.py`, which compares their results on real data.

## Action items

1. [x] Download, clean, and test against the real file
2. [x] Browser matching with plain-language results and an accessibility scan
3. [ ] Turn on GitHub Pages (Settings, Pages, deploy from `main`, folder `/docs`)
4. [ ] Show it to three Ontario vendors and record what they would have missed
