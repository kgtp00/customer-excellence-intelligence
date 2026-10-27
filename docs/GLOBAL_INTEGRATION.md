# Global research discovery — manual pilot

## Purpose
Discover external, *global-first*, pharmaceutical Customer Excellence research from Across Health, ZS, IQVIA, Veeva, DT Consulting and Indegene. This is not a UK-only research engine.

## What the adapter does
- Tests public listing pages, after checking robots.txt.
- Collects only link titles, links, discovery date, preliminary topic tags and source status.
- Stops at one page per listing, restricts request size and limits request duration.
- Keeps all results in a **manual review artifact**, not the public website.
- Records blocked/failed sources independently.

## Limitations
- It is **not** a validated feed/API integration with the publishers.
- It may find zero items for sites whose content is rendered client-side, blocked, or presented in a format outside our simple parser.
- It does not verify page publication dates, study design, methodology, findings or evidence quality. Discovery date is NOT publication date.
- It does not index, republish, scrape complete articles, circumvent paywalls or collect proprietary report PDFs.
- Source monitoring must be checked against each publisher's access terms before any recurring crawler is enabled.

## Manual test
GitHub Actions → **Global research discovery (manual review only)** → **Run workflow**.
Download `global-research-review-candidates` from the workflow run artifacts. If the workflow fails, inspect the logs. Nothing is auto-published.

## Next work after this test
1. Validate actual source access and yield.
2. Fix weak source-specific selectors and prefer RSS/API where documented.
3. Verify article dates and add source-aware relevance filters.
4. Produce a reviewed evidence-backed published feed, never direct unmoderated publisher output.
