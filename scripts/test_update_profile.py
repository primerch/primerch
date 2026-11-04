import unittest

from update_profile import public_external, render, render_history, text


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
        self.assertIn("1 pull request merged across 1 project", output)

    def test_closed_is_not_counted_as_merged(self):
        output = render([pr(), pr("CLOSED"), pr("OPEN")])
        self.assertIn("1 pull request merged across 1 project", output)
        self.assertIn("1 open", output)
        self.assertIn("+10 / −2 lines", output)
        self.assertIn("2026-11-04", output)  # Shanghai date crosses midnight.

    def test_titles_cannot_break_table_or_add_html(self):
        self.assertEqual(text("a|b\n<script>[x]"), "a\\|b &lt;script&gt;\\[x\\]")

    def test_empty_profile_remains_readable(self):
        self.assertIn("0 pull requests merged across 0 projects", render([]))

    def test_new_merge_moves_from_open_to_full_history(self):
        before = render_history([pr("OPEN")])
        after = render_history([pr("MERGED")])
        merged_before, open_before = before.split("## Open pull requests")
        merged_after, open_after = after.split("## Open pull requests")
        url = "https://github.com/upstream/library/pull/1"
        self.assertNotIn(url, merged_before)
        self.assertIn(url, open_before)
        self.assertIn(url, merged_after)
        self.assertNotIn(url, open_after)

    def test_full_history_does_not_drop_old_merges(self):
        values = [dict(pr(), number=i, url=f"https://github.com/upstream/library/pull/{i}") for i in range(25)]
        self.assertEqual(render_history(values).count("| 2026-11-04 |"), 25)


if __name__ == "__main__":
    unittest.main()
