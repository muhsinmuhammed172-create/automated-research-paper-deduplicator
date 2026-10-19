
from src.preprocessing import normalize_papers


def detect_paper_duplicates(papers):
    """Identify duplicate candidates using DOI, title and author."""
    papers = normalize_papers(papers)

    papers["normalized_doi"] = (
        papers["doi"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    papers["duplicate_by_doi"] = False
    valid_doi = papers["normalized_doi"] != ""

    papers.loc[valid_doi, "duplicate_by_doi"] = (
        papers.loc[valid_doi, "normalized_doi"]
        .duplicated(keep="first")
    )

    papers["duplicate_by_title_author"] = (
        papers.duplicated(
            subset=["normalized_title", "normalized_author"],
            keep="first"
        )
        & (papers["normalized_title"] != "")
        & (papers["normalized_author"] != "")
    )

    papers["duplicate_candidate"] = (
        papers["duplicate_by_doi"]
        | papers["duplicate_by_title_author"]
    )

    return papers
