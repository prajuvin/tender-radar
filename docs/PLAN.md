# Build plan

One step at a time. Each step ends with something you can see working.

| Step | What gets built | You can see it when |
| --- | --- | --- |
| 0 | Talk to 3 Ontario vendors: do they look for tenders, and what stops them? | Notes saved in the repo |
| 1 | Download and read one day of tender data | A printed list of real tenders |
| 2 | Save tenders in a database and match by keyword | A search returns sensible results |
| 3 | Vendor settings page: keywords and region | Saved settings change the matches |
| 4 | Daily email digest with short summaries | A real email arrives |
| 5 | Deploy and run for one week with one real vendor | Feedback on what they would have missed |

## Data tables

- `tenders`: id, title, description, category, closing date, link
- `vendors`: email, region
- `keywords`: vendor, word
- `digests_sent`: vendor, date, tender count

## Things to check early

- The data file's format and update schedule, from the official page
- Any terms of use for the data
- How to link to and describe each tender accurately, without changing its meaning
