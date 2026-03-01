#!/usr/bin/env python3
"""Validate YAML frontmatter in all research documents.

Usage:
    python scripts/validate-frontmatter.py [docs_dir]

Exits non-zero if any file fails validation. Skips index.md files.
"""

import sys
from pathlib import Path
import yaml

REQUIRED_FIELDS = {"title", "date", "category", "status"}
VALID_CATEGORIES = {
    "llm-infra", "sre", "agents", "benchmarks",
    "security", "publishing", "weekly-digest",
}
VALID_STATUSES = {"draft", "reviewed", "published"}


def parse_frontmatter(content: str) -> dict | None:
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    try:
        return yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parse error: {e}") from e


def validate_file(path: Path) -> list[str]:
    errors = []
    content = path.read_text(encoding="utf-8")

    try:
        fm = parse_frontmatter(content)
    except ValueError as e:
        return [str(e)]

    if fm is None:
        return ["Missing frontmatter block (expected --- ... ---)"]

    missing = REQUIRED_FIELDS - set(fm.keys())
    if missing:
        errors.append(f"Missing required fields: {', '.join(sorted(missing))}")

    if "status" in fm and fm["status"] not in VALID_STATUSES:
        errors.append(
            f"Invalid status '{fm['status']}' — must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )

    if "category" in fm and fm["category"] not in VALID_CATEGORIES:
        errors.append(
            f"Invalid category '{fm['category']}' — must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
        )

    return errors


def main() -> int:
    docs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs")

    if not docs_dir.exists():
        print(f"Error: docs directory not found: {docs_dir}", file=sys.stderr)
        return 1

    failed = 0
    checked = 0

    for md_file in sorted(docs_dir.rglob("*.md")):
        if md_file.name in {"index.md", "tags.md"}:
            continue

        checked += 1
        try:
            errors = validate_file(md_file)
        except Exception as e:
            errors = [f"Unexpected error: {e}"]

        rel = md_file.relative_to(docs_dir.parent)
        if errors:
            failed += 1
            print(f"❌ {rel}")
            for err in errors:
                print(f"   → {err}")
        else:
            print(f"✅ {rel}")

    print(f"\n{checked} file(s) checked — {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
