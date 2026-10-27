# Customer Excellence Intelligence

Independent **global-first** public-source research prototype for pharmaceutical Customer Excellence and AI-enabled transformation. Not affiliated with or endorsed by Novartis.

## Published website
- Frontend: `index.html`, hosted on GitHub Pages after Pages is enabled.
- Curated review library: `data/library.json`.
- The library contains 14 manually reviewed public-source summaries with evidence limitations and executive questions.
- Research publishers may be commercially interested parties. Editorial interpretations are not independent verification or operating guidance.
- Three records intentionally omit publication dates because precise dates could not be confirmed.

## Features
Search by title, summary and implications; filter by functional domain, AI relevance, and UK tag; view evidence limitations and original sources. Saved articles use local browser storage only and do not sync between users or devices.

## Research collection (manual test only)
- `.github/workflows/collection-smoke-test.yml` examines public GOV.UK/MHRA metadata.
- `.github/workflows/global-source-smoke-test.yml` discovers public specialist-publisher links and runs conservative triage.
- The MHRA and global smoke-test workflows are manually triggered. A separate **Daily global research discovery** workflow is scheduled once per day and may commit only unreviewed titles and links to `data/discoveries.json` after a successful run. It does **not** alter `data/library.json` or generate executive findings.
- Never assume crawler discovery dates are article publication dates.
- Robots restrictions and publisher terms must be respected.

## Editorial release policy
Only an editor may add a record after verifying the source's title and URL; where possible publication date; its content type, findings and limitations; and the distinction between research evidence and our interpretation. Records with dates not established must be labelled as such. Never publish confidential corporate information, personal data, proprietary full texts or credentials.

## Current limitations
Automated **metadata-only** collection is configured but still awaiting a confirmed successful scheduled/manual run. No automatic publishing of vetted executive analysis, AI API scoring, user login, shared bookmarking or full-text semantic research assistant. This is a **prototype with an editorially curated library**, not a fully automated intelligence service.

## Next milestones
1. Validate the 14 published entries and source links in the user's own browser.
2. Improve global source coverage and discovery dates, especially IQVIA and DT Consulting.
3. Add a durable editorial review/approval workflow with provenance.
4. Evaluate scheduled collection and optional no-cost/low-cost AI augmentation only after quality and licensing checks.

## Daily discovery operation
GitHub Actions → **Daily global research discovery** → **Run workflow** for the first test. Requires the repository's Actions workflow to have permission to write contents to commit the metadata feed. Check the workflow logs and `data/discoveries.json` before treating scheduled refresh as operational. GitHub schedules are best-effort and may be delayed or disabled on inactive repositories. The website's **Newly discovered research** section shows link-only metadata, not approved analysis.
