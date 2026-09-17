"""Unit tests for the pure decision logic of ownership.py — run from .github/scripts."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ownership import decide, groups_for, latest_approvals  # noqa: E402

ADMINS = {"alice", "bob"}
OWNERS = {"search": {"leo"}, "gtm": {"alice"}}


def review(login, state):
    return {"user": {"login": login}, "state": state}


class LatestApprovalsTests(unittest.TestCase):
    def test_comment_does_not_count_and_dismissal_revokes(self):
        reviews = [
            review("leo", "COMMENTED"),
            review("bob", "APPROVED"),
            review("bob", "DISMISSED"),
            review("alice", "APPROVED"),
            review("alice", "COMMENTED"),
        ]
        self.assertEqual(latest_approvals(reviews), {"alice"})

    def test_changes_requested_after_approval_revokes(self):
        self.assertEqual(
            latest_approvals([review("leo", "APPROVED"), review("leo", "CHANGES_REQUESTED")]),
            set(),
        )


class DecideTests(unittest.TestCase):
    def test_owner_edits_own_plugin_without_review(self):
        ok, _ = decide(["plugins/search/dify/main.py"], "leo", set(), ADMINS, OWNERS)
        self.assertTrue(ok)

    def test_non_owner_needs_owner_approval(self):
        files = ["plugins/search/README.md"]
        ok, lines = decide(files, "alice", set(), ADMINS, OWNERS)
        self.assertFalse(ok)
        self.assertIn("@leo", lines[0])
        ok, _ = decide(files, "alice", {"leo"}, ADMINS, OWNERS)
        self.assertTrue(ok)

    def test_admin_approval_does_not_substitute_for_owner(self):
        ok, _ = decide(["plugins/search/x.py"], "carol", {"bob"}, ADMINS, OWNERS)
        self.assertFalse(ok)

    def test_admin_edits_outside_plugins_without_review(self):
        ok, _ = decide(["README.md", ".github/workflows/ci.yml"], "alice", set(), ADMINS, OWNERS)
        self.assertTrue(ok)

    def test_non_admin_outside_plugins_needs_admin(self):
        ok, _ = decide(["README.md"], "leo", set(), ADMINS, OWNERS)
        self.assertFalse(ok)
        ok, _ = decide(["README.md"], "leo", {"bob"}, ADMINS, OWNERS)
        self.assertTrue(ok)

    def test_admin_group_message_never_lists_nobody(self):
        ok, lines = decide(["README.md"], "carol", set(), set(), OWNERS)
        self.assertFalse(ok)
        self.assertIn("a repository admin", lines[0])
        self.assertNotIn("nobody", lines[0])

    def test_new_plugin_needs_admin(self):
        files = ["plugins/news/plugin.aisa.yaml", "plugins/news/README.md"]
        ok, lines = decide(files, "leo", set(), ADMINS, OWNERS)
        self.assertFalse(ok)
        self.assertIn("new plugin news", lines[0])
        ok, _ = decide(files, "leo", {"alice"}, ADMINS, OWNERS)
        self.assertTrue(ok)

    def test_mixed_pr_requires_every_group(self):
        files = ["plugins/gtm/dify/main.py", "plugins/search/dify/main.py", "README.md"]
        # alice owns gtm and is an admin, but search belongs to leo
        ok, lines = decide(files, "alice", set(), ADMINS, OWNERS)
        self.assertFalse(ok)
        self.assertEqual(sum(line.startswith("NEED") for line in lines), 1)
        ok, _ = decide(files, "alice", {"leo"}, ADMINS, OWNERS)
        self.assertTrue(ok)

    def test_groups_are_keyed_by_plugin(self):
        groups = groups_for(["plugins/gtm/a", "plugins/gtm/b", "x"], OWNERS, ADMINS)
        self.assertEqual(len(groups), 2)


if __name__ == "__main__":
    unittest.main()
