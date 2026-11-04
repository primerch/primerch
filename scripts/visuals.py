"""Render profile artwork from verified public PRs and anonymous activity totals."""

import json
from collections import defaultdict
from html import escape
from pathlib import Path

from anonymous_activity import validate_activity

ROOT = Path(__file__).resolve().parents[1]
PALETTES = {
    'dark': {'bg': '#080e18', 'panel': '#0d1523', 'ink': '#edf4fc', 'muted': '#a4b6cb', 'accent': '#79ffe1', 'line': '#26364c'},
    'light': {'bg': '#f5f8fc', 'panel': '#ffffff', 'ink': '#102238', 'muted': '#50647d', 'accent': '#086b57', 'line': '#d5dfeb'},
}


def svg(width, height, palette, title, description, content):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<style>text{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;font-variant-numeric:tabular-nums}}.muted{{fill:{palette['muted']}}}</style>
<rect width="{width}" height="{height}" rx="12" fill="{palette['bg']}"/>
{content}</svg>'''


def text(x, y, value, size, fill, weight=400, anchor='start'):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>'


def wordmark(label, x, baseline, width, fill, marks):
    item = marks[label]
    scale = width / item['width']
    return f'<path d="{item["path"]}" transform="translate({x} {baseline}) scale({scale:.6f} {-scale:.6f})" fill="{fill}"/>'


def merged_prs(prs):
    for pr in prs:
        if pr['repository']['isPrivate'] or pr['repository']['owner']['login'].casefold() == 'primerch':
            raise ValueError('Artwork accepts only public upstream pull requests')
    return sorted((pr for pr in prs if pr['state'] == 'MERGED'), key=lambda pr: pr['mergedAt'], reverse=True)


def hero(prs, palette, marks, mobile=False):
    merged = merged_prs(prs)
    samples = merged[:3]
    width, height = (440, 312) if mobile else (900, 288)
    parts = [wordmark('REACHER', 32, 98 if mobile else 128, 376 if mobile else 548, palette['ink'], marks)]
    if mobile:
        parts += [text(32, 151, 'Build products.', 27, palette['ink'], 500), text(32, 185, 'Give fixes back.', 27, palette['accent'], 500)]
        for index, pr in enumerate(samples):
            x = 60 + index * 158
            parts.append(f'<path d="M32 231 H{x}" stroke="{palette["line"]}" fill="none" stroke-width="2"/>')
            parts.append(f'<circle cx="{x}" cy="231" r="7" fill="{palette["bg"]}" stroke="{palette["accent"]}" stroke-width="2"/>')
            label = pr['repository']['nameWithOwner'].split('/', 1)[1]
            label = label[:13] + '…' if len(label) > 14 else label
            parts += [text(x, 263, label, 17, palette['muted'], anchor='middle'), text(x, 287, f"#{pr['number']}", 18, palette['accent'], 500, 'middle')]
    else:
        parts += [text(32, 181, 'Build products. Give fixes back.', 27, palette['ink'], 500), text(32, 246, 'Teaching platforms. Product work. Open source.', 16, palette['muted'])]
        for index, pr in enumerate(samples):
            y = 60 + index * 83
            parts.append(f'<path d="M618 143 C652 143 652 {y} 688 {y}" stroke="{palette["accent"]}" fill="none" stroke-width="2"/>')
            parts.append(f'<circle cx="688" cy="{y}" r="7" fill="{palette["bg"]}" stroke="{palette["accent"]}" stroke-width="2"/>')
            label = pr['repository']['nameWithOwner'].split('/', 1)[1]
            label = label[:17] + '…' if len(label) > 18 else label
            parts += [text(710, y - 6, label, 17, palette['ink'], 500), text(710, y + 20, f"#{pr['number']} · merged", 14, palette['muted'])]
        parts.append(f'<circle cx="618" cy="143" r="5" fill="{palette["accent"]}"/>')
    description = f"Reacher. Build products. Give fixes back. {len(merged)} verified public upstream merges."
    return svg(width, height, palette, 'Reacher', description, '\n'.join(parts))


def products(palette, marks, mobile=False):
    entries = (
        ('SupaSchool', ('A teaching and', 'learning platform'), 190),
        ('Imminfo', ('An immigration', 'information website'), 135),
        ('Blink Approval', ('A homework', 'review interface'), 222),
    )
    width, height = (440, 360) if mobile else (900, 184)
    parts = []
    for index, (name, lines, logo_width) in enumerate(entries):
        x, y = (32, 38 + index * 112) if mobile else (32 + index * 300, 36)
        if index:
            if mobile:
                parts.append(f'<path d="M32 {y-22} H408" stroke="{palette["line"]}"/>')
            else:
                parts.append(f'<path d="M{x-16} 32 V152" stroke="{palette["line"]}"/>')
        parts.append(wordmark(name, x, y + 23, logo_width if not mobile else logo_width * 1.15, palette['ink'], marks))
        if mobile:
            parts.append(text(x, y + 57, ' '.join(lines), 19, palette['muted']))
        else:
            parts += [text(x, y + 64, lines[0], 18, palette['muted']), text(x, y + 90, lines[1], 18, palette['muted'])]
    return svg(width, height, palette, 'Selected products', 'SupaSchool: a teaching and learning platform. Imminfo: an immigration information website. Blink Approval: a homework review interface. Source repositories remain private.', '\n'.join(parts))


def activity_chart(activity, palette, mobile=False):
    validate_activity(activity)
    totals = defaultdict(int)
    for day, count in activity['days']:
        totals[day[:7]] += count
    values = sorted(totals.items())
    width, height = (440, 272) if mobile else (900, 232)
    left, right, top, bottom = 32, width - 32, 82, height - 48
    parts = [text(left, 36, 'A year of building', 22 if mobile else 20, palette['ink'], 500), text(right, 38, f"{activity['lastYearContributions']:,}", 27, palette['accent'], 500, 'end')]
    peak = max((value for _, value in values), default=1) or 1
    step = (right - left) / max(len(values), 1)
    for index, (month, value) in enumerate(values):
        x = left + index * step
        bar_height = (bottom - top) * value / peak
        color = palette['accent'] if value == peak and value > 0 else palette['muted']
        parts.append(f'<rect x="{x+3:.2f}" y="{bottom-bar_height:.2f}" width="{max(step-8,2):.2f}" height="{max(bar_height,1):.2f}" rx="2" fill="{color}" opacity="{1 if value == peak else .52}"/>')
        if index == 0 or index == len(values) - 1 or index % (4 if mobile else 2) == 0:
            label = month[2:4] + '/' + month[5:7]
            parts.append(text(x + step / 2, bottom + 28, label, 17 if mobile else 14, palette['muted'], anchor='middle'))
    parts.append(f'<path d="M{left} {bottom+1} H{right}" stroke="{palette["line"]}"/>')
    return svg(width, height, palette, 'GitHub contribution calendar', f"{activity['lastYearContributions']:,} contributions in the past year, including {activity['anonymousPrivateLastYear']:,} anonymous private contributions. Bars group GitHub's returned calendar by month; boundary months are partial.", '\n'.join(parts))


def build_visuals(prs, activity, destination=ROOT / 'assets/brand'):
    validate_activity(activity)
    marks = json.loads((ROOT / 'assets/brand/wordmarks.json').read_text())
    destination.mkdir(parents=True, exist_ok=True)
    for theme, palette in PALETTES.items():
        for mobile in (False, True):
            suffix = f'{theme}-mobile' if mobile else theme
            for name, output in (
                ('hero', hero(prs, palette, marks, mobile)),
                ('products', products(palette, marks, mobile)),
                ('activity', activity_chart(activity, palette, mobile)),
            ):
                (destination / f'{name}-{suffix}.svg').write_text(output)


if __name__ == '__main__':
    prs = json.loads((ROOT / 'data/contributions.json').read_text())
    activity = json.loads((ROOT / 'data/activity.json').read_text())
    build_visuals(prs, activity)
    print('Rendered responsive artwork using public PRs and anonymous contribution counts')
