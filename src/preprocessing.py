
import re
import pandas as pd


def normalize_text(value):
    """Normalize text for metadata comparison."""
    if pd.isna(value):
        return ""

    value = str(value).lower().strip()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value


def normalize_papers(papers):
    """Create normalized title and author columns."""
    papers = papers.copy()

    papers["normalized_title"] = papers["title"].apply(normalize_text)
    papers["normalized_author"] = papers["author"].apply(normalize_text)

    return papers
