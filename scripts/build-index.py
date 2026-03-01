#!/usr/bin/env python3
"""Build data/index.json from all research documents.

Run this before committing new research files so the index stays current.
The index is used for ChromaDB ingestion and API-ready search.

Usage:
    python scripts/build-index.py [docs_dir] [output_path]
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


def parse_frontmatter(content: str) -> dict | None:
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    try:
        return yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return None


def doc_id(path: Path, docs_dir: Path) -> str:
    return str(path.relative_to(docs_dir).with_suffix(""))


def main() -> int:
    docs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/index.json")

    if not docs_dir.exists():
        print(f"Error: docs directory not found: {docs_dir}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    documents = []
    skipped = 0

    for md_file in sorted(docs_dir.rglob("*.md")):
        if md_file.name in {"index.md", "tags.md"}:
            continue

        content = md_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)

        if not fm:
            skipped += 1
            print(f"  skip (no frontmatter): {md_file.relative_to(docs_dir)}")
            continue

        doc = {
            "id": doc_id(md_file, docs_dir),
            "title": fm.get("title", ""),
            "date": str(fm.get("date", "")),
            "category": fm.get("category", ""),
            "tags": fm.get("tags", []),
            "status": fm.get("status", "draft"),
            "author": fm.get("author", "linda"),
            "path": str(md_file),
            "embeddings_ready": fm.get("embeddings_ready", False),
        }

        if "sources" in fm:
            doc["sources"] = fm["sources"]
        if "related" in fm:
            doc["related"] = fm["related"]

        documents.append(doc)

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(documents),
        "skipped": skipped,
        "documents": documents,
    }

    output_path.write_text(
        json.dumps(index, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print(f"Built: {len(documents)} documents → {output_path}  ({skipped} skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
