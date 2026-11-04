"""Reject partial chart generation before publishing a new profile snapshot."""

from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "0-profile-details.svg",
    "1-repos-per-language.svg",
    "2-most-commit-language.svg",
    "3-stats.svg",
    "4-productive-time.svg",
)

for theme in ("github", "github_dark"):
    for name in FILES:
        path = ROOT / "assets" / theme / name
        document = ElementTree.parse(path)
        if document.getroot().tag != "{http://www.w3.org/2000/svg}svg":
            raise SystemExit(f"Invalid chart: {path}")
        content = " ".join(document.getroot().itertext()).lower()
        if "something went wrong" in content or "api rate limit exceeded" in content:
            raise SystemExit(f"Chart contains an API error: {path}")

print("Verified all ten charts across light and dark themes")
