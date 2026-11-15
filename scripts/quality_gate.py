#!/usr/bin/env python3
"""Dependency-free repository hygiene checks. Run as part of CI and locally."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_FILE_BYTES = 15 * 1024 * 1024
REQUIRED_POLICY_FILES = (
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".github/pull_request_template.md",
    ".github/dependabot.yml",
    "docs/ENGINEERING_POLICY.md",
    "docs/adr/README.md",
)
FORBIDDEN_DIRECTORIES = {"node_modules", "dist", "release", ".collection", "__pycache__", ".pytest_cache"}
FORBIDDEN_SUFFIXES = {".pem", ".p12", ".pfx"}
SCANNED_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".yaml", ".yml", ".md", ".html", ".css", ".sh", ".txt", ".toml"}
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")
GITHUB_TOKEN = re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,})")
AWS_KEY = re.compile(r"AKIA[0-9A-Z]{16}")
MERGE_CONFLICT = re.compile(r"^(?:<<<<<<< |>>>>>>> |=======$)", re.MULTILINE)


def disallowed_path(relative: Path) -> str | None:
    parts = set(relative.parts)
    if parts & FORBIDDEN_DIRECTORIES:
        return "generated output/cache must not be committed"
    if relative.name == ".env" or (relative.name.startswith(".env.") and relative.name != ".env.example"):
        return "environment credentials must not be committed"
    if relative.suffix.lower() in FORBIDDEN_SUFFIXES or relative.name.endswith(".private.key"):
        return "credential/key files must not be committed"
    return None


def scan_text(value: str) -> list[str]:
    errors = []
    for rule, label in (
        (PRIVATE_KEY, "private key material"),
        (GITHUB_TOKEN, "GitHub credential token"),
        (AWS_KEY, "AWS access key"),
        (MERGE_CONFLICT, "unresolved merge conflict"),
    ):
        if rule.search(value):
            errors.append(label)
    return errors


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT, capture_output=True, check=True,
    )
    return [Path(os.fsdecode(name)) for name in result.stdout.split(b"\0") if name]


def main() -> int:
    errors = []
    for required in REQUIRED_POLICY_FILES:
        if not (ROOT / required).is_file():
            errors.append(f"{required}: required engineering policy missing")
    try:
        paths = tracked_files()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Cannot enumerate tracked files: {exc}", file=sys.stderr)
        return 1
    for rel in paths:
        issue = disallowed_path(rel)
        if issue:
            errors.append(f"{rel}: {issue}")
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        if path.stat().st_size > MAX_TRACKED_FILE_BYTES:
            errors.append(f"{rel}: large tracked file; use evidence archive storage")
            continue
        if path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{rel}: binary data disguised as text")
            continue
        for issue in scan_text(content):
            errors.append(f"{rel}: {issue}")
        if path.suffix.lower() == ".py":
            try:
                compile(content, str(rel), "exec")
            except SyntaxError as exc:
                errors.append(f"{rel}: Python syntax invalid at line {exc.lineno}")
    if errors:
        for issue in errors:
            print("ERROR:", issue, file=sys.stderr)
        return 1
    print(f"Repository hygiene OK: {len(paths)} tracked files.")
    if not (ROOT / "package-lock.json").is_file():
        print("WARNING: no package-lock.json; npm builds are not reproducible (DEBT-001).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
