
from pathlib import Path

import pandas as pd


RESULTS_FILE = Path("output/crossref_deduplication_results.csv")
QUEUE_FILE = Path("output/crossref_verification_queue.csv")
OUTPUT_FILE = Path("output/crossref_deduplicated_records.csv")


def build_retained_dataset():
    if not RESULTS_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {RESULTS_FILE}")

    if not QUEUE_FILE.exists():
        raise FileNotFoundError(f"Verification queue not found: {QUEUE_FILE}")

    papers = pd.read_csv(RESULTS_FILE).fillna("")
    queue = pd.read_csv(QUEUE_FILE).fillna("")

    if "record_id" not in papers.columns:
        raise ValueError("record_id is missing from the results dataset.")

    if "record_id" not in queue.columns:
        raise ValueError("record_id is missing from the verification queue.")

    if "verification_status" not in queue.columns:
        raise ValueError("verification_status is missing from the queue.")

    papers["record_id"] = papers["record_id"].astype(str)
    queue["record_id"] = queue["record_id"].astype(str)

    # Do not finalize while any flagged candidate remains unreviewed.
    pending = queue[
        ~queue["verification_status"].isin(
            ["Confirmed Duplicate", "Not Duplicate"]
        )
    ]

    if not pending.empty:
        raise ValueError(
            f"{len(pending)} candidates are still pending. "
            "Complete verification before building the final dataset."
        )

    # Record IDs manually confirmed as duplicates.
    duplicate_ids = set(
        queue.loc[
            queue["verification_status"] == "Confirmed Duplicate",
            "record_id",
        ]
    )

    # Remove only the candidate records confirmed as duplicates.
    retained = papers[
        ~papers["record_id"].isin(duplicate_ids)
    ].copy()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    retained.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 55)
    print("DEDUPLICATION SUMMARY")
    print("=" * 55)
    print("Original records:", len(papers))
    print("Confirmed duplicate records removed:", len(duplicate_ids))
    print("Records retained:", len(retained))
    print("Output file:", OUTPUT_FILE)


if __name__ == "__main__":
    build_retained_dataset()
