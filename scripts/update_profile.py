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
    "https://github.com/convex/rag/pull/120": "修正类型导入，解决构建兼容问题",
    "https://github.com/ChristopherVR/ooxml/pull/241": "保留 PPTX 动画结束后的填充与描边",
    "https://github.com/ChristopherVR/pptx-viewer/pull/185": "修复 PowerPoint 动画播放与渲染",
    "https://github.com/opentypejs/opentype.js/pull/883": "让 ES module 使用正确的 ESM 构建",
    "https://github.com/convex/better-auth/pull/460": "避免短暂网络故障中断登录令牌刷新",
    "https://github.com/convex/convex-backend/pull/631": "修复异步令牌获取中的认证配置竞态",
    "https://github.com/brijeshb42/monaco-vim/pull/176": "让 Vim 按键先于编辑器原生快捷键处理",
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


def rows(prs, merged=False):
    if not prs:
        return "暂时没有记录\n"
    headers = "| 项目 / PR | 做了什么 | 合并日期 |\n| --- | --- | --- |\n" if merged else "| 项目 / PR | 做了什么 |\n| --- | --- |\n"
    output = []
    for pr in prs[:10]:
        project = text(pr["repository"]["nameWithOwner"])
        summary = text(SUMMARIES.get(pr["url"], pr["title"]))
        row = f"| [{project} #{pr['number']}]({pr['url']}) | {summary} |"
        if merged:
            row += f" {date(pr['mergedAt']):%Y-%m-%d} |"
        output.append(row)
    return headers + "\n".join(output) + "\n"


def render(prs):
    prs = public_external(prs)
    merged = sorted((pr for pr in prs if pr["state"] == "MERGED"), key=lambda pr: pr["mergedAt"], reverse=True)
    opened = sorted((pr for pr in prs if pr["state"] == "OPEN"), key=lambda pr: pr["updatedAt"], reverse=True)
    closed = sorted((pr for pr in prs if pr["state"] == "CLOSED"), key=lambda pr: pr["updatedAt"], reverse=True)
    merged_projects = len({pr["repository"]["nameWithOwner"] for pr in merged})
    additions = sum(pr["additions"] for pr in merged)
    deletions = sum(pr["deletions"] for pr in merged)
    latest = max((pr["updatedAt"] for pr in prs), default=None)
    activity = f"最近 PR 动态：{date(latest):%Y-%m-%d %H:%M}（北京时间）" if latest else "尚无公开外部 PR"
    return f"""# Reacher

I build apps people crave, and contribute fixes back upstream.

## 开源贡献

**{len(merged)} 个 PR 已合并到 {merged_projects} 个项目** · {len(opened)} 个正在等待合并

[查看已合并 PR]({search('is:merged sort:updated-desc')}) · [查看待合并 PR]({search('is:open sort:updated-desc')})

### 已被项目采纳

{rows(merged, merged=True)}
已合并 PR 的代码改动合计：**+{additions:,} / −{deletions:,} 行**

### 等待下一次合并

{rows(opened)}
<details>
<summary>完整统计与已关闭记录</summary>

累计向 {len({pr['repository']['nameWithOwner'] for pr in prs})} 个公开外部仓库提交 {len(prs)} 个 PR：{len(merged)} 个已合并、{len(opened)} 个待合并、{len(closed)} 个已关闭未合并。

{rows(closed)}
只统计公开外部仓库；自己的仓库和私有项目不计入。代码行数按已合并 PR 的 diff 汇总，包含测试，不代表去重后的代码总量。已关闭不等于已合并。

</details>

<sub>{activity} · [自动同步记录](https://github.com/{LOGIN}/{LOGIN}/actions/workflows/update-profile.yml) · 计划每小时更新，GitHub 调度可能延迟</sub>
"""


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN or GITHUB_TOKEN is required")
    prs = fetch_pull_requests(token)
    # Both files are prepared only after every API page has succeeded.
    readme = render(prs)
    data = json.dumps(prs, ensure_ascii=False, indent=2) + "\n"
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data/contributions.json").write_text(data)
    (ROOT / "README.md").write_text(readme)
    print(f"Profile generated from {len(prs)} public external pull requests")


if __name__ == "__main__":
    main()
