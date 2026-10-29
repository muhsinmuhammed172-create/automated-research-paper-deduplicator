
import pandas as pd
from src.preprocessing import normalize_papers

papers = pd.DataFrame({
    "title": [
        "Machine Learning for Disease Prediction",
        "Machine Learning for Disease Prediction",
        "Deep Learning for Medical Diagnosis"
    ],
    "author": ["A Kumar", "A Kumar", "S Thomas"],
    "doi": ["10.1234/abc", "10.1234/abc", "10.5678/xyz"]
})

result = normalize_papers(papers)

print(result[["record_id", "title", "normalized_title"]])

assert result["record_id"].notna().all()
assert result["record_id"].is_unique

print("\nPASS: Every paper has a unique record ID.")
