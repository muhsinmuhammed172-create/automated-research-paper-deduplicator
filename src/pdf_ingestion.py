
import re
from pathlib import Path

import fitz
import pandas as pd

from src.utils import calculate_file_hash


PDF_DIR = Path("data/pdfs")
OUTPUT_FILE = Path("output/pdf_extracted_metadata.csv")


DOI_PATTERN = re.compile(
    r"\b10\.\d{4,9}/[^\s<>\"{}|\\^`\[\]]+",
    re.IGNORECASE,
)

YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")

# Keywords that often appear near a publication year on the first page.
PUBLICATION_YEAR_MARKERS = re.compile(
    r"(?:published|received|accepted|volume|vol\.|issue|©|\(c\))\D{0,20}((?:19|20)\d{2})\b",
    re.IGNORECASE,
)


def _clean_doi_match(match: re.Match) -> str:
    """Remove punctuation commonly attached to DOI text."""
    return match.group(0).rstrip(".,;:)]}\"")


def extract_pdf_text(pdf_path: Path) -> tuple[dict, str]:
    """Extract text from the first three pages of a PDF."""
    with fitz.open(pdf_path) as document:
        metadata = document.metadata or {}
        text = "\n".join(
            page.get_text("text") for page in document[:3]
        )
    return metadata, text


def extract_doi(text: str) -> str:
    """Extract a DOI from extracted page text."""
    match = DOI_PATTERN.search(text)
    return _clean_doi_match(match) if match else ""


def extract_title(text: str, pdf_metadata: dict) -> str:
    """Use PDF properties first, then cautiously inspect page text."""
    title = (pdf_metadata.get("title") or "").strip()

    if title and title.lower() not in {
        "untitled", "unknown", "microsoft word"
    }:
        return title

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
    ]
    lines = [line for line in lines if line and len(line) > 8]

    # Heuristic: title often appears near the beginning of page 1.
    # Skip obvious metadata labels and DOI-only lines.
    for line in lines[:25]:
        lower = line.lower()

        if DOI_PATTERN.search(line):
            continue

        if lower.startswith((
            "abstract", "keywords", "doi:", "https://doi.org",
            "received:", "accepted:", "published:",
        )):
            continue

        if len(line) > 180:
            continue

        if len(line.split()) >= 3:
            return line

    return ""


def extract_authors(text: str, pdf_metadata: dict) -> str:
    """Use PDF properties or a cautious first-page heuristic."""
    author = (pdf_metadata.get("author") or "").strip()

    if author and author.lower() not in {"unknown", "anonymous"}:
        return author

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
    ]
    lines = [line for line in lines if line]

    # Inspect lines shortly after the possible title.
    for line in lines[1:15]:
        lower = line.lower()

        if DOI_PATTERN.search(line):
            continue

        if lower.startswith((
            "abstract", "keywords", "introduction",
            "received:", "accepted:", "published:",
        )):
            break

        # Avoid returning a long abstract paragraph as an author list.
        if len(line) > 120 or len(line.split()) > 15:
            continue

        if re.search(r"\b(university|department|faculty|institute)\b", lower):
            continue

        # Names are often separated by commas, semicolons or "and".
        if re.search(r"[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+", line):
            return line

    return ""


def extract_year(text: str, pdf_metadata: dict) -> str:
    """Extract a plausible publication year.

    Priority order:
    1. A year adjacent to a known publication marker in the page text
       (e.g. "Published 2023", "Vol. 14, 2022").
    2. A year found anywhere in the page text.
    3. A year found in the PDF creation/modification date metadata.
    """
    # Priority 1: year near a publication marker.
    marker_match = PUBLICATION_YEAR_MARKERS.search(text)
    if marker_match:
        return marker_match.group(1)

    # Priority 2: first year found anywhere in the page text.
    text_match = YEAR_PATTERN.search(text)
    if text_match:
        return text_match.group(0)

    # Priority 3: PDF metadata dates as a last resort.
    for key in ("creationDate", "modDate"):
        value = str(pdf_metadata.get(key) or "")
        meta_match = YEAR_PATTERN.search(value)
        if meta_match:
            return meta_match.group(0)

    return ""


def extract_pdf_metadata(pdf_path: Path) -> dict:
    """Create one metadata record for a PDF."""
    file_hash = calculate_file_hash(pdf_path)

    try:
        pdf_metadata, text = extract_pdf_text(pdf_path)

        return {
            "filename": pdf_path.name,
            "file_path": str(pdf_path),
            "source": pdf_path.parent.name,
            "file_hash": file_hash,
            "title": extract_title(text, pdf_metadata),
            "author": extract_authors(text, pdf_metadata),
            "doi": extract_doi(text),
            "year": extract_year(text, pdf_metadata),
            "extraction_status": "Success",
        }

    except Exception as error:
        return {
            "filename": pdf_path.name,
            "file_path": str(pdf_path),
            "source": pdf_path.parent.name,
            "file_hash": file_hash,
            "title": "",
            "author": "",
            "doi": "",
            "year": "",
            "extraction_status": f"Error: {error}",
        }


def ingest_pdfs(pdf_dir: Path = PDF_DIR, output_file: Path = OUTPUT_FILE) -> pd.DataFrame:
    pdf_dir = Path(pdf_dir)
    output_file = Path(output_file)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(
        path for path in pdf_dir.rglob("*")
        if path.is_file() and path.suffix.lower() == ".pdf"
    )

    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        print("Add some PDFs and run this script again.")
        return pd.DataFrame()

    new_data = pd.DataFrame(
        [extract_pdf_metadata(path) for path in pdf_files]
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Keep one record per file path.
    # Identical files with different names must remain separate
    # so the deduplication module can detect them.
    if output_file.exists():
        old_data = pd.read_csv(output_file).fillna("")
        combined = pd.concat(
            [old_data, new_data], ignore_index=True
        )
        combined = combined.drop_duplicates(
            subset=["file_path"], keep="last"
        )
    else:
        combined = new_data

    combined.to_csv(output_file, index=False)

    print(f"PDFs processed this run: {len(pdf_files)}")
    print(f"Unique PDF files recorded: {len(combined)}")
    print(f"DOIs found this run: {(new_data['doi'] != '').sum()}")
    print(f"Titles extracted: {(new_data['title'] != '').sum()}")
    print(f"Authors extracted: {(new_data['author'] != '').sum()}")
    print(f"Years extracted: {(new_data['year'] != '').sum()}")
    print(f"Saved metadata to: {output_file}")
    return combined


if __name__ == "__main__":
    ingest_pdfs()
