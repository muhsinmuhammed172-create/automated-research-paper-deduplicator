
import time
from pathlib import Path

import pandas as pd
import requests


INPUT_FILE = Path("output/pdf_extracted_metadata.csv")
OUTPUT_FILE = Path("output/pdf_enriched_metadata.csv")
ISSUES_FILE = Path("output/pdf_metadata_enrichment_issues.csv")

CROSSREF_API = "https://api.crossref.org/works/"


def clean_doi(value):
    """Normalize a DOI copied from a PDF."""
    doi = str(value or "").strip()

    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "doi:",
    ):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):].strip()

    return doi.rstrip(".,;:)]}")


def crossref_lookup(doi):
    """Retrieve metadata for a DOI from Crossref."""
    try:
        response = requests.get(
            CROSSREF_API + requests.utils.quote(doi, safe="/"),
            timeout=20,
            headers={"User-Agent": "MCA-PaperDeduplicator/1.0"},
        )

        if response.status_code != 200:
            return None, f"Crossref HTTP {response.status_code}"

        message = response.json().get("message", {})
        title_list = message.get("title", [])
        author_list = message.get("author", [])

        authors = []
        for author in author_list:
            name = " ".join(
                part for part in [
                    author.get("given", ""),
                    author.get("family", ""),
                ] if part
            ).strip()

            if name:
                authors.append(name)

        published = (
            message.get("published-print")
            or message.get("published-online")
            or message.get("published")
            or {}
        )

        date_parts = published.get("date-parts", [[]])
        year = str(date_parts[0][0]) if date_parts and date_parts[0] else ""

        return {
            "crossref_title": title_list[0] if title_list else "",
            "crossref_author": "; ".join(authors),
            "crossref_year": year,
            "crossref_doi": message.get("DOI", doi),
        }, ""

    except (requests.RequestException, ValueError) as error:
        return None, str(error)


def enrich_metadata():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE).fillna("")
    enriched_rows = []
    issues = []

    for _, row in df.iterrows():
        record = row.to_dict()
        doi = clean_doi(record.get("doi", ""))

        if not doi:
            record["metadata_source"] = "PDF extraction"
            record["enrichment_status"] = "No DOI; manual review needed"
            enriched_rows.append(record)
            continue

        metadata, error = crossref_lookup(doi)

        if metadata:
            # Preserve original extracted values for comparison.
            record["pdf_title"] = record.get("title", "")
            record["pdf_author"] = record.get("author", "")
            record["pdf_year"] = record.get("year", "")

            # Prefer Crossref fields when Crossref supplies them.
            for source_field, target_field in [
                ("crossref_title", "title"),
                ("crossref_author", "author"),
                ("crossref_year", "year"),
            ]:
                if metadata[source_field]:
                    record[target_field] = metadata[source_field]

            record["doi"] = metadata["crossref_doi"]
            record["metadata_source"] = "Crossref DOI lookup"
            record["enrichment_status"] = "Retrieved"
        else:
            record["metadata_source"] = "PDF extraction"
            record["enrichment_status"] = "Lookup failed; manual review needed"

            issues.append({
                "filename": record.get("filename", ""),
                "doi": doi,
                "issue": error,
            })

        enriched_rows.append(record)
        time.sleep(0.1)

    output = pd.DataFrame(enriched_rows)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_FILE, index=False)

    pd.DataFrame(
        issues, columns=["filename", "doi", "issue"]
    ).to_csv(ISSUES_FILE, index=False)

    print(f"PDF records processed: {len(output)}")
    print(
        "Records enriched from Crossref: "
        f"{(output['metadata_source'] == 'Crossref DOI lookup').sum()}"
    )
    print(
        "Records needing manual review: "
        f"{output['enrichment_status'].astype(str).str.contains('review needed').sum()}"
    )
    print(f"Enriched metadata saved to: {OUTPUT_FILE}")
    print(f"Lookup issues saved to: {ISSUES_FILE}")


if __name__ == "__main__":
    enrich_metadata()
