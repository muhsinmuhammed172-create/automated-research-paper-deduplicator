
import time
from difflib import SequenceMatcher
from pathlib import Path
import re

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils import normalize_doi, get_publication_year


INPUT_FILE = Path("output/pdf_extracted_metadata.csv")
OUTPUT_FILE = Path("output/pdf_enriched_metadata.csv")
ISSUES_FILE = Path("output/pdf_metadata_enrichment_issues.csv")

CROSSREF_API = "https://api.crossref.org/works/"
CROSSREF_SEARCH_API = "https://api.crossref.org/works"
USER_AGENT = "MCA-PaperDeduplicator/1.0"

# Retry on transient server errors and rate-limit responses.
_SESSION = requests.Session()
_RETRY = Retry(
    total=3,
    backoff_factor=1.0,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
_SESSION.mount("https://", HTTPAdapter(max_retries=_RETRY))
_SESSION.mount("http://", HTTPAdapter(max_retries=_RETRY))


def normalize_title(value: str) -> str:
    """Normalize titles for comparison."""
    value = str(value or "").lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def compare_titles(pdf_title: str, crossref_title: str) -> float:
    """Compare the extracted PDF title with the Crossref title.

    Returns a similarity score between 0 and 1.

    The substring shortcut handles the common case where the PDF
    extractor captured only part of the actual title (as with P3).
    """
    pdf_norm = normalize_title(pdf_title)
    crossref_norm = normalize_title(crossref_title)

    if not pdf_norm or not crossref_norm:
        return 0.0

    if pdf_norm == crossref_norm:
        return 1.0

    # Partial title — one string is a substring of the other.
    if pdf_norm in crossref_norm or crossref_norm in pdf_norm:
        shorter = min(len(pdf_norm), len(crossref_norm))
        longer = max(len(pdf_norm), len(crossref_norm))
        return shorter / longer

    return SequenceMatcher(None, pdf_norm, crossref_norm).ratio()


def crossref_lookup(doi: str) -> tuple[dict | None, str]:
    """Retrieve bibliographic metadata from Crossref by DOI."""
    try:
        response = _SESSION.get(
            CROSSREF_API + requests.utils.quote(doi, safe="/"),
            timeout=20,
            headers={"User-Agent": USER_AGENT},
        )

        if response.status_code != 200:
            return None, f"Crossref HTTP {response.status_code}"

        message = response.json().get("message", {})
        return _parse_crossref_message(message), ""

    except (requests.RequestException, ValueError) as error:
        return None, str(error)


def crossref_title_search(title: str) -> tuple[dict | None, str]:
    """Search Crossref by title when no DOI is available.

    Returns the top result only if its title similarity to the query
    exceeds 0.90, to avoid false matches.
    """
    if not title or len(title.strip()) < 10:
        return None, "Title too short for reliable search"

    try:
        response = _SESSION.get(
            CROSSREF_SEARCH_API,
            params={
                "query.title": title,
                "rows": 1,
                "select": (
                    "DOI,title,author,published,published-print,"
                    "published-online,issued,created,"
                    "container-title,publisher,volume,issue,page,type"
                ),
            },
            timeout=20,
            headers={"User-Agent": USER_AGENT},
        )

        if response.status_code != 200:
            return None, f"Crossref search HTTP {response.status_code}"

        items = response.json().get("message", {}).get("items", [])
        if not items:
            return None, "No results returned by title search"

        message = items[0]
        titles = message.get("title") or []
        crossref_title = titles[0] if titles else ""

        similarity = compare_titles(title, crossref_title)
        if similarity < 0.90:
            return None, (
                f"Title search top result similarity too low "
                f"({similarity:.3f}) — skipped"
            )

        return _parse_crossref_message(message), ""

    except (requests.RequestException, ValueError) as error:
        return None, str(error)


def _parse_crossref_message(message: dict) -> dict:
    """Extract standardised bibliographic fields from a Crossref message."""
    titles = message.get("title") or []
    authors = []

    for author in message.get("author", []):
        name = " ".join(
            part for part in (
                author.get("given", ""),
                author.get("family", ""),
            ) if part
        ).strip()
        if name:
            authors.append(name)

    journals = message.get("container-title") or []
    year = get_publication_year(message)

    pub_date_raw = (
        message.get("published-print")
        or message.get("published-online")
        or message.get("published")
        or message.get("issued")
        or {}
    )

    return {
        "crossref_title": titles[0] if titles else "",
        "crossref_author": "; ".join(authors),
        "crossref_doi": message.get("DOI", ""),
        "crossref_year": year,
        "crossref_journal": journals[0] if journals else "",
        "crossref_publisher": message.get("publisher", ""),
        "crossref_volume": message.get("volume", ""),
        "crossref_issue": message.get("issue", ""),
        "crossref_page": message.get("page", ""),
        "crossref_publication_date": str(
            pub_date_raw.get("date-parts", "")
        ),
        "crossref_type": message.get("type", ""),
    }


def enrich_metadata(
    input_file: Path = INPUT_FILE,
    output_file: Path = OUTPUT_FILE,
    issues_file: Path = ISSUES_FILE
) -> pd.DataFrame:
    input_file = Path(input_file)
    output_file = Path(output_file)
    issues_file = Path(issues_file)

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}"
        )

    df = pd.read_csv(input_file).fillna("")

    enriched_rows = []
    issues = []

    for _, row in df.iterrows():
        record = row.to_dict()

        original_title = str(record.get("title", "")).strip()
        original_author = str(record.get("author", "")).strip()
        original_year = str(record.get("year", "")).strip()

        # Normalise the raw DOI (strips prefixes, fixes ligatures).
        doi = normalize_doi(record.get("doi", ""))

        # Preserve original PDF-extracted metadata.
        record["pdf_title"] = original_title
        record["pdf_author"] = original_author
        record["pdf_year"] = original_year

        # ── Try DOI-based lookup ─────────────────────────────────────────
        if doi:
            metadata, error = crossref_lookup(doi)
        else:
            metadata, error = None, "No DOI"

        # ── Fallback: title-based Crossref search ────────────────────────
        if not metadata and original_title:
            fallback_meta, fallback_error = crossref_title_search(original_title)
            if fallback_meta:
                metadata = fallback_meta
                enrichment_method = "Crossref title search"
                error = ""
            else:
                enrichment_method = "PDF extraction"
                if not doi:
                    error = f"No DOI; title search: {fallback_error}"
                else:
                    error = f"DOI lookup failed ({error}); title search: {fallback_error}"
        else:
            enrichment_method = "Crossref DOI lookup" if metadata else "PDF extraction"

        # ── No metadata retrieved ────────────────────────────────────────
        if not metadata:
            record["metadata_source"] = enrichment_method
            record["enrichment_status"] = (
                "No DOI" if not doi else "Lookup Failed"
            )
            record["metadata_validation"] = "Needs Review"
            record["title_match_score"] = ""

            issues.append({
                "filename": record.get("filename", ""),
                "doi": doi,
                "issue": error,
            })

            enriched_rows.append(record)
            time.sleep(0.1)
            continue

        # ── Metadata retrieved — compare titles ──────────────────────────
        crossref_title = metadata["crossref_title"]
        score = compare_titles(original_title, crossref_title)

        record.update(metadata)
        record["doi"] = metadata["crossref_doi"] or doi
        record["title_match_score"] = round(score, 3)

        if score >= 0.70:
            record["metadata_validation"] = "Title Match"
        else:
            record["metadata_validation"] = "Needs Review"

            issues.append({
                "filename": record.get("filename", ""),
                "doi": doi,
                "issue": (
                    f"PDF title and Crossref title differ. "
                    f"Similarity score: {score:.3f}"
                ),
            })

        # Overwrite extracted fields with Crossref values.
        if metadata["crossref_title"]:
            record["title"] = metadata["crossref_title"]
        if metadata["crossref_author"]:
            record["author"] = metadata["crossref_author"]
        if metadata["crossref_year"]:
            record["year"] = metadata["crossref_year"]

        record["metadata_source"] = enrichment_method
        record["enrichment_status"] = "Retrieved"

        enriched_rows.append(record)
        time.sleep(0.1)

    output = pd.DataFrame(enriched_rows)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_file, index=False)

    pd.DataFrame(
        issues,
        columns=["filename", "doi", "issue"],
    ).to_csv(issues_file, index=False)

    retrieved = (output["metadata_source"].str.contains("Crossref")).sum()
    doi_retrieved = (output["metadata_source"] == "Crossref DOI lookup").sum()
    title_retrieved = (output["metadata_source"] == "Crossref title search").sum()
    title_matches = (output["metadata_validation"] == "Title Match").sum()
    needs_review = (output["metadata_validation"] == "Needs Review").sum()

    print("\nPDF METADATA ENRICHMENT SUMMARY")
    print("--------------------------------")
    print(f"PDF records processed: {len(output)}")
    print(f"Enriched via Crossref: {retrieved}")
    print(f"  - by DOI lookup:      {doi_retrieved}")
    print(f"  - by title search:    {title_retrieved}")
    print(f"Title matches (>=0.70): {title_matches}")
    print(f"Records needing review: {needs_review}")
    print(f"\nEnriched metadata: {output_file}")
    print(f"Enrichment issues: {issues_file}")
    return output


if __name__ == "__main__":
    enrich_metadata()
