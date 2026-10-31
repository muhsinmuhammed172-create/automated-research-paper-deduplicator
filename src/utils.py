
"""Shared utilities used by multiple modules."""

import hashlib
import re
import unicodedata
from pathlib import Path


# ---------------------------------------------------------------------------
# File hashing
# ---------------------------------------------------------------------------

def calculate_file_hash(file_path: str | Path) -> str:
    """Return the SHA-256 hex digest of a file.

    Reads the file in 1 MB chunks so that large PDFs do not consume
    excessive memory.
    """
    sha256 = hashlib.sha256()

    with Path(file_path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


# ---------------------------------------------------------------------------
# DOI normalisation
# ---------------------------------------------------------------------------

_DOI_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
    "doi:",
)

_DOI_TRAILING = ".,;:)]}>"


def normalize_doi(value: str) -> str:
    """Clean and normalise a raw DOI string.

    Steps applied:
    1. Strip surrounding whitespace.
    2. Remove common URL prefixes (https://doi.org/, doi:, …).
    3. Apply Unicode NFKC normalisation to convert typographic
       ligatures (ﬁ, ﬂ, ﬃ, …) to their ASCII equivalents.  This
       prevents Crossref HTTP 404s caused by ligature characters that
       some PDF producers embed in DOI text.
    4. Remove trailing punctuation that PDF extraction commonly appends.
    """
    doi = str(value or "").strip()

    lower = doi.lower()
    for prefix in _DOI_PREFIXES:
        if lower.startswith(prefix):
            doi = doi[len(prefix):].strip()
            break

    # Convert ligatures and other compatibility characters to ASCII.
    doi = unicodedata.normalize("NFKC", doi)

    return doi.rstrip(_DOI_TRAILING)


# ---------------------------------------------------------------------------
# Publication-year extraction from Crossref date structures
# ---------------------------------------------------------------------------

def get_publication_year(message: dict) -> str:
    """Return the earliest available publication year from a Crossref
    ``message`` dict, trying fields in priority order."""
    for field in (
        "published-print",
        "published-online",
        "published",
        "issued",
        "created",
    ):
        date_info = message.get(field) or {}
        date_parts = date_info.get("date-parts", [])

        if date_parts and date_parts[0]:
            return str(date_parts[0][0])

    return ""
