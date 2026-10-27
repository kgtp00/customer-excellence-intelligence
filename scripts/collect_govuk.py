#!/usr/bin/env python3
"""Collect public GOV.UK / MHRA metadata and create an UNPUBLISHED editorial triage file.

No external packages, no full-text storage, no LLM analysis and no automatic website publication.
"""
import argparse
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

TODAY = dt.datetime.now(dt.timezone.utc).date()
BASE_URL = "https://www.gov.uk/api/search.json"
PARAMS = {"q": "pharmaceutical", "count": "100", "order": "-public_timestamp",
          "filter_organisations": "medicines-and-healthcare-products-regulatory-agency"}
USER_AGENT = "CustomerExcellenceIntelligenceResearch/0.2 (public metadata, manual review)"
DEFAULT_OUTPUT = Path("data/candidates.json")

# Purposefully conservative *discovery* signals; never equate these with evidence quality.
PATTERNS = (
    ("AI & Transformation", r"\b(?:ai|artificial intelligence|machine learning|agentic|generative ai)\b", 90),
    ("Marketing & Governance", r"\b(?:advertis\w*|promot\w*|promotional|code of practice)\b", 85),
    ("Launch & Access", r"\b(?:mhra\s*[-–—]\s*nice|aligned pathway|earlier access|early access|patient access|launch readiness|integrated scientific advice)\b", 78),
    ("Evidence & Insights", r"\b(?:real[ -]world (?:evidence|data)|rwe|rwd|healthcare intelligence)\b", 74),
    ("Customer & Patient Experience", r"\b(?:patient experience|patient engagement|patient journey|patient support|hcp engagement)\b", 78),
    ("Processes & Operations", r"\b(?:commercial operations|process automation|workflow optimisation|digital transformation|operational excellence)\b", 74),
)
LOW_VALUE = re.compile(r"\b(?:class [234] medicines? recall|medicines? defect notification|falsified|counterfeit|fake|seizure|seized|arrested)\b", re.I)
ROUTINE = re.compile(r"\b(?:authorises?|approved for use|apply for a licence|licences? and registrations?|packaging|pharmacovigilance|clinical trials? for medicines|guidance on|portal|submission and assessment timetables)\b", re.I)

def clean(s):
    return re.sub(r"<[^>]*>", "", str(s or "")).strip()

def classify(item, today=TODAY, window_days=90):
    title = clean(item.get("title"))
    description = clean(item.get("description"))
    link = item.get("link") or item.get("url")
    if not title or not isinstance(link, str):
        return None
    if link.startswith("/"):
        link = "https://www.gov.uk" + link
    if not link.startswith("https://www.gov.uk/"):
        return None
    published = str(item.get("public_timestamp") or item.get("published") or "")[:10]
    try:
        pubdate = dt.date.fromisoformat(published)
    except ValueError:
        return None
    if pubdate > today:
        return None
    combined = title + " " + description
    tags = [name for name, pattern, score in PATTERNS if re.search(pattern, combined, re.I)]
    score = max((s for name, pattern, s in PATTERNS if re.search(pattern, combined, re.I)), default=20)
    if LOW_VALUE.search(title):
        score = min(score, 25)
    elif ROUTINE.search(title) and not tags:
        score = min(score, 30)
    age = (today - pubdate).days
    if age > window_days:
        triage = "archive_older"
    elif score >= 70:
        triage = "priority_review"
    elif score >= 50:
        triage = "standard_review"
    else:
        triage = "archive_low_relevance"
    return {"title": title, "url": link, "published": published,
            "source": "GOV.UK / MHRA", "description": description[:500],
            "tags": tags, "ai": "AI & Transformation" in tags,
            "uk": True, "triage": triage, "triage_score": score,
            "score_meaning": "heuristic discovery priority, NOT evidence quality or confirmed relevance",
            "status": "needs_editorial_review" if triage.endswith("review") else "not_selected_for_review"}

def fetch():
    url = BASE_URL + "?" + urllib.parse.urlencode(PARAMS)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    if not isinstance(data.get("results"), list):
        raise RuntimeError("Unexpected GOV.UK API response; results array missing")
    return data["results"]

def build(raw_records, today=TODAY):
    seen = set()
    out = []
    for raw in raw_records:
        rec = classify(raw, today=today)
        if rec and rec["url"] not in seen:
            seen.add(rec["url"])
            out.append(rec)
    counts = Counter(x["triage"] for x in out)
    return {"retrieved": today.isoformat(), "source_status": "ok", "review_required": True,
            "automatic_publication": False, "source_query": PARAMS,
            "total_records": len(out), "triage_counts": dict(sorted(counts.items())),
            "records": out}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Offline JSON: prior candidates.json or raw {results:[...]}")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.input:
        sample = json.loads(args.input.read_text(encoding="utf-8"))
        raw = sample.get("results", sample.get("records", []))
    else:
        raw = fetch()
    result = build(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Processed {result['total_records']} unique valid records")
    print("Triage:", json.dumps(result["triage_counts"], sort_keys=True))
    print("No records have been approved or published.")

if __name__ == "__main__":
    main()
