#!/usr/bin/env python3
"""Bump version for your-docs-mcp or your-docs-server.

Usage:
    python scripts/bump_version.py --package mcp --bump patch
    python scripts/bump_version.py --package server --version 1.2.3
    python scripts/bump_version.py --package mcp --bump minor --dry-run

Prints the new version to stdout (last line). All diagnostics go to stderr.
Stdlib-only — no external dependencies.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FILES = {
    "mcp": {
        "pyproject": REPO_ROOT / "pyproject.toml",
        "init": REPO_ROOT / "docs_mcp" / "__init__.py",
    },
    "server": {
        "pyproject": REPO_ROOT / "packages" / "your-docs-server" / "pyproject.toml",
    },
}

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def read_version_from_pyproject(path: Path) -> str:
    """Read version from [project] section of a pyproject.toml."""
    in_project = False
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_project = stripped == "[project]"
        if in_project:
            m = re.match(r'version\s*=\s*"([^"]+)"', stripped)
            if m:
                return m.group(1)
    log(f"ERROR: Could not find version in {path}")
    sys.exit(1)


def read_version_from_init(path: Path) -> str:
    """Read __version__ from a Python file."""
    content = path.read_text()
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not m:
        log(f"ERROR: Could not find __version__ in {path}")
        sys.exit(1)
    return m.group(1)


def write_version_to_pyproject(path: Path, old: str, new: str) -> None:
    """Replace version in [project] section of pyproject.toml."""
    in_project = False
    replaced = False
    lines = []
    for line in path.read_text().splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("["):
            in_project = stripped == "[project]"
        if in_project and not replaced:
            if re.match(r'version\s*=\s*"' + re.escape(old) + '"', stripped):
                line = line.replace(f'"{old}"', f'"{new}"')
                replaced = True
        lines.append(line)
    if not replaced:
        log(f"ERROR: Failed to replace version {old} -> {new} in {path}")
        sys.exit(1)
    path.write_text("".join(lines))
    log(f"  Updated {path.relative_to(REPO_ROOT)}: {old} -> {new}")


def write_version_to_init(path: Path, old: str, new: str) -> None:
    """Replace __version__ in a Python file."""
    content = path.read_text()
    new_content = content.replace(f'__version__ = "{old}"', f'__version__ = "{new}"')
    if new_content == content:
        log(f"ERROR: Failed to replace __version__ in {path}")
        sys.exit(1)
    path.write_text(new_content)
    log(f"  Updated {path.relative_to(REPO_ROOT)}: {old} -> {new}")


def compute_bump(current: str, bump_type: str) -> str:
    """Compute the next version given a bump type."""
    parts = current.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        log(f"ERROR: Current version '{current}' is not valid semver")
        sys.exit(1)
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "major":
        return f"{major + 1}.0.0"
    else:
        log(f"ERROR: Unknown bump type: {bump_type}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump package version")
    parser.add_argument(
        "--package",
        required=True,
        choices=["mcp", "server"],
        help="Package to bump: mcp (your-docs-mcp) or server (your-docs-server)",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        help="Bump type",
    )
    group.add_argument(
        "--version",
        help="Explicit version (X.Y.Z)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing files",
    )
    args = parser.parse_args()

    # Validate custom version format
    if args.version and not SEMVER_RE.match(args.version):
        log(f"ERROR: Invalid version format: {args.version} (expected X.Y.Z)")
        sys.exit(1)

    files = FILES[args.package]

    # Verify files exist
    for label, path in files.items():
        if not path.exists():
            log(f"ERROR: File not found: {path}")
            sys.exit(1)

    # Read current version
    current = read_version_from_pyproject(files["pyproject"])
    log(f"Current {args.package} version: {current}")

    # Cross-check __init__.py if mcp package
    if args.package == "mcp" and "init" in files:
        init_ver = read_version_from_init(files["init"])
        if init_ver != current:
            log(f"WARNING: __init__.py version ({init_ver}) differs from pyproject.toml ({current})")
            log("  Will update both to the new version.")

    # Compute new version
    if args.version:
        new_version = args.version
    else:
        new_version = compute_bump(current, args.bump)

    log(f"New version: {new_version}")

    if args.dry_run:
        log("Dry run — no files modified.")
        print(new_version)
        return

    # Write new version
    write_version_to_pyproject(files["pyproject"], current, new_version)

    if args.package == "mcp" and "init" in files:
        init_ver = read_version_from_init(files["init"])
        write_version_to_init(files["init"], init_ver, new_version)

    # Final output: new version on stdout for CI to capture
    print(new_version)


if __name__ == "__main__":
    main()
