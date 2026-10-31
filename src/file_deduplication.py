
"""SHA-256 file-level duplicate detection.

This module provides the canonical ``calculate_file_hash`` function
(imported from ``src.utils``) and a lightweight helper for checking
whether a file has been seen before, backed by the ``file_hash``
column that ``pdf_ingestion.py`` stores in
``output/pdf_extracted_metadata.csv``.

The earlier standalone JSON-database approach has been removed to
avoid having two disconnected deduplication systems.  The CSV is now
the single source of truth for file hashes.
"""

from pathlib import Path

import pandas as pd

from src.utils import calculate_file_hash   # single shared implementation

EXTRACTED_METADATA = Path("output/pdf_extracted_metadata.csv")


def find_file_duplicates(metadata_csv: Path = EXTRACTED_METADATA) -> pd.DataFrame:
    """Identify rows in the extracted-metadata CSV that share the same
    SHA-256 hash, indicating identical PDF files.

    Returns a DataFrame of duplicate rows with an added
    ``duplicate_of_file`` column showing the first occurrence's
    filename.
    """
    if not metadata_csv.exists():
        raise FileNotFoundError(
            f"Metadata CSV not found: {metadata_csv}\n"
            "Run 'python src/pdf_ingestion.py' first."
        )

    df = pd.read_csv(metadata_csv).fillna("")

    if "file_hash" not in df.columns:
        raise ValueError("file_hash column missing from metadata CSV.")

    # First occurrence of each hash is the "primary" file.
    first_seen = (
        df.drop_duplicates(subset=["file_hash"], keep="first")
        .set_index("file_hash")["filename"]
    )

    duplicates = df[df.duplicated(subset=["file_hash"], keep="first")].copy()
    duplicates["duplicate_of_file"] = duplicates["file_hash"].map(first_seen)

    return duplicates


def report_file_duplicates(metadata_csv: Path = EXTRACTED_METADATA) -> None:
    """Print a summary of exact file-level duplicates."""
    duplicates = find_file_duplicates(metadata_csv)

    if duplicates.empty:
        print("No exact file-level duplicates found.")
        return

    print(f"File-level duplicates detected: {len(duplicates)}")
    print()
    for _, row in duplicates.iterrows():
        print(f"  Duplicate : {row['filename']}")
        print(f"  Original  : {row['duplicate_of_file']}")
        print(f"  SHA-256   : {row['file_hash']}")
        print()


if __name__ == "__main__":
    report_file_duplicates()
