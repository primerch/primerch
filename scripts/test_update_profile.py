import unittest

from update_profile import public_external, render, text


def pr(state="MERGED", private=False, owner="upstream", title="Example fix"):
    return {
        "number": 1,
        "title": title,
        "url": f"https://github.com/{owner}/library/pull/1",
        "state": state,
        "mergedAt": "2026-11-03T23:59:10Z" if state == "MERGED" else None,
        "updatedAt": "2026-11-04T02:33:02Z",
        "additions": 10,
        "deletions": 2,
        "repository": {"nameWithOwner": f"{owner}/library", "isPrivate": private, "owner": {"login": owner}},
    }


class ProfileTests(unittest.TestCase):
    def test_private_and_owned_repositories_never_appear(self):
        values = [pr(), pr(private=True, owner="secret"), pr(owner="PRIMERCH")]
        self.assertEqual(len(public_external(values)), 1)
        output = render(values)
        self.assertNotIn("secret", output)
        self.assertNotIn("PRIMERCH", output)
        self.assertIn("1 个 PR 已合并到 1 个项目", output)

    def test_closed_is_not_counted_as_merged(self):
        output = render([pr(), pr("CLOSED"), pr("OPEN")])
        self.assertIn("1 个 PR 已合并到 1 个项目", output)
        self.assertIn("1 个正在等待合并", output)
        self.assertIn("+10 / −2 行", output)
        self.assertIn("2026-11-04", output)  # Shanghai date crosses midnight.

    def test_titles_cannot_break_table_or_add_html(self):
        self.assertEqual(text("a|b\n<script>[x]"), "a\\|b &lt;script&gt;\\[x\\]")

    def test_empty_profile_remains_readable(self):
        self.assertIn("0 个 PR 已合并到 0 个项目", render([]))


if __name__ == "__main__":
    unittest.main()
