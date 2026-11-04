"""Build a GitHub profile from public contributions, using only the standard library."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
LOGIN = "primerch"
QUERY = """
query($login:String!, $cursor:String) {
  user(login:$login) {
    pullRequests(first:100, after:$cursor, orderBy:{field:CREATED_AT,direction:DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url state mergedAt createdAt updatedAt additions deletions
        repository { nameWithOwner isPrivate owner { login } }
      }
    }
  }
}
"""

# Human summaries of already-public PRs. Future contributions fall back to their titles.
SUMMARIES = {
    "https://github.com/convex/rag/pull/120": "Fix a type-only import for build compatibility",
    "https://github.com/ChristopherVR/ooxml/pull/241": "Preserve fills and strokes after PPTX animations",
    "https://github.com/ChristopherVR/pptx-viewer/pull/185": "Restore authored PowerPoint playback and rendering",
    "https://github.com/opentypejs/opentype.js/pull/883": "Route ES module consumers to the ESM build",
    "https://github.com/convex/better-auth/pull/460": "Keep token refresh pending during temporary outages",
    "https://github.com/convex/convex-backend/pull/631": "Fix auth configuration races during token retrieval",
    "https://github.com/brijeshb42/monaco-vim/pull/176": "Handle Vim keys before native editor shortcuts",
}


def public_external(prs, login=LOGIN):
    """Never persist private repositories or count our own repositories as upstream."""
    return [
        pr for pr in prs
        if not pr["repository"]["isPrivate"]
        and pr["repository"]["owner"]["login"].casefold() != login.casefold()
    ]


def fetch_pull_requests(token, login=LOGIN):
    cursor = None
    results = []
    while True:
        payload = {"query": QUERY, "variables": {"login": login, "cursor": cursor}}
        request = Request(
            "https://api.github.com/graphql",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": f"{login}-profile",
            },
        )
        with urlopen(request, timeout=45) as response:
            data = json.load(response)
        if data.get("errors"):
            raise RuntimeError("GitHub rejected the contribution query; keeping existing profile")
        connection = data["data"]["user"]["pullRequests"]
        results.extend(public_external(connection["nodes"], login))
        if not connection["pageInfo"]["hasNextPage"]:
            return results
        next_cursor = connection["pageInfo"]["endCursor"]
        if not next_cursor or next_cursor == cursor:
            raise RuntimeError("GitHub returned an invalid pagination cursor")
        cursor = next_cursor


def text(value):
    for old, new in (("\\", "\\\\"), ("|", "\\|"), ("[", "\\["), ("]", "\\]"), ("<", "&lt;"), (">", "&gt;")):
        value = value.replace(old, new)
    return " ".join(value.splitlines())


def date(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Shanghai"))


def search(query):
    return "https://github.com/pulls?q=" + quote(f"is:pr author:{LOGIN} is:public -user:{LOGIN} {query}", safe="")


def rows(prs, merged=False, limit=10, full_names=False):
    if not prs:
        return "No pull requests here yet.\n"
    headers = "| Project / PR | Contribution | Merged |\n| --- | --- | --- |\n" if merged else "| Project / PR | Contribution |\n| --- | --- |\n"
    output = []
    for pr in prs[:limit] if limit else prs:
        name = pr["repository"]["nameWithOwner"]
        project = text(name if full_names else name.split("/", 1)[1])
        summary = text(SUMMARIES.get(pr["url"], pr["title"]))
        row = f"| [{project} #{pr['number']}]({pr['url']}) | {summary} |"
        if merged:
            row += f" {date(pr['mergedAt']):%Y-%m-%d} |"
        output.append(row)
    return headers + "\n".join(output) + "\n"


def artwork(name, alt, width="100%", category='brand', responsive=True):
    base = f"https://raw.githubusercontent.com/{LOGIN}/{LOGIN}/main/assets"
    mobile = f'''  <source media="(prefers-color-scheme: dark) and (max-width: 600px)" srcset="{base}/{category}/{name}-dark-mobile.svg">
  <source media="(prefers-color-scheme: light) and (max-width: 600px)" srcset="{base}/{category}/{name}-light-mobile.svg">
''' if responsive else ''
    return f'''<picture>
{mobile}  <source media="(prefers-color-scheme: dark)" srcset="{base}/{category}/{name}-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="{base}/{category}/{name}-light.svg">
  <img alt="{alt}" src="{base}/{category}/{name}-light.svg" width="{width}">
</picture>'''


def render(prs, activity=None):
    prs = public_external(prs)
    merged = sorted((pr for pr in prs if pr["state"] == "MERGED"), key=lambda pr: pr["mergedAt"], reverse=True)
    opened = sorted((pr for pr in prs if pr["state"] == "OPEN"), key=lambda pr: pr["updatedAt"], reverse=True)
    closed = sorted((pr for pr in prs if pr["state"] == "CLOSED"), key=lambda pr: pr["updatedAt"], reverse=True)
    merged_projects = len({pr["repository"]["nameWithOwner"] for pr in merged})
    additions = sum(pr["additions"] for pr in merged)
    deletions = sum(pr["deletions"] for pr in merged)
    latest = max((pr["updatedAt"] for pr in prs), default=None)
    latest_pr = f"Latest PR activity: {date(latest):%Y-%m-%d %H:%M} UTC+8" if latest else "No public upstream PRs yet"
    activity = activity or {'lifetimeContributions': 0, 'lastYearContributions': 0, 'anonymousPrivateLastYear': 0, 'asOf': 'not yet refreshed'}
    pr_word = 'pull request' if len(merged) == 1 else 'pull requests'
    project_word = 'project' if merged_projects == 1 else 'projects'
    return f"""{artwork('hero', 'Reacher. Build products. Give fixes back. Selected verified upstream merges.')}

