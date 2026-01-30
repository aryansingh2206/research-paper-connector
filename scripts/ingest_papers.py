#!/usr/bin/env python3
"""
Command-line script for ingesting research papers.
Supports PDF and TXT documents.
"""

import sys
import argparse
import logging
from pathlib import Path

# ------------------------------------------------------------------
# Canonical project root (Docker-safe)
# ------------------------------------------------------------------
PROJECT_ROOT = Path("/app")
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion import IngestionPipeline

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def resolve_path(path_str: str) -> Path:
    """
    Resolve user-provided paths relative to /app inside Docker.
    """
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def collect_files(directory: Path) -> list[Path]:
    """
    Collect all .pdf and .txt files from a directory.
    Explicit iteration avoids glob / OS issues.
    """
    files: list[Path] = []

    for item in directory.iterdir():
        if item.is_file() and item.suffix.lower() in {".pdf", ".txt"}:
            files.append(item)

    return sorted(files)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Ingest research papers into Endee"
    )

    parser.add_argument(
        "paths",
        nargs="+",
        help="Path(s) to paper files or directories (relative to project root)"
    )

    parser.add_argument("--title", help="Default title")
    parser.add_argument("--authors", help="Default authors")
    parser.add_argument("--year", type=int, help="Publication year")

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset collection before ingestion"
    )

    args = parser.parse_args()

    logger.info("Initializing ingestion pipeline...")
    pipeline = IngestionPipeline()

    if args.reset:
        logger.warning("Resetting collection (explicit delete requested)")
        pipeline.endee_client.delete_collection()
        pipeline._initialize_collection()

    base_metadata = {}
    if args.title:
        base_metadata["title"] = args.title
    if args.authors:
        base_metadata["authors"] = args.authors
    if args.year:
        base_metadata["year"] = args.year

    all_results: dict[str, bool] = {}

    for raw_path in args.paths:
        path = resolve_path(raw_path)
        logger.info(f"Resolved input path to: {path}")

        if not path.exists():
            logger.error(f"Path not found: {path}")
            continue

        if path.is_file():
            logger.info(f"Ingesting file: {path}")
            all_results[str(path)] = pipeline.ingest_single_paper(
                file_path=str(path),
                metadata=base_metadata.copy()
            )

        elif path.is_dir():
            logger.info(f"Ingesting directory: {path}")
            files = collect_files(path)
            logger.info(f"Found {len(files)} files for ingestion")

            for file_path in files:
                logger.info(f"Processing: {file_path.name}")
                all_results[str(file_path)] = pipeline.ingest_single_paper(
                    file_path=str(file_path),
                    metadata=base_metadata.copy()
                )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("INGESTION SUMMARY")
    print("=" * 80)

    successful = sum(all_results.values())
    failed = len(all_results) - successful

    print(f"\nTotal files: {len(all_results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed:
        print("\nFailed files:")
        for path, ok in all_results.items():
            if not ok:
                print(f"  ❌ {path}")

    print("\n" + "=" * 80)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
