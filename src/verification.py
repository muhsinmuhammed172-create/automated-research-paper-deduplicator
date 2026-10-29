
import sys
from pathlib import Path

import pandas as pd


# Select the dataset:
# python src/verification.py crossref
# python src/verification.py synthetic

DATASET = sys.argv[1].lower() if len(sys.argv) > 1 else "synthetic"

if DATASET == "crossref":
    QUEUE_FILE = Path("output/crossref_verification_queue.csv")
    RESULTS_FILE = Path("output/crossref_deduplication_results.csv")
elif DATASET == "synthetic":
    QUEUE_FILE = Path("output/synthetic_verification_queue.csv")
    RESULTS_FILE = Path("output/synthetic_deduplication_results.csv")
else:
    raise ValueError(
        "Invalid dataset. Use 'crossref' or 'synthetic'."
    )


CANDIDATE_STATUSES = {"Duplicate", "Potential Duplicate"}

REVIEWED_STATUSES = {
    "Confirmed Duplicate",
    "Not Duplicate",
}


def create_verification_queue(results):
    """
    Create a queue containing only Duplicate and Potential Duplicate
    records. Preserve existing reviewer decisions using record_id.
    """

    required_columns = {
        "record_id",
        "duplicate_status",
    }

    missing_columns = required_columns - set(results.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    # Only flagged duplicate candidates require manual verification.
    candidates = results[
        results["duplicate_status"].isin(CANDIDATE_STATUSES)
    ].copy()

    if candidates["record_id"].isna().any():
        raise ValueError(
            "Some candidate records have missing record IDs."
        )

    candidates["record_id"] = candidates["record_id"].astype(str)

    if candidates["record_id"].duplicated().any():
        raise ValueError(
            "Duplicate record_id values found in the verification queue."
        )

    candidates["verification_status"] = "Pending"
    candidates["reviewer_decision"] = ""

    # Preserve earlier decisions when the queue is regenerated.
    if QUEUE_FILE.exists() and QUEUE_FILE.stat().st_size > 0:
        previous = pd.read_csv(QUEUE_FILE).fillna("")

        required_previous = {
            "record_id",
            "verification_status",
            "reviewer_decision",
        }

        if required_previous.issubset(previous.columns):
            previous["record_id"] = previous["record_id"].astype(str)

            previous = previous.drop_duplicates(
                subset=["record_id"],
                keep="last",
            )

            previous_lookup = previous.set_index("record_id")

            for index, row in candidates.iterrows():
                record_id = row["record_id"]

                if record_id in previous_lookup.index:
                    old = previous_lookup.loc[record_id]

                    candidates.at[index, "verification_status"] = (
                        old["verification_status"]
                        or "Pending"
                    )

                    candidates.at[index, "reviewer_decision"] = (
                        old["reviewer_decision"]
                    )

    return candidates


def review_queue():
    """
    Review flagged duplicate candidates interactively.
    Save each decision immediately.
    """

    if not QUEUE_FILE.exists():
        print("Verification queue not found.")
        print("Run the main pipeline first to generate the queue.")
        return

    review = pd.read_csv(QUEUE_FILE).fillna("")

    if review.empty:
        print("No duplicate candidates need verification.")
        return

    # Ensure the queue contains only records requiring verification.
    if "duplicate_status" not in review.columns:
        raise ValueError(
            "duplicate_status column is missing from the queue."
        )

    review = review[
        review["duplicate_status"].isin(CANDIDATE_STATUSES)
    ].copy()

    if review.empty:
        print("No Duplicate or Potential Duplicate candidates found.")
        return

    # Load the full dataset to display the matched paper's details.
    if RESULTS_FILE.exists():
        all_papers = pd.read_csv(RESULTS_FILE).fillna("")

        if "record_id" in all_papers.columns:
            all_papers["record_id"] = (
                all_papers["record_id"].astype(str)
            )

            paper_lookup = (
                all_papers
                .drop_duplicates(subset=["record_id"], keep="last")
                .set_index("record_id")
                .to_dict("index")
            )
        else:
            paper_lookup = {}
    else:
        paper_lookup = {}

    total_candidates = len(review)
    reviewed_this_run = 0

    print("\n" + "=" * 65)
    print("RESEARCH PAPER DUPLICATE VERIFICATION")
    print("=" * 65)
    print("Dataset:", DATASET)
    print("Candidates requiring verification:", total_candidates)
    print("Already reviewed:", sum(
        str(status) in REVIEWED_STATUSES
        for status in review["verification_status"]
    ))

    for index, row in review.iterrows():

        status = str(row.get("verification_status", "Pending"))

        # Do not ask the reviewer to decide a second time.
        if status in REVIEWED_STATUSES:
            continue

        matched_id = str(row.get("matched_record", ""))
        matched = paper_lookup.get(matched_id, {})

        print("\n" + "=" * 65)
        print(f"Queue item: {index + 1} of {total_candidates}")

        print("\nCANDIDATE PAPER")
        print("Record ID:", row.get("record_id", ""))
        print("Title:", row.get("title", ""))
        print("Author:", row.get("author", ""))
        print("DOI:", row.get("doi", ""))

        print("\nMATCHED PAPER")

        if matched:
            print("Record ID:", matched_id)
            print("Title:", matched.get("title", ""))
            print("Author:", matched.get("author", ""))
            print("DOI:", matched.get("doi", ""))
        else:
            print("Matched paper details are unavailable.")
            print("Matched record ID:", matched_id or "None")

        print("\nMATCH INFORMATION")
        print("Algorithm status:", row.get("duplicate_status", ""))
        print("Match reason:", row.get("match_reason", ""))
        print("Title similarity:", row.get("title_similarity", ""))

        print("\n1. Confirm duplicate")
        print("2. Not a duplicate")
        print("3. Leave pending and continue")

        choice = input("Your decision (1/2/3): ").strip()

        if choice == "1":
            review.at[index, "verification_status"] = (
                "Confirmed Duplicate"
            )
            review.at[index, "reviewer_decision"] = (
                "Confirmed Duplicate"
            )

        elif choice == "2":
            review.at[index, "verification_status"] = "Not Duplicate"
            review.at[index, "reviewer_decision"] = "Not Duplicate"

        elif choice == "3":
            print("Candidate left pending.")

        else:
            print("Invalid choice. Candidate left pending.")

        # Save immediately to avoid losing decisions.
        review.to_csv(QUEUE_FILE, index=False)
        reviewed_this_run += 1

    print("\n" + "=" * 65)
    print("VERIFICATION SUMMARY")
    print("=" * 65)
    print("Total candidates:", len(review))
    print(
        "Confirmed duplicates:",
        (review["verification_status"] == "Confirmed Duplicate").sum(),
    )
    print(
        "Not duplicates:",
        (review["verification_status"] == "Not Duplicate").sum(),
    )
    print(
        "Pending:",
        (~review["verification_status"].isin(REVIEWED_STATUSES)).sum(),
    )
    print("Decisions processed this run:", reviewed_this_run)
    print("Saved to:", QUEUE_FILE)


if __name__ == "__main__":
    review_queue()
