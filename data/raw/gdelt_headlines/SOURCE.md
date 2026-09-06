# Source 11 — GDELT DOC 2.0 news headlines

**Role:** SLM training + test input.  
**Verification date:** 2026-09-04  
**Decision:** ✅ **RESOLVED 2026-09-04 — Option C selected.**
ArtList for the last ~90 days (real recent headlines, no registration) **plus** a hand-collected historical set of ~20–40 headlines per calendar event (7 events × ~20–30 = ~140–210 headlines). Total expected corpus: 400–600 headlines. Enough for zero-shot eval + 300–400 labeled for LoRA. **Document sample size honestly in viva.**

## PRIMARY

- Endpoint: `https://api.gdeltproject.org/api/v2/doc/doc`
- Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- No API key. `mode=ArtList`, `format=json`, `maxrecords` cap 250, **no paging**.
- Fields typically: `url`, `title`, `seendate`, `domain`, `language`, `sourcecountry`, …

**Intended query:** semiconductor shortage + India + automotive; 30-day windows; `sleep(2)`; retries 2s/4s/8s max 3; failures → `data/logs/gdelt_failures.jsonl`.

## Sample row (schema)

```json
{
  "url": "https://example.news/...",
  "title": "headline string",
  "seendate": "20210315T120000Z",
  "domain": "example.news"
}
```

Live JSON fetch from this environment **timed out**. Do not invent headlines.

## RESOLVED — data collection plan (Option C)

**Two-part corpus:**

1. **Recent headlines (ArtList, ~90-day window):** Query ArtList with `mode=ArtList`, `format=json`, semiconductor + india + automotive keywords. Expected yield: 200–400 headlines from the current rolling window. `sleep(2)` between calls, retries 2s/4s/8s, failures → `data/logs/gdelt_failures.jsonl`.

2. **Historical headlines (hand-collected, 7 calendar events):**
   Manually collect ~20–40 headlines per event from GDELT Event Explorer, Google News cached links, or news archive sites. Events:
   - COVID-19 manufacturing shutdown (Mar–Jun 2020)
   - Global chip shortage peak (Q3 2021 – Q2 2022)
   - Shanghai lockdown (Apr–May 2022)
   - China Ga/Ge export controls (Aug 2023)
   - Red Sea shipping crisis (Dec 2023 – Mar 2024)
   - China rare-earth magnet restrictions (Apr 2025)
   - Russia-Ukraine neon/palladium shock (Mar 2022)

   Save as `data/raw/gdelt_headlines/historical_manual.csv` with columns: `title, url, seendate, domain, event_tag, collection_method`.
   `collection_method` = one of `gdelt_artlist | manual_google_news | manual_news_archive`.

**Total target:** 400–600 headlines. Honest in the report about the mixed collection method.

**Rejected options (logged):**
- A (raw dumps): too heavy for project scope
- B (BigQuery): adds GCP dependency
- D (different source): architecture change not warranted


## Known issues

HTTP 200 with a **plain-text** error body on rate limits (must not `json.loads` blindly). Rate limits are tight. Max 250 per call.
