#!/usr/bin/env python3
"""Check Conventional Commit subjects and the pull-request title.

Project convention: a lowercase type, mandatory one-word lowercase scope,
optional breaking-change marker, colon, space and a nonempty description.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


PATTERN = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)\([a-z][a-z0-9]*\)!?: [^\s].*$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def validate(subject, label):
    if not PATTERN.fullmatch(subject):
        raise ValueError(f"{label}: use type(scope): description; example: fix(audio): correct playback volume")


def check(base, head, title=None):
    if not SHA.fullmatch(base) or not SHA.fullmatch(head):
        raise ValueError("Expected full commit SHAs, not user-provided branch expressions")
    if title is not None:
        validate(title, "Pull request title")
    result = subprocess.run(["git", "log", "--format=%H%x00%s", base + ".." + head], check=True, capture_output=True, text=True)
    lines = result.stdout.splitlines()
    if not lines:
        raise ValueError("No commits to validate")
    for line in lines:
        commit, subject = line.split("\0", 1)
        validate(subject, "Commit " + commit[:12])
    print(f"Conventional Commits: {len(lines)} commit(s) and {'PR title' if title is not None else 'commit subjects'} passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path)
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--title")
    args = parser.parse_args()
    try:
        if args.event:
            event = json.loads(args.event.read_text())
            pr = event["pull_request"]
            check(pr["base"]["sha"], pr["head"]["sha"], pr["title"])
        else:
            check(args.base or "", args.head or "", args.title)
    except (ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
