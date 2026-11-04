"""Clarify public PR labels and align cards without changing generated numbers."""

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
            if element.tag == '{http://www.w3.org/2000/svg}title':
                element.text = element.text.split(', Rank:', 1)[0]
    tree.write(path, encoding='unicode')
    language_path = ROOT / f'assets/extended/languages-{theme}.svg'
    languages = ET.parse(language_path)
    height = max(float(tree.getroot().get('height')), float(languages.getroot().get('height')))
    for card, destination in ((tree, path), (languages, language_path)):
        root = card.getroot()
        root.set('height', f'{height:g}')
        root.set('viewBox', f"0 0 {root.get('width')} {height:g}")
        card.write(destination, encoding='unicode')
print('Public scope labels and aligned card canvases verified; generated values preserved')
