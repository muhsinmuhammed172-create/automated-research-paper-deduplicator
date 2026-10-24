
import pandas as pd
from src.preprocessing import normalize_papers
from src.similarity import calculate_title_similarity


def detect_paper_duplicates(papers, similarity_threshold=85):
    papers = normalize_papers(papers).reset_index(drop=True)

    papers["normalized_doi"] = (
        papers["doi"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    papers["duplicate_status"] = "Distinct"
    papers["matched_record"] = ""
    papers["title_similarity"] = 0.0

    for i in range(len(papers)):
        if papers.loc[i, "duplicate_status"] != "Distinct":
            continue

        for j in range(i):
            doi_i = papers.loc[i, "normalized_doi"]
            doi_j = papers.loc[j, "normalized_doi"]

            title_i = papers.loc[i, "normalized_title"]
            title_j = papers.loc[j, "normalized_title"]

            author_i = papers.loc[i, "normalized_author"]
            author_j = papers.loc[j, "normalized_author"]

            # DOI match: strong duplicate candidate
            if doi_i and doi_j and doi_i == doi_j:
                papers.loc[i, "duplicate_status"] = "Duplicate"
                papers.loc[i, "matched_record"] = str(j + 1)
                break

            # Exact title and author match
            if title_i and author_i and title_i == title_j and author_i == author_j:
                papers.loc[i, "duplicate_status"] = "Duplicate"
                papers.loc[i, "matched_record"] = str(j + 1)
                break

            # Fuzzy title matching for possible duplicates
            score = calculate_title_similarity(title_i, title_j)
            papers.loc[i, "title_similarity"] = max(
                papers.loc[i, "title_similarity"], score
            )

            if score >= similarity_threshold:
                papers.loc[i, "duplicate_status"] = "Potential Duplicate"
                papers.loc[i, "matched_record"] = str(j + 1)

    return papers
