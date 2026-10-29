
import re
import requests
import pandas as pd
from pathlib import Path

# Crossref API endpoint
API_URL = "https://api.crossref.org/works"
ROWS = 500

OUTPUT_PATH = Path("data/sample/crossref_papers.csv")
ISSUES_PATH = Path("data/sample/crossref_metadata_issues.csv")

params = {
    "query.bibliographic": "systematic literature review",
    "filter": "type:journal-article",
    "rows": ROWS,
    "select": (
        "DOI,title,author,published,published-print,"
        "published-online,container-title,type,URL"
    ),
}

# Replace YOUR_EMAIL with your email address if possible.
headers = {
    "User-Agent": "ResearchPaperDeduplicator/1.0 (mailto:YOUR_EMAIL)"
}


def clean_title(value):
    """Clean extra whitespace from a title."""
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()


def remove_repeated_title(title):
    """
    Remove a title repeated exactly twice within the same field.
    Preserve titles that do not match this pattern.
    """
    title = clean_title(title)
    length = len(title)

    if length >= 2 and length % 2 == 0:
        first_half = title[:length // 2].strip()
        second_half = title[length // 2:].strip()

        if first_half.casefold() == second_half.casefold():
            return first_half

    return title


def get_year(item):
    """Get the publication year from available date fields."""
    for field in ("published", "published-print", "published-online"):
        date_parts = item.get(field, {}).get("date-parts", [])

        if date_parts and date_parts[0]:
            return date_parts[0][0]

    return ""


def get_authors(item):
    """Extract author names from Crossref metadata."""
    names = []

    for author in item.get("author", []):
        given = author.get("given", "")
        family = author.get("family", "")

        name = " ".join(
            part for part in [given, family] if part
        ).strip()

        if name:
            names.append(name)

    return "; ".join(names)


print(f"Fetching up to {ROWS} records from Crossref...")

response = requests.get(
    API_URL,
    params=params,
    headers=headers,
    timeout=60,
)
response.raise_for_status()

items = response.json()["message"]["items"]

records = []
issues = []

for item in items:
    titles = item.get("title", [])

    # Clean the title and remove exact repetition if present.
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
        issues.append({
            **record,
            "issue": "Missing title",
        })
        continue

    # Keep valid records even when the original title was repeated.
    records.append(record)

    # Record the title correction for auditing.
    if original_title != title:
        issues.append({
            **record,
            "issue": "Repeated title cleaned",
        })


# Save the dataset separately from the synthetic dataset.
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

df = pd.DataFrame(records)
df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)

# Save metadata issues and corrections for inspection.
issue_columns = [
    "title",
    "author",
    "doi",
    "year",
    "journal",
    "type",
    "url",
    "source",
    "issue",
]

issues_df = pd.DataFrame(issues, columns=issue_columns)
issues_df.to_csv(
    ISSUES_PATH,
    index=False,
    encoding="utf-8-sig",
)

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

    print("\nRepeated-title corrections:")
    corrected = issues_df[
        issues_df["issue"] == "Repeated title cleaned"
    ]

    if corrected.empty:
        print("No repeated titles found.")
    else:
        print(
            corrected[["title", "doi"]]
            .to_string(index=False)
        )
