#!/usr/bin/env python3
"""Check publication boundaries and the repository's CI safety conventions."""

import re
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRS = {".runtime", ".venv", "node_modules", "data", "outputs", "target", "dist"}
FORBIDDEN_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".webm", ".aiff", ".aif", ".caf", ".safetensors", ".gguf", ".onnx", ".pth", ".pt", ".ckpt", ".bin", ".npz", ".db", ".sqlite", ".sqlite3", ".log", ".pem", ".key", ".p12", ".pfx"}
SECRET = re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")


def check():
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().strip("\0").split("\0")
    for name in names:
        path = Path(name)
        assert not FORBIDDEN_DIRS.intersection(path.parts), f"Private/generated path is tracked: {name}"
        assert path.suffix.lower() not in FORBIDDEN_SUFFIXES, f"Private/binary artifact is tracked: {name}"
        assert path.name == ".env.example" or not (path.name == ".env" or path.name.startswith(".env.")), name
        target = ROOT / path
        assert target.is_file() and not target.is_symlink(), name
        assert target.stat().st_size <= 5_000_000, f"Unexpected large source file: {name}"
        if target.suffix not in {".png", ".jpg", ".whl", ".gz"}:
            assert not SECRET.search(target.read_bytes()), f"Possible credential in {name}"

    workflows = list((ROOT / ".github/workflows").glob("*.yml"))
    assert workflows, "No workflows found"
    for path in workflows:
        document = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        assert document.get("permissions") == {"contents": "read"}, f"Default token permissions: {path}"
        assert not {"pull_request_target", "workflow_run"}.intersection(document["on"]), path
        for name, job in document["jobs"].items():
            assert job.get("runs-on") == "ubuntu-24.04", f"Only standard Ubuntu runners are allowed: {name}"
            assert 1 <= int(job["timeout-minutes"]) <= 20, name
            for step in job.get("steps", []):
                action = step.get("uses", "")
                if action:
                    assert re.fullmatch(r"(?:actions/[a-z0-9-]+|github/codeql-action/[a-z0-9-]+)@[0-9a-f]{40}", action), f"Unpinned or unapproved action: {action}"
                command = step.get("run", "")
                assert "${{ github.event." not in command, "Read untrusted PR data through an event file"
                assert "--repo-secrets" not in command
                if action.startswith("actions/upload-pages-artifact@"):
                    assert step.get("with", {}).get("path") == ".runtime/site"
                    assert step["with"]["retention-days"] == "1"
    print(f"Repository policy: {len(names)} tracked files and {len(workflows)} workflows passed")


if __name__ == "__main__":
    check()
