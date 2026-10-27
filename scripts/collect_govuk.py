#!/usr/bin/env python3
"""Metadata-only GOV.UK publication discovery. Never automatically publish findings."""
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

TODAY = dt.datetime.now(dt.timezone.utc).date()
QUERY = "pharmaceutical OR medicines OR healthcare"
URL = "https://www.gov.uk/api/search.json?" + urllib.parse.urlencode({
    "q": "pharmaceutical", "count": "100", "order": "-public_timestamp",
    "filter_organisations": "medicines-and-healthcare-products-regulatory-agency"
})
USER_AGENT = "CustomerExcellenceIntelligenceResearch/0.1 (metadata only; GitHub public pilot)"
TERMS = ("pharm", "medicine", "healthcare", "regulat", "hcp", "patient", "clinical",
         "marketing", "commercial", "digital", "ai", "artificial intelligence")
OUT = Path("data/candidates.json")

def normalize(item):
    title = re.sub(r"<[^>]+>", "", str(item.get("title", ""))).strip()
    link = item.get("link", "")
    if not isinstance(link, str) or not link.startswith("/"):
        return None
    published = str(item.get("public_timestamp") or "")[:10]
    if not published or published > TODAY.isoformat():
        return None
    text = (title + " " + str(item.get("description", ""))).lower()
    if not any(term in text for term in TERMS):
        return None
    return {"title": title, "url": "https://www.gov.uk" + link,
            "published": published, "source": "GOV.UK / MHRA",
            "description": re.sub(r"<[^>]+>", "", str(item.get("description", "")))[:300],
            "status": "needs_editorial_review", "uk": True, "ai": bool(re.search(r"\\bai\\b|artificial intelligence", text))}

def main():
    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT,
                                                  "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as response:
        result = json.load(response)
    seen = set()
    candidates = []
    for item in result.get("results", []):
        record = normalize(item)
        if record and record["url"] not in seen:
            candidates.append(record)
            seen.add(record["url"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"retrieved": TODAY.isoformat(),
                               "source_status": "ok",
                               "review_required": True,
                               "records": candidates}, indent=2, ensure_ascii=False) + "\n")
    print(f"Retrieved {len(candidates)} metadata candidates. No items approved or published.")

if __name__ == "__main__":
    main()
