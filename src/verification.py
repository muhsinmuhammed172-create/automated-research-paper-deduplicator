
import hashlib
from pathlib import Path

import pandas as pd

QUEUE_FILE = Path("output/verification_queue.csv")
REVIEWED_STATUSES = {"Confirmed Duplicate", "Not Duplicate"}


def create_verification_queue(results):
    candidates = results[
        results["duplicate_status"].isin(
            ["Duplicate", "Potential Duplicate"]
        )
    ].copy()

    # Create a stable key for each candidate.
    key_columns = [
        column for column in [
            "title", "author", "doi", "year",
            "normalized_title", "normalized_author",
            "normalized_doi",
        ]
        if column in candidates.columns
    ]

    def make_key(row):
        values = [
            str(row.get(column, "") or "").strip().lower()
            for column in key_columns
        ]
        return hashlib.sha256(
            "|".join(values).encode("utf-8")
        ).hexdigest()

    candidates["record_key"] = candidates.apply(make_key, axis=1)
    candidates["verification_status"] = "Pending"
    candidates["reviewer_decision"] = ""

    # Restore previous decisions by record key.
    if QUEUE_FILE.exists():
        previous = pd.read_csv(QUEUE_FILE).fillna("")

        if {"record_key", "verification_status"}.issubset(previous.columns):
            previous = previous.drop_duplicates(
                subset=["record_key"], keep="last"
            ).set_index("record_key")

            for index, row in candidates.iterrows():
                key = row["record_key"]

                if key in previous.index:
                    old = previous.loc[key]
                    candidates.at[index, "verification_status"] = (
                        old.get("verification_status", "Pending")
                    )
                    candidates.at[index, "reviewer_decision"] = (
                        old.get("reviewer_decision", "")
                    )

    return candidates


def review_queue():
    if not QUEUE_FILE.exists():
        print("Verification queue not found. Run main.py first.")
        return

    review = pd.read_csv(QUEUE_FILE).fillna("")

    if review.empty:
        print("No records need verification.")
        return

    for index, row in review.iterrows():
        status = str(row.get("verification_status", "Pending"))

        if status in REVIEWED_STATUSES:
            continue

        print("\n" + "=" * 50)
        print("Queue item:", index + 1)
        print("Title:", row.get("title", ""))
        print("Author:", row.get("author", ""))
        print("DOI:", row.get("doi", ""))
        print("Algorithm status:", row.get("duplicate_status", ""))
        print("Matched record:", row.get("matched_record", ""))

        print("\n1. Confirm duplicate")
        print("2. Not a duplicate")
        print("3. Leave pending")

        choice = input("Your decision (1/2/3): ").strip()

        if choice == "1":
            review.at[index, "verification_status"] = "Confirmed Duplicate"
            review.at[index, "reviewer_decision"] = "Confirmed Duplicate"
        elif choice == "2":
            review.at[index, "verification_status"] = "Not Duplicate"
            review.at[index, "reviewer_decision"] = "Not Duplicate"
        elif choice != "3":
            print("Invalid choice; leaving this record pending.")

        # Save each decision immediately.
        review.to_csv(QUEUE_FILE, index=False)

    print("\nVerification decisions saved to:", QUEUE_FILE)
