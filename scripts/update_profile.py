"""Build a GitHub profile from public contributions, using only the standard library."""

import json
import os
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


def chart(file, alt, width="100%"):
    base = f"https://raw.githubusercontent.com/{LOGIN}/{LOGIN}/main/assets"
    return f'''<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{base}/github_dark/{file}">
  <source media="(prefers-color-scheme: light)" srcset="{base}/github/{file}">
  <img alt="{alt}" src="{base}/github/{file}" width="{width}">
</picture>'''


def render(prs):
    prs = public_external(prs)
    merged = sorted((pr for pr in prs if pr["state"] == "MERGED"), key=lambda pr: pr["mergedAt"], reverse=True)
    opened = sorted((pr for pr in prs if pr["state"] == "OPEN"), key=lambda pr: pr["updatedAt"], reverse=True)
    closed = sorted((pr for pr in prs if pr["state"] == "CLOSED"), key=lambda pr: pr["updatedAt"], reverse=True)
    merged_projects = len({pr["repository"]["nameWithOwner"] for pr in merged})
    additions = sum(pr["additions"] for pr in merged)
    deletions = sum(pr["deletions"] for pr in merged)
    latest = max((pr["updatedAt"] for pr in prs), default=None)
    activity = f"Latest PR activity: {date(latest):%Y-%m-%d %H:%M} UTC+8" if latest else "No public upstream PRs yet"
    return f"""# Reacher

I build apps people crave, and contribute fixes back upstream.

## Open-source contributions

**{len(merged)} pull requests merged across {merged_projects} projects** · {len(opened)} open

[Merged PRs]({search('is:merged sort:updated-desc')}) · [Open PRs]({search('is:open sort:updated-desc')}) · [Full history](https://github.com/{LOGIN}/{LOGIN}/blob/main/HISTORY.md)

### Merged contributions

{rows(merged, merged=True)}
Merged code changes: **+{additions:,} / −{deletions:,} lines**

## What I build

| Project | Focus |
| --- | --- |
| **SupaSchool** | A teaching and learning platform |
| **Imminfo** | An immigration information website |
| **Blink Approval** | A homework review interface |

These projects have private source repositories. Also on GitHub: [GESP Exam Assessment](https://github.com/{LOGIN}/gesp-exam-assessment) · [Purrge Website](https://github.com/{LOGIN}/purrge-website).

## Contribution analytics

{chart('0-profile-details.svg', 'GitHub contribution trend over the past year, with account activity totals')}

{chart('1-repos-per-language.svg', 'Language distribution across public source repositories', '49%')}
{chart('4-productive-time.svg', 'Public commit activity by hour in Asia/Shanghai', '49%')}

<details>
<summary>More charts and what these numbers mean</summary>

{chart('3-stats.svg', 'Public GitHub stars, commits, pull requests, issues, and repositories contributed to', '49%')}
{chart('2-most-commit-language.svg', 'Languages associated with public commit activity', '49%')}

- **Contributions** count qualifying GitHub activity, including commits, issues, PRs, reviews, and repository creation. They do not count lines of code.
- **Merged PRs** show changes accepted by upstream projects. This homepage counts public external PRs separately from work in my own repositories.
- **Language charts** describe public repository code or commit activity, not proficiency. Private code is outside this integration's access.
- **Activity by hour** shows when public commits were made in Asia/Shanghai. It does not measure hours worked.
- **Projects** above are a portfolio. GitHub's separate Projects tab contains planning boards.

Charts are generated by [GitHub Profile Summary Cards](https://github.com/vn7n24fzkq/github-profile-summary-cards) and stored in this repository. [How GitHub counts contributions](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference).

</details>

### Open pull requests

{rows(opened)}
<details>
<summary>All-time totals and closed PRs</summary>

{len(prs)} PRs submitted to {len({pr['repository']['nameWithOwner'] for pr in prs})} public upstream repositories: {len(merged)} merged, {len(opened)} open, {len(closed)} closed without merging.

{rows(closed)}
Only public upstream repositories are counted. My own repositories and private work are excluded. Line counts sum merged PR diffs, including tests; they are not a count of unique lines. Closed PRs are not counted as merged.

</details>

<sub>{activity} · [Sync log](https://github.com/{LOGIN}/{LOGIN}/actions/workflows/update-profile.yml) · Refreshed hourly; GitHub scheduling may be delayed</sub>
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
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN or GITHUB_TOKEN is required")
    prs = fetch_pull_requests(token)
    # Both files are prepared only after every API page has succeeded.
    readme = render(prs)
    history = render_history(prs)
    data = json.dumps(prs, ensure_ascii=False, indent=2) + "\n"
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data/contributions.json").write_text(data)
    (ROOT / "README.md").write_text(readme)
    (ROOT / "HISTORY.md").write_text(history)
    print(f"Profile generated from {len(prs)} public external pull requests")


if __name__ == "__main__":
    main()