**{activity['lifetimeContributions']:,} lifetime contributions.** Public work and anonymous private activity, counted together.

[Merged upstream ({len(merged)})]({search('is:merged sort:updated-desc')}) · [Open PRs ({len(opened)})]({search('is:open sort:updated-desc')}) · [Full contribution history](https://github.com/{LOGIN}/{LOGIN}/blob/main/HISTORY.md)

## Built by me

{artwork('products', 'SupaSchool: a teaching and learning platform. Imminfo: an immigration information website. Blink Approval: a homework review interface.')}

Source stays private. Also on GitHub: [GESP Exam Assessment](https://github.com/{LOGIN}/gesp-exam-assessment) · [Purrge Website](https://github.com/{LOGIN}/purrge-website).

## GitHub, in numbers

{artwork('stats', 'GitHub Stats Extended: lifetime contributions including anonymous private work; public pull requests and merged PRs', '400', 'extended', False)}
{artwork('languages', 'GitHub Stats Extended: language distribution by public source-code bytes; private code excluded', '400', 'extended', False)}

Lifetime contributions include anonymous private activity. The language chart covers public source code.

{artwork('activity', f"{activity['lastYearContributions']:,} contributions over the past year, including {activity['anonymousPrivateLastYear']:,} anonymous private contributions")}

**{activity['lastYearContributions']:,} contributions in the past year**, including **{activity['anonymousPrivateLastYear']:,} anonymous private contributions**. Private repository names, commits, and source code stay private.

## Accepted upstream

**{len(merged)} {pr_word} merged across {merged_projects} {project_word}** · {len(opened)} open

{rows(merged, merged=True)}
Merged code changes: **+{additions:,} / −{deletions:,} lines**

<details>
<summary>{len(opened)} open upstream pull requests</summary>

{rows(opened)}
</details>

<details>
<summary>How the numbers work</summary>

- **Lifetime contributions** count qualifying GitHub activity across all contribution years, including the anonymized private activity shared on my profile.
- **Past-year activity** covers GitHub's trailing-year contribution calendar. Boundary months in the monthly chart are partial.
- **Anonymous private contributions** are aggregate activity counts. No private repository names, commit messages, paths, or code are published.
- **Public PRs** and **Public merged PRs** on the Stats Extended card cover public repositories. The upstream section below the charts specifically excludes my own repositories.
- **Public language mix** counts public code bytes, excluding forks and this profile automation repository. It does not measure proficiency or expose private code.
- **Merged code changes** sum accepted upstream PR diffs, including tests. They are not a deduplicated count of authored lines.

Statistics are generated by [GitHub Stats Extended](https://github.com/stats-organization/github-stats-extended) with its [official Action](https://github.com/stats-organization/github-readme-stats-action). Saved charts stay visible between updates. [GitHub's contribution rules](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference).

</details>

<details>
<summary>Full public upstream totals and closed PRs</summary>

{len(prs)} PRs submitted to {len({pr['repository']['nameWithOwner'] for pr in prs})} public upstream repositories: {len(merged)} merged, {len(opened)} open, {len(closed)} closed without merging.

{rows(closed)}
These PR totals count public upstream repositories. My own repositories and private PRs are excluded here; anonymous private activity is included in the contribution totals above. Closed PRs are not counted as merged.

</details>

<sub>Data refreshed {activity['asOf']} · {latest_pr} · [Hourly sync](https://github.com/{LOGIN}/{LOGIN}/actions/workflows/update-profile.yml)</sub>
"""


def render_history(prs):
    prs = public_external(prs)
    merged = sorted((pr for pr in prs if pr["state"] == "MERGED"), key=lambda pr: pr["mergedAt"], reverse=True)
    opened = sorted((pr for pr in prs if pr["state"] == "OPEN"), key=lambda pr: pr["updatedAt"], reverse=True)
    closed = sorted((pr for pr in prs if pr["state"] == "CLOSED"), key=lambda pr: pr["updatedAt"], reverse=True)
    return f"""# Contribution history

[Back to my profile](https://github.com/{LOGIN})

Every public upstream PR, with the most recent merges first. This page refreshes automatically with the profile. A merged PR moves from the open list into the merged history on the next successful sync.

## Merged contributions

{rows(merged, merged=True, limit=None, full_names=True)}
## Open pull requests

{rows(opened, limit=None, full_names=True)}
## Closed without merging

{rows(closed, limit=None, full_names=True)}
Public upstream repositories only. The homepage shows the latest ten entries per section; this history has no entry limit. Earlier snapshots remain in this repository's Git history.
"""


def main():
    if '--render-only' in sys.argv:
        prs = json.loads((ROOT / 'data/contributions.json').read_text())
        activity = json.loads((ROOT / 'data/activity.json').read_text())
        from visuals import build_visuals
        build_visuals(prs, activity)
        (ROOT / 'README.md').write_text(render(prs, activity))
        return
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN or GITHUB_TOKEN is required")
    prs = fetch_pull_requests(token)
    # Both files are prepared only after every API page has succeeded.
    history = render_history(prs)
    data = json.dumps(prs, ensure_ascii=False, indent=2) + "\n"
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data/contributions.json").write_text(data)
    (ROOT / "HISTORY.md").write_text(history)
    if (ROOT / 'data/activity.json').exists() and (ROOT / 'assets/extended/stats-dark.svg').exists():
        from visuals import build_visuals
        activity = json.loads((ROOT / 'data/activity.json').read_text())
        build_visuals(prs, activity)
        (ROOT / 'README.md').write_text(render(prs, activity))
    print(f"Profile generated from {len(prs)} public external pull requests")


if __name__ == "__main__":
    main()
