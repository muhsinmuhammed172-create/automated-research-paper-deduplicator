
import re
import pandas as pd
from uuid import uuid4


def normalize_text(value) -> str:
    """Normalize text for metadata comparison.

    Lowercases, strips punctuation, and collapses whitespace so that
    minor formatting differences do not prevent a match.
    """
    if pd.isna(value):
        return ""

    value = str(value).lower().strip()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_author(value) -> str:
    """Normalize an author string for comparison.

    Sorts name tokens so that "Saleem, Muhammad" and "Muhammad Saleem"
    compare as equal after normalization.
    """
    text = normalize_text(value)
    if not text:
        return ""
    # Sort individual name tokens to handle different orderings.
    tokens = sorted(text.split())
    return " ".join(tokens)


def normalize_papers(papers: pd.DataFrame) -> pd.DataFrame:
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

    papers["normalized_title"] = papers["title"].apply(normalize_text)

    # Use author-sort normalization for more robust author matching.
    papers["normalized_author"] = papers["author"].apply(normalize_author)

    if "doi" in papers.columns:
        papers["normalized_doi"] = (
            papers["doi"]
            .fillna("")
            .apply(normalize_text)
        )

    return papers
