
import pandas as pd

from src.preprocessing import normalize_papers
from src.similarity import calculate_title_similarity


def detect_paper_duplicates(papers: pd.DataFrame, similarity_threshold: float = 85) -> pd.DataFrame:
    """Detect duplicate and potential-duplicate paper records.

    Three matching rules are applied in priority order for every pair
    (i, j) where j < i:

    Rule 1 — Matching non-empty normalised DOI → Duplicate
    Rule 2 — Exact normalised title match (author optional) → Duplicate
    Rule 3 — Fuzzy title similarity ≥ threshold → Potential Duplicate

    Rule 2 previously required both title AND author to be non-empty,
    which caused exact-title matches to be missed when author metadata
    was absent.  The revised rule matches on title alone when both
    records lack author information.
    """

    papers = normalize_papers(papers).reset_index(drop=True)

    papers["duplicate_status"] = "Distinct"
    papers["matched_record"] = ""
    papers["title_similarity"] = 0.0
    papers["match_reason"] = ""

    for i in range(len(papers)):
        # Do not reclassify a record already identified as a duplicate.
        if papers.loc[i, "duplicate_status"] != "Distinct":
            continue

        best_score = 0.0
        best_match_id = ""
        best_match_reason = ""

        for j in range(i):
            doi_i = str(papers.loc[i, "normalized_doi"]).strip()
            doi_j = str(papers.loc[j, "normalized_doi"]).strip()

            title_i = str(papers.loc[i, "normalized_title"]).strip()
            title_j = str(papers.loc[j, "normalized_title"]).strip()

            author_i = str(papers.loc[i, "normalized_author"]).strip()
            author_j = str(papers.loc[j, "normalized_author"]).strip()

            matched_id = str(papers.loc[j, "record_id"])

            # ── Rule 1: Matching non-empty DOI ───────────────────────────
            if doi_i and doi_j and doi_i == doi_j:
                papers.loc[i, "duplicate_status"] = "Duplicate"
                papers.loc[i, "matched_record"] = matched_id
                papers.loc[i, "match_reason"] = "DOI Match"
                papers.loc[i, "title_similarity"] = (
                    calculate_title_similarity(title_i, title_j)
                )
                break

            # ── Rule 2a: Exact title + matching authors ───────────────────
            if (
                title_i
                and title_i == title_j
                and author_i
                and author_j
                and author_i == author_j
            ):
                papers.loc[i, "duplicate_status"] = "Duplicate"
                papers.loc[i, "matched_record"] = matched_id
                papers.loc[i, "match_reason"] = "Exact Title and Author Match"
                papers.loc[i, "title_similarity"] = 100.0
                break

            # ── Rule 2b: Exact title when both records have no author ─────
            if title_i and title_i == title_j and not author_i and not author_j:
                papers.loc[i, "duplicate_status"] = "Duplicate"
                papers.loc[i, "matched_record"] = matched_id
                papers.loc[i, "match_reason"] = "Exact Title Match (no author)"
                papers.loc[i, "title_similarity"] = 100.0
                break

            # ── Rule 3: Fuzzy title similarity ───────────────────────────
            if title_i and title_j:
                score = calculate_title_similarity(title_i, title_j)

                if score > best_score:
                    best_score = score
                    best_match_id = matched_id
                    best_match_reason = "Title Similarity"

        # Save a fuzzy match only if it reaches the threshold.
        if papers.loc[i, "duplicate_status"] == "Distinct":
            papers.loc[i, "title_similarity"] = best_score

            if best_score >= similarity_threshold:
                papers.loc[i, "duplicate_status"] = "Potential Duplicate"
                papers.loc[i, "matched_record"] = best_match_id
                papers.loc[i, "match_reason"] = best_match_reason

    return papers
