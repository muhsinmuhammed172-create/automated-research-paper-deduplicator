
import pandas as pd

from src.paper_deduplication import detect_paper_duplicates
from src.verification import create_verification_queue

INPUT_FILE = "data/sample/papers.csv"
OUTPUT_FILE = "output/deduplication_results.csv"
QUEUE_FILE = "output/verification_queue.csv"


def main():
    # 1. Load input records
    papers = pd.read_csv(INPUT_FILE)

    # 2. Detect duplicate candidates
    results = detect_paper_duplicates(papers)

    columns = [
        "title",
        "author",
        "doi",
        "duplicate_status",
        "matched_record",
        "title_similarity",
    ]

    print(results[columns].to_string(index=False))

    print("\nTotal records:", len(results))
    print(
        "Duplicate candidates:",
        (results["duplicate_status"] == "Duplicate").sum()
    )
    print(
        "Potential duplicates:",
        (results["duplicate_status"] == "Potential Duplicate").sum()
    )

    # 3. Save detection results
    results.to_csv(OUTPUT_FILE, index=False)
    print("\nResults saved to:", OUTPUT_FILE)

    # 4. Create and save the verification queue
    queue = create_verification_queue(results)
    queue.to_csv(QUEUE_FILE, index=False)

    pending = (
        queue["verification_status"] == "Pending"
    ).sum()

    print("\nVerification queue updated:", QUEUE_FILE)
    print("Total candidates:", len(queue))
    print("Pending reviews:", pending)


if __name__ == "__main__":
    main()
