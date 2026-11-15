"""Bounded diagnostics for official collection alternatives; no proxying or identity spoofing."""
import json
from urllib.error import HTTPError
from collect import fetch, PoliteFetch

ROUTES = [
    ('parliament-report-api', 'https://committees-api.parliament.uk/api/Publications/55076', True),
    ('parliament-discovery-api', 'https://committees-api.parliament.uk/api/CommitteeBusiness/8765/Publications/Summary', True),
    ('parliament-report-catalogue', 'https://api.parliament.uk/committees/publications/55076', False),
    ('parliament-news', 'https://committees.parliament.uk/work/8765/reforming-the-water-sector/news/', False),
    ('ofwat-publication', 'https://www.ofwat.gov.uk/publication/water-company-operational-performance-report-2025-26/', False),
    ('joint-report-mirror', 'https://www.gov.uk/government/news/regulators-publish-first-joint-report-on-water-industry-performance-giving-the-public-a-clearer-picture-of-company-performance', False),
    ('joint-report-pdf', 'https://assets.publishing.service.gov.uk/media/6ada0fd1d798ae11e9bc5bd0/Water-industry-performance-insights-A-joint-water-regulator-report.pdf', False),
]


def describe(value, path=''):
    """Print schema keys, titles and document URLs, without dumping entire response text."""
    output = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in ('id', 'title', 'name', 'url', 'link', 'filedataformat', 'file', 'documents', 'publicationdate'):
                output.append((path + '/' + key, item if not isinstance(item, (dict, list)) else type(item).__name__))
            output.extend(describe(item, path + '/' + key))
    elif isinstance(value, list):
        for i, item in enumerate(value[:20]):
            output.extend(describe(item, path + '/' + str(i)))
    return output[:100]


if __name__ == '__main__':
    polite = PoliteFetch()
    for name, url, official_api in ROUTES:
        try:
            # Parliament explicitly publishes these machine-access endpoints in its OpenAPI spec.
            # HTML/PDF collection still follows robots policy, and any API denial remains a failure.
            status, headers, body = (fetch if official_api else polite)(url, {'Accept': 'application/json'} if official_api else {})
            record = {'route': name, 'url': url, 'status': status, 'bytes': len(body)}
            if official_api and status == 200:
                record['schema'] = describe(json.loads(body))
            print(json.dumps(record), flush=True)
        except (OSError, ValueError) as exc:
            print(json.dumps({'route': name, 'url': url, 'error': str(exc)}), flush=True)
