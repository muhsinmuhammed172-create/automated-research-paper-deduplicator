
import re
import pandas as pd
from uuid import uuid4


def normalize_text(value):
    """Normalize text for metadata comparison."""
    if pd.isna(value):
        return ""

    value = str(value).lower().strip()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value


def normalize_papers(papers):
    """Normalize metadata and ensure every paper has a unique ID."""
    papers = papers.copy().reset_index(drop=True)

    if "record_id" not in papers.columns:
        papers["record_id"] = ""

    papers["record_id"] = (
        papers["record_id"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Reject duplicate existing IDs rather than silently changing them.
    existing_ids = papers.loc[
        papers["record_id"] != "", "record_id"
    ]

    if existing_ids.duplicated().any():
        duplicates = existing_ids[existing_ids.duplicated()].tolist()
        raise ValueError(
            f"Duplicate record_id values found: {duplicates}"
        )

    # Assign IDs to records that do not have one.
    for index in papers.index:
        if not papers.at[index, "record_id"]:
            papers.at[index, "record_id"] = f"REC-{uuid4().hex}"

    papers["normalized_title"] = (
        papers["title"].apply(normalize_text)
    )

    papers["normalized_author"] = (
        papers["author"].apply(normalize_text)
    )

    if "doi" in papers.columns:
        papers["normalized_doi"] = (
            papers["doi"]
            .fillna("")
            .apply(normalize_text)
        )

    return papers
