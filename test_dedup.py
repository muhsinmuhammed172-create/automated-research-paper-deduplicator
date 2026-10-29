
import pandas as pd
from src.preprocessing import normalize_papers
from src.paper_deduplication import detect_paper_duplicates

papers = pd.read_csv("data/sample/dedup_test.csv").fillna("")
papers = normalize_papers(papers)

results = detect_paper_duplicates(papers)

print(results[
    [
        "title",
        "doi",
        "duplicate_status",
        "matched_record",
        "title_similarity",
        "match_reason",
    ]
].to_string(index=False))

print("\nStatus counts:")
print(results["duplicate_status"].value_counts())
