# Tender Radar

The Government of Canada publishes tenders every day, but they're buried in a huge feed. This sends a small vendor a short daily email with only the ones that match what they sell.

**Status:** Day 0. Planning is done, code starts next. Nothing here is tested yet.

## The problem, in plain words

A local supplier or service company could win public work, but finding the right tender means digging through thousands of notices. Most owners don't have the time, so they don't look.

## What is known and what isn't

The tender notices are published as open data by the Government of Canada ([CanadaBuys tender notices](https://open.canada.ca/data/en/dataset/6abd20d4-7a1c-4b38-baa2-9525d0bb2fd2)). What is **not** yet known is whether small vendors actually miss tenders because of this. Talking to a few owners is step one, before building further.

## What the first version does

1. Reads the open tender data once a day
2. Lets a vendor pick keywords and a region
3. Emails a digest of matches, each with a two-line plain summary and a link to the original notice

Not in version one: bid writing help, multi-user accounts, payment.

## Success looks like

One real Ontario vendor gets the email for a week and tells me which tenders they would have missed.

## Built with

Next.js, Supabase, Vercel scheduled jobs, and the Claude API for summaries.

See [`docs/PLAN.md`](docs/PLAN.md) for the step-by-step plan.

## Part of

[Ontario SMB Problem Atlas](https://github.com/prajuvin/ontario-smb-problem-atlas), a cited map of what small businesses struggle with.

Built by Praju at YHWH Digital, Toronto. *We refresh businesses. We rise together.*
