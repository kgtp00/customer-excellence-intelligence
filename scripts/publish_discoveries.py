#!/usr/bin/env python3
"""Prepare a title/link-only public discovery feed. Never approve research findings.
Preserves first_seen for existing URLs. Unknown publication dates are never inferred.
"""
import datetime as dt
import json
from pathlib import Path

SOURCE = Path("data/global-triage-report.json")
OUTPUT = Path("data/discoveries.json")
TODAY = dt.datetime.now(dt.timezone.utc).date().isoformat()
MAX_ITEMS = 100

def build(report, old=None, today=TODAY):
    old = old or {}
    previous = {r["url"]:r for r in old.get("items",[]) if r.get("url")}
    permitted = {"priority_editorial_review","secondary_editorial_review"}
    new = []
    seen = set()
    for row in report.get("records",[]):
        url = row.get("url","")
        title = row.get("title","").strip()
        if not url.startswith("https://") or url in seen or len(title)<20:
            continue
        if row.get("editorial_queue") not in permitted:
            continue
        # Provisional URL-slug titles are not appropriate for a public feed.
        if row.get("title_status") not in ("source_anchor_text",):
            continue
        if row.get("content_type_hint") == "survey_invitation":
            continue
        seen.add(url)
        prev = previous.get(url,{})
        new.append({
            "source": row.get("source",""),
            "title":title,
            "url":url,
            "topics":row.get("topics",[]),
            "first_seen":prev.get("first_seen", today),
            "last_seen":today,
            "publication_date":None,
            "publication_date_status":"unverified",
            "review_status":"unreviewed_metadata_only"
        })
    # Never invent dates or summaries. Sort by first observed, not publication date.
    new.sort(key=lambda x: (x["first_seen"],x["source"],x["title"]),reverse=True)
    return {"feed_type":"unreviewed_metadata_only","generated_on":today,
            "warning":"Discovery date is not article publication date. Links are unreviewed and contain no verified findings.",
            "items":new[:MAX_ITEMS]}

def main():
    report=json.loads(SOURCE.read_text(encoding="utf-8"))
    prior=json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    if not report.get("records"):
        raise RuntimeError("No research records returned; refuse to erase existing feed")
    feed=build(report,prior)
    if not feed["items"]:
        raise RuntimeError("No eligible review candidates found; refuse to erase existing feed")
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(feed,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Prepared {len(feed['items'])} unreviewed title/link records; 0 expert findings published.")

if __name__=="__main__":
    main()
