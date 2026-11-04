"""A PR may preserve legacy base history, but not add malformed commit subjects."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check-commits.py"
spec = importlib.util.spec_from_file_location("commit_convention", SCRIPT)
convention = importlib.util.module_from_spec(spec)
spec.loader.exec_module(convention)


class CommitConventionTests(unittest.TestCase):
    def test_event_checks_new_commits_without_rejecting_legacy_base(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = dict(os.environ, GIT_AUTHOR_NAME="Test", GIT_COMMITTER_NAME="Test", GIT_AUTHOR_EMAIL="ci@example.invalid", GIT_COMMITTER_EMAIL="ci@example.invalid")

            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, env=env, stderr=subprocess.DEVNULL).decode().strip()

            git("init", "-b", "main")
            git("commit", "--allow-empty", "-m", "Historical initial import")
            base = git("rev-parse", "HEAD")
            git("commit", "--allow-empty", "-m", "fix(audio): preserve the selected take")
            head = git("rev-parse", "HEAD")
            event = root / "event.json"
            event.write_text(json.dumps({"pull_request": {"title": "fix(audio): preserve the selected take", "base": {"sha": base}, "head": {"sha": head}}}))
            result = subprocess.run(["python3", str(SCRIPT), "--event", str(event)], cwd=root, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            git("commit", "--allow-empty", "-m", "misc changes")
            event.write_text(json.dumps({"pull_request": {"title": "fix(audio): preserve the selected take", "base": {"sha": base}, "head": {"sha": git("rev-parse", "HEAD")}}}))
            result = subprocess.run(["python3", str(SCRIPT), "--event", str(event)], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)

    def test_title_cannot_hide_a_second_line_or_omit_scope(self):
        for title in ["fix: correct playback", "fix(audio): correct playback\n::warning::hidden", "fix(audio): ", "Fix(audio): correct playback", "feat(two words): add preview"]:
            with self.subTest(title=title), self.assertRaises(ValueError):
                convention.validate(title, "title")
        convention.validate("feat(api)!: change export format", "title")

    def test_revision_arguments_cannot_be_git_options_or_expressions(self):
        with self.assertRaises(ValueError):
            convention.check("--all", "HEAD", "chore(repo): inspect history")


if __name__ == "__main__":
    unittest.main()
