#!/usr/bin/env python3
"""Conservative second-stage triage of public publisher link metadata.

Does not verify publication date, article claims or evidence quality.
Does not approve or publish any intelligence item.
"""
import argparse
import json
import re
from pathlib import Path
from collections import Counter
from urllib.parse import urlsplit, unquote

TAGS = {
 "AI & Transformation": r"\b(?:ai|genai|agentic|artificial intelligence|generative|machine learning|automation|llm)\b",
 "Customer Strategy & Journeys": r"\b(?:hcp|healthcare professional|customer experience|customer journey|customer engagement|segmentation|nps|physician)\b",
 "Content & Omnichannel": r"\b(?:omnichannel|content supply chain|content operations|marketing automation|modular content|mlr|content review|generative engine optimiz|geo strategy|content strategy)\w*\b",
 "Events & Engagement": r"\b(?:congress|events?|conference|social listening)\b",
 "Patient Experience": r"\b(?:patient support|patient experience|patient journey|patient engagement|patient centricity)\b",
 "Processes & Operations": r"\b(?:commercial excellence|commercial operations|operating model|workflow|commercial effectiveness|efficiency|resource allocation|resource optimiz|execution|launch readiness|field force)\w*\b",
 "Channel Orchestration": r"\b(?:next.best.action|orchestrat|channel strategy|channel mix|field engagement|commercial crm|sales force|crm tech)\w*\b"
}
STRONG = re.compile(r"\b(?:omnichannel|customer engagement|customer experience|commercial excellence|commercial effectiveness|hcp|content supply chain|content operations|mlr|congress|customer journey|channel orchestrat\w*|benchmark\w*|crm|field engagement|patient support|agentic commercial|go.to.market|marketing|brand performance|brand success|resource allocation|budget allocation|fieldforce strategy|next.best.action)\b",re.I)
MODERATE = re.compile(r"\b(?:ai|artificial intelligence|agentic|engagement|content|commercial|customer|market share|budget|experience|operating model|patient)\b",re.I)
OFF_SCOPE = re.compile(r"\b(?:clinical trial|clinical research|clinical supply|clinical operations|ctms|pharmacovigilance|quality control|batch release|manufacturing|esource|e2b|drug discovery|clinical data|trial data|safety suite|study training|regulatory submissions|women.s health)\b",re.I)
RESOURCE_PREFIX = re.compile(r"^(?:(?:Press Release|White Paper|Article|Industry Report|Demo|eBook|Video|Webinar)\s+)?(?:Read Press Release|Read Report|Read White Paper|Read Article|Read More|Learn More|Watch Demo|Watch Video|Watch Webinar)\s+", re.I)
FORMAT_PREFIX = re.compile(r"^(Press Release|White Paper|Article|Industry Report|Demo|eBook|Video|Webinar)\b", re.I)

def normalise(row):
    source=row["source"]
    title=" ".join(row["title"].split())
    kind="unspecified"
    quality="source_anchor_text"
    if source=="Veeva":
        m=FORMAT_PREFIX.match(title)
        if m: kind=m.group(1)
        title=RESOURCE_PREFIX.sub("",title)
    if source=="ZS" and (title.startswith("/content/zs/") or title.startswith("/insights/")):
        slug=unquote(urlsplit(row["url"]).path.rstrip("/").split("/")[-1])
        title=slug.replace("-", " ").replace("_", " ").strip()
        quality="url_slug_placeholder_needs_verification"
    if source=="IQVIA" and len(title)>150 and "explore" in title.lower():
        quality="promotional_blurb_needs_verification"
    return title,quality,kind

def triage(row):
    title,quality,kind=normalise(row)
    source=row["source"]
    text=title.lower()
    tags=[name for name,pat in TAGS.items() if re.search(pat,text,re.I)]
    strong=bool(STRONG.search(text))
    moderate=bool(MODERATE.search(text))
    out_of_scope=bool(OFF_SCOPE.search(text))
    # Source-aware commercial intelligence signals: broad words like ROI/NPS alone
    # would be too permissive on generic publisher websites.
    source_specific = source == "Across Health" and bool(re.search(
        r"\\b(?:roi|nps|allocation|efficiency|effectiveness|share of voice|budget)\\b", text))
    strong = strong or source_specific
    survey_invitation = source == "Across Health" and bool(re.search(
        r"\\bmaturometer 2026\\b", text))
    content_type_hint = ("survey_invitation" if survey_invitation else
                         "publisher_report_label" if kind in ("Industry Report", "White Paper") else
                         "publisher_editorial_or_unknown")

    if out_of_scope and ("clinical operations" in text or "clinical trial" in text or not strong):
        queue="off_scope_archive"
        reason="clinical_or_regulatory_topic_outside_customer_excellence"
    elif strong:
        queue="priority_editorial_review"
        reason="direct_customer_excellence_topic"
    elif moderate and (source in ("Across Health","Indegene","ZS") or "AI & Transformation" in tags):
        queue="secondary_editorial_review"
        reason="adjacent_topic_or_transformation"
    else:
        queue="off_scope_archive"
        reason="no_clear_customer_excellence_signal"
    if survey_invitation:
        queue="secondary_editorial_review"
        reason="survey_invitation_not_published_findings"
    if quality=="promotional_blurb_needs_verification":
        queue="secondary_editorial_review"
        reason="promotional_text_not_a_verified_article_title"
    if quality=="url_slug_placeholder_needs_verification" and queue=="priority_editorial_review":
        reason+="; title_is_unverified_url_slug"
    return {
        "source":source,"title":title,"original_discovery_title":row["title"],
        "title_status":quality,"resource_format":kind,"url":row["url"],"topics":tags,
        "editorial_queue":queue,"reason":reason,
        "publication_date":None,"publication_date_status":"UNVERIFIED",
        "evidence_assessment":"NOT_PERFORMED",
        "source_content_status":"may_be_vendor_promotional_material",
        "content_type_hint":content_type_hint,
        "content_type_verification":"NOT_PERFORMED",
        "auto_publish":False
    }

def make_report(source_json):
    records=[triage(r) for r in source_json["records"]]
    counts=Counter(r["editorial_queue"] for r in records)
    by_source={}
    for source in sorted({r["source"] for r in records}):
        source_records=[r for r in records if r["source"]==source]
        by_source[source]={"total":len(source_records),**dict(Counter(r["editorial_queue"] for r in source_records))}
    return {"as_of":source_json.get("collected_at"),"input_total":len(records),
        "no_automatic_publication":True,"date_and_content_verification_needed":True,
        "queue_totals":dict(counts),"publisher_breakdown":by_source,"records":records}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    report=make_report(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Triage:",report["queue_totals"])
    for name,counts in report["publisher_breakdown"].items():
        print(name,counts)
    print("No records are approved or published.")

if __name__=="__main__":
    main()
