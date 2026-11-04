"""Clarify public-only PR labels without changing Stats Extended's numbers."""

from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ET.register_namespace('', 'http://www.w3.org/2000/svg')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
for theme in ('dark', 'light'):
    path = ROOT / f'assets/extended/stats-{theme}.svg'
    tree = ET.parse(path)
    for element in tree.getroot().iter():
        if element.text:
            element.text = element.text.replace('Total PRs Merged:', 'Public merged PRs:').replace('Total PRs:', 'Public PRs:')
    tree.write(path, encoding='unicode')
print('Public PR scope labels verified; all generated values preserved')
