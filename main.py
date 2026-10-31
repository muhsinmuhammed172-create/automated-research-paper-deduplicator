
"""Main entry point for the metadata-based deduplication pipeline.

Usage
-----
python main.py --input crossref
python main.py --input synthetic
python main.py --input plant_test
"""

import argparse
from pathlib import Path

import pandas as pd

from src.paper_deduplication import detect_paper_duplicates
from src.preprocessing import normalize_papers
from src.verification import create_verification_queue


DEFAULT_INPUT = Path("data/sample/papers.csv")
CROSSREF_INPUT = Path("data/sample/crossref_papers.csv")
PLANT_TEST_INPUT = Path("output/plant_disease_test_metadata.csv")

PROCESSED_DIR = Path("data/processed")
OUTPUT_DIR = Path("output")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Research-paper deduplication system"
    )
    parser.add_argument(
        "--input",
        choices=["synthetic", "crossref", "plant_test"],
        default="synthetic",
        help="Choose the dataset to process",
    )
    args = parser.parse_args()

    if args.input == "crossref":
        input_file = CROSSREF_INPUT
        dataset_name = "crossref"
    elif args.input == "plant_test":
        input_file = PLANT_TEST_INPUT
        dataset_name = "plant_test"
    else:
        input_file = DEFAULT_INPUT
        dataset_name = "synthetic"

    processed_file = PROCESSED_DIR / f"{dataset_name}_papers_with_ids.csv"
    output_file = OUTPUT_DIR / f"{dataset_name}_deduplication_results.csv"
    queue_file = OUTPUT_DIR / f"{dataset_name}_verification_queue.csv"

    if not input_file.exists():
        raise FileNotFoundError(f"Dataset not found: {input_file}")

    papers = pd.read_csv(input_file).fillna("")

    required_columns = {"title", "author", "doi"}
    missing = required_columns - set(papers.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Reuse persistent IDs only when source records still match.
    if processed_file.exists():
        saved = pd.read_csv(processed_file).fillna("")

        same_records = len(saved) == len(papers) and all(
            str(saved.iloc[i].get("title", "")) == str(papers.iloc[i].get("title", ""))
            and str(saved.iloc[i].get("author", "")) == str(papers.iloc[i].get("author", ""))
            and str(saved.iloc[i].get("doi", "")) == str(papers.iloc[i].get("doi", ""))
            for i in range(len(papers))
        )

        if same_records and "record_id" in saved.columns:
            papers["record_id"] = saved["record_id"]
        else:
            print("Dataset changed. Creating IDs for the current records.")
            papers = normalize_papers(papers)
    else:
        papers = normalize_papers(papers)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    papers.to_csv(processed_file, index=False)

    print(f"\nDataset: {dataset_name}")
    print(f"Input records: {len(papers)}")
    print(f"Persistent IDs saved: {processed_file}")

    results = detect_paper_duplicates(papers)

    display_columns = [
        "record_id", "title", "author", "doi",
        "duplicate_status", "matched_record",
        "title_similarity", "match_reason",
    ]
    display_columns = [col for col in display_columns if col in results.columns]

    print("\nDetection results:")
    print(results[display_columns].to_string(index=False))

    print("\nTotal records:", len(results))
    print(
        "Duplicate candidates:",
        (results["duplicate_status"] == "Duplicate").sum(),
    )
    print(
        "Potential duplicates:",
        (results["duplicate_status"] == "Potential Duplicate").sum(),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_file, index=False)
    print("\nDetection results saved:", output_file)

    # Pass dataset_name so the queue is written to the correct file.
    queue = create_verification_queue(results, dataset=dataset_name)
    queue.to_csv(queue_file, index=False)

    print("Verification queue saved:", queue_file)
    print("Total candidates:", len(queue))

    if "verification_status" in queue.columns:
        print(
            "Pending reviews:",
            (queue["verification_status"] == "Pending").sum(),
        )


if __name__ == "__main__":
    main()
