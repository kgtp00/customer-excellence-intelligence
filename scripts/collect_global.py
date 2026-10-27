#!/usr/bin/env python3
"""Discover metadata-only candidate articles from public publisher listing pages.

Manual, review-only experiment. Never publish. One page per source, honours robots rules,
limits response size, records failures per source, and stores only titles and URLs.
"""
import datetime as dt
import html
from html.parser import HTMLParser
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit, urlunsplit, quote, unquote
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

USER_AGENT = "CustomerExcellenceIntelligenceLab/0.1 (metadata-only source discovery; research prototype)"
TIMEOUT = 15
MAX_BYTES = 1_500_000
NOW = dt.datetime.now(dt.timezone.utc).date().isoformat()
OUT = Path('data/global-review-candidates.json')
SOURCES = (
    ('Across Health', 'https://across.health/resources/expert-insights/', ('/resources/expert-insights/',)),
    ('ZS', 'https://www.zs.com/industry-insights/pharmaceuticals-biotech', ('/insights/',)),
    ('ZS', 'https://www.zs.com/capabilities/data-digital-technology', ('/insights/',)),
    ('IQVIA', 'https://www.iqvia.com/locations/emea/blogs', ('/locations/emea/blogs/', '/blogs/')),
    ('Veeva', 'https://www.veeva.com/resources/', ('/resources/', '/blog/')),
    ('DT Consulting', 'https://dt-consulting.com/latest-insights/', ('/latest-insights/',)),
    ('Indegene', 'https://www.indegene.com/insights/reports', ('/insights/reports/',)),
)
TOPICS = (
    ('AI & Transformation', re.compile(r'\b(?:ai|genai|artificial intelligence|agentic|llm|generative|automation|machine learning)\b', re.I)),
    ('Customer Strategy & Journeys', re.compile(r'\b(?:hcp|customer|physician|healthcare professional|journey|segmentation|experience|digital health|patient engagement)\b', re.I)),
    ('Content & Omnichannel', re.compile(r'\b(?:omnichannel|content|modular|digital engagement|marketing|mlr|campaign|personalization|personalisation)\b', re.I)),
    ('Events & Engagement', re.compile(r'\b(?:congress|event|conference|engagement|medical meeting)\b', re.I)),
    ('Patient Experience', re.compile(r'\b(?:patient|support program|support programme|patient journey|patient centric)\b', re.I)),
    ('Processes & Operations', re.compile(r'\b(?:operations|workflow|efficiency|launch|commercial excellence|operating model|governance|effectiveness)\b', re.I)),
    ('Channel Orchestration', re.compile(r'\b(?:next.best.action|channel|orchestrat|field force|sales force|engagement model|targeting)\w*\b', re.I)),
)
STOP_TITLES = {'expert insights', 'insights', 'reports', 'read more', 'read article', 'learn more', 'resources', 'latest insights', 'blog', 'blogs', 'home', 'all insights'}

class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self._href = None
        self._parts = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self._href = dict(attrs).get('href')
            self._parts = []
    def handle_data(self, data):
        if self._href is not None:
            self._parts.append(data)
    def handle_endtag(self, tag):
        if tag == 'a' and self._href is not None:
            self.anchors.append((self._href, ' '.join(' '.join(self._parts).split())))
            self._href = None
            self._parts = []

def canonical_url(href, listing):
    """Only accept source-local HTTPS links; drop navigation fragments and query strings."""
    if not href or href.startswith(('mailto:', 'javascript:', '#', 'tel:')):
        return None
    url = urljoin(listing, href)
    parts = urlsplit(url)
    origin = urlsplit(listing)
    if parts.scheme != 'https' or parts.hostname != origin.hostname:
        return None
    path = unquote(parts.path).rstrip('/')
    if origin.hostname == 'www.zs.com' and path.startswith('/content/zs/en/insights/'):
        path = path.replace('/content/zs/en/insights/', '/insights/', 1)
    return urlunsplit(('https', origin.netloc, quote(path, safe='/%-._~'), '', ''))

def extract(source, listing, prefixes, html_data):
    parser = AnchorParser()
    parser.feed(html_data)
    results = []
    seen = set()
    landing = canonical_url(listing, listing)
    for href, label in parser.anchors:
        url = canonical_url(href, listing)
        if not url or url == landing or url in seen:
            continue
        path = urlsplit(url).path
        if not any(path.startswith(prefix) and len(path) > len(prefix) + 3 for prefix in prefixes):
            continue
        title = html.unescape(label.strip())
        if len(title) < 18 or len(title) > 240 or title.casefold() in STOP_TITLES:
            continue
        if re.search(r'\b(?:privacy|cookie|terms|subscribe|contact us)\b', title, re.I):
            continue
        tags = [name for name, match in TOPICS if match.search(title)]
        seen.add(url)
        results.append({'source': source, 'title': title, 'url': url,
                        'publication_date': None, 'date_status': 'unknown_do_not_assume_current',
                        'discovered_at': NOW, 'topics': tags,
                        'review_priority': 'topic_match' if tags else 'manual_screen',
                        'status': 'needs_editorial_review', 'listing_page': listing})
    return results

def fetch_bytes(url):
    req = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xml;q=0.9,*/*;q=0.5'})
    with urlopen(req, timeout=TIMEOUT) as r:
        data = r.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('response_size_limit_exceeded')
        return data, r.headers.get_content_charset() or 'utf-8'

def robots_allowed(url):
    parts = urlsplit(url)
    robots_url = f'{parts.scheme}://{parts.netloc}/robots.txt'
    try:
        raw, charset = fetch_bytes(robots_url)
        parser = RobotFileParser(robots_url)
        parser.parse(raw.decode(charset, errors='replace').splitlines())
        return parser.can_fetch(USER_AGENT, url), 'robots_checked'
    except HTTPError as e:
        if e.code == 404:
            return True, 'robots_missing_404'
        return False, f'robots_http_{e.code}'
    except Exception as exc:
        return False, f'robots_unavailable_{type(exc).__name__}'

def run(fetch=fetch_bytes, allow=robots_allowed):
    records = {}
    checks = []
    for source, listing, prefixes in SOURCES:
        ok, robots_status = allow(listing)
        if not ok:
            checks.append({'source': source, 'listing': listing, 'status': 'skipped', 'reason': robots_status})
            continue
        try:
            content, charset = fetch(listing)
            result = extract(source, listing, prefixes, content.decode(charset, errors='replace'))
            new = 0
            for row in result:
                if row['url'] not in records:
                    records[row['url']] = row
                    new += 1
            checks.append({'source': source, 'listing': listing, 'status': 'ok', 'discovered_candidates': new, 'robots': robots_status})
        except Exception as exc:
            checks.append({'source': source, 'listing': listing, 'status': 'failed', 'reason': type(exc).__name__ + ': ' + str(exc)[:150]})
    rows = list(records.values())
    return {'collected_at': NOW, 'automatic_publication': False, 'review_required': True,
            'collection_scope': 'metadata_and_links_only', 'total_candidates': len(rows),
            'source_checks': checks, 'records': rows}

def main():
    output = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Candidate URLs:', output['total_candidates'])
    for check in output['source_checks']:
        print(f"{check['source']}: {check['status']} {check.get('discovered_candidates',check.get('reason',''))}")
    if not any(s['status']=='ok' for s in output['source_checks']):
        print('No source succeeded; inspect the collection report.', file=sys.stderr)
        return 1
    print('No candidates were published. Dates remain unverified.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
