
"""Download up to 500 research-paper records from the Crossref API.

Usage
-----
python fetch_crossref.py

The script saves the dataset to ``data/sample/crossref_papers.csv``
and logs any metadata issues to ``data/sample/crossref_metadata_issues.csv``.
"""

import re
import sys

import requests
import pandas as pd
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


API_URL = "https://api.crossref.org/works"
ROWS = 500

OUTPUT_PATH = Path("data/sample/crossref_papers.csv")
ISSUES_PATH = Path("data/sample/crossref_metadata_issues.csv")

PARAMS = {
    "query.bibliographic": "systematic literature review",
    "filter": "type:journal-article",
    "rows": ROWS,
    "select": (
        "DOI,title,author,published,published-print,"
        "published-online,container-title,type,URL"
    ),
}

# Replace with your actual email address for Crossref's polite pool.
HEADERS = {
    "User-Agent": "ResearchPaperDeduplicator/1.0 (mailto:your-email@example.com)"
}


def _make_session() -> requests.Session:
    """Create a requests Session with automatic retry on transient errors."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def clean_title(value) -> str:
    """Clean extra whitespace from a title."""
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()


def remove_repeated_title(title: str) -> str:
    """Remove a title repeated exactly twice within the same field.
    Preserve titles that do not match this pattern.
    """
    title = clean_title(title)
    length = len(title)

    if length >= 2 and length % 2 == 0:
        first_half = title[: length // 2].strip()
        second_half = title[length // 2 :].strip()

        if first_half.casefold() == second_half.casefold():
            return first_half

    return title


def get_year(item: dict) -> str:
    """Get the publication year from available date fields."""
    for field in ("published", "published-print", "published-online"):
        date_parts = item.get(field, {}).get("date-parts", [])
        if date_parts and date_parts[0]:
            return str(date_parts[0][0])
    return ""


def get_authors(item: dict) -> str:
    """Extract author names from Crossref metadata."""
    names = []
    for author in item.get("author", []):
        given = author.get("given", "")
        family = author.get("family", "")
        name = " ".join(part for part in [given, family] if part).strip()
        if name:
            names.append(name)
    return "; ".join(names)


def fetch_crossref_records() -> None:
    """Fetch records from Crossref and save to CSV."""
    print(f"Fetching up to {ROWS} records from Crossref...")

    session = _make_session()

    response = session.get(API_URL, params=PARAMS, headers=HEADERS, timeout=60)
    response.raise_for_status()

    items = response.json()["message"]["items"]

    records = []
    issues = []

    for item in items:
        titles = item.get("title", [])

        original_title = clean_title(titles[0]) if titles else ""
        title = remove_repeated_title(original_title)

        authors = get_authors(item)
        doi = item.get("DOI", "")
        journals = item.get("container-title", [])

        record = {
            "title": title,
            "author": authors,
            "doi": doi,
            "year": get_year(item),
            "journal": journals[0] if journals else "",
            "type": item.get("type", ""),
            "url": item.get("URL", ""),
            "source": "Crossref",
        }

        # Do not save records without usable titles.
        if not title:
            issues.append({**record, "issue": "Missing title"})
            continue

        records.append(record)

        # Record the title correction for auditing.
        if original_title != title:
            issues.append({**record, "issue": "Repeated title cleaned"})

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    issue_columns = [
        "title", "author", "doi", "year",
        "journal", "type", "url", "source", "issue",
    ]
    issues_df = pd.DataFrame(issues, columns=issue_columns)
    issues_df.to_csv(ISSUES_PATH, index=False, encoding="utf-8-sig")

    print("\nCrossref download completed.")
    print(f"Records returned by Crossref: {len(items)}")
    print(f"Usable records saved: {len(df)}")
    print(f"Metadata issues/corrections logged: {len(issues_df)}")
    print(f"Main dataset: {OUTPUT_PATH}")
    print(f"Metadata issues: {ISSUES_PATH}")

    if not df.empty:
        print("\nFirst five records:")
        print(
            df[["title", "author", "doi", "year"]]
            .head()
            .to_string(index=False)
        )

        corrected = issues_df[issues_df["issue"] == "Repeated title cleaned"]
        print("\nRepeated-title corrections:")
        if corrected.empty:
            print("No repeated titles found.")
        else:
            print(corrected[["title", "doi"]].to_string(index=False))


if __name__ == "__main__":
    fetch_crossref_records()
