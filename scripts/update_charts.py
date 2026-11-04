"""Save public Summary Cards as durable repository assets; no personal token needed."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
CARDS = (
    ("profile-details", "0-profile-details.svg"),
    ("repos-per-language", "1-repos-per-language.svg"),
    ("most-commit-language", "2-most-commit-language.svg"),
    ("stats", "3-stats.svg"),
    ("productive-time", "4-productive-time.svg"),
)


def fetch_card(item):
    theme, card, name = item
    query = urlencode({"username": "primerch", "theme": theme, "name": "Reacher", "utcOffset": 8, "timeZone": "Asia/Shanghai", "exclude_repos": "primerch"})
    request = Request(
        f"https://github-profile-summary-cards.vercel.app/api/cards/{card}?{query}",
        headers={"User-Agent": "primerch-profile-charts", "Accept": "image/svg+xml"},
    )
    with urlopen(request, timeout=60) as response:
        data = response.read(2_000_000)
        if "image/svg+xml" not in response.headers.get("Content-Type", ""):
            raise RuntimeError(f"Chart service did not return an SVG: {theme}/{card}")
    root = ElementTree.fromstring(data)
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise RuntimeError(f"Invalid SVG: {theme}/{card}")
    content = " ".join(root.itertext()).lower()
    if any(message in content for message in ("something went wrong", "api rate limit exceeded", "error fetching")):
        raise RuntimeError(f"Chart service returned an error card: {theme}/{card}")
    # Clarify the upstream card's mixed time windows without changing any data.
    if card == "profile-details":
        data = data.replace(b" Contributions on GitHub", b" lifetime contributions")
        data = data.replace(b" Public Repos", b" public original repos")
    return ROOT / "assets" / theme / name, data


def main():
    items = [(theme, card, name) for theme in ("github", "github_dark") for card, name in CARDS]
    with ThreadPoolExecutor(max_workers=3) as pool:
        completed = list(pool.map(fetch_card, items))
    # Never replace a complete snapshot with only some of the requested charts.
    for path, data in completed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print("Refreshed all ten public charts without a personal access token")


if __name__ == "__main__":
    main()
