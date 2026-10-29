
import pandas as pd
from src.paper_deduplication import detect_paper_duplicates

input_file = "data/sample/deduplication_test_cases.csv"

papers = pd.read_csv(input_file)
results = detect_paper_duplicates(papers)

expected = {
    "T01": "Distinct",
    "T02": "Duplicate",
    "T03": "Distinct",
    "T04": "Duplicate",
    "T05": "Potential Duplicate",
    "T06": "Potential Duplicate",
    "T07": "Distinct",
    "T08": "Duplicate",
    "T09": "Duplicate",
    "T10": "Duplicate",
    "T11": "Duplicate",
    "T12": "Distinct",
}

results["expected_status"] = results["record_id"].map(expected)
results["test_passed"] = (
    results["duplicate_status"] == results["expected_status"]
)

print(results[
    ["record_id", "duplicate_status", "expected_status", "test_passed"]
].to_string(index=False))

print("\nPassed:", results["test_passed"].sum(), "/", len(results))
