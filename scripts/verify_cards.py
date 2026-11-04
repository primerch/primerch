"""Verify complete assets, anonymous-only activity, and private-inclusive totals."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

from anonymous_activity import validate_activity

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'
activity = json.loads((ROOT / 'data/activity.json').read_text())
validate_activity(activity)
prs = json.loads((ROOT / 'data/contributions.json').read_text())
for pr in prs:
    if pr['repository']['isPrivate'] or pr['repository']['owner']['login'].casefold() == 'primerch':
        raise SystemExit('Private or owned PR records must not be published in the upstream dataset')

files = [ROOT / f'assets/extended/{name}-{theme}.svg' for theme in ('dark', 'light') for name in ('stats', 'languages')]
files += [ROOT / f'assets/brand/{name}-{theme}{size}.svg' for name in ('hero', 'products', 'activity') for theme in ('dark', 'light') for size in ('', '-mobile')]
for path in files:
    root = ET.parse(path).getroot()
    if root.tag != SVG + 'svg':
        raise SystemExit(f'Invalid SVG: {path}')
    content = ' '.join(root.itertext()).lower()
    if any(message in content for message in ('something went wrong', 'api rate limit exceeded', 'error fetching', 'resource not accessible')):
        raise SystemExit(f'Error card rejected: {path}')
    if any(element.tag in (SVG + 'script', SVG + 'foreignObject') for element in root.iter()):
        raise SystemExit(f'Unexpected active content in {path}')
    if path.name.startswith('stats-'):
        labels = [''.join(item.itertext()).strip() for item in root.iter(SVG + 'text')]
        if 'Total Contributions:' not in labels or 'Public merged PRs:' not in labels:
            raise SystemExit('Stats card is missing required contribution metrics or scope labels')
        value = labels[labels.index('Total Contributions:') + 1]
        total = int(value.replace(',', '').replace(' ', ''))
        if total < activity['lastYearContributions'] or total < activity['anonymousPrivateLastYear']:
            raise SystemExit('Stats card does not cover the verified private-inclusive activity totals')

readme = (ROOT / 'README.md').read_text()
if 'github-profile-summary-cards' in readme or 'github-readme-stats.vercel.app' in readme:
    raise SystemExit('A retired statistics service is still referenced')
print(f"Verified {len(files)} SVGs and anonymous-only activity: {activity['anonymousPrivateLastYear']:,} private contributions included")
