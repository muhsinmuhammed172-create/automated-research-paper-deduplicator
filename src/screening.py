
from pathlib import Path

import pandas as pd


# Project file paths
RETAINED_FILE = Path("output/crossref_deduplicated_records.csv")
SCREENING_FILE = Path("output/crossref_screening_queue.csv")

REVIEWED_DECISIONS = {"Include", "Exclude"}


def create_screening_queue():
    """Build the screening queue from retained records and preserve decisions."""

    if not RETAINED_FILE.exists():
        raise FileNotFoundError(
            f"Retained dataset not found: {RETAINED_FILE}\n"
            "Run 'python src/build_retained_dataset.py' first."
        )

    records = pd.read_csv(RETAINED_FILE).fillna("")

    if "record_id" not in records.columns:
        raise ValueError(
            "The retained dataset must contain record_id."
        )

    # Select the metadata needed for title-and-abstract screening.
    columns = [
        "record_id",
        "title",
        "author",
        "doi",
        "year",
        "journal",
    ]

    columns = [column for column in columns if column in records.columns]
    queue = records[columns].copy()

    # Prevent ambiguous decision preservation.
    queue["record_id"] = queue["record_id"].astype(str)

    if queue["record_id"].duplicated().any():
        raise ValueError(
            "The retained dataset contains duplicate record_id values."
        )

    # Default decisions for new records.
    queue["screening_decision"] = "Pending"
    queue["exclusion_reason"] = ""

    # Preserve decisions from the existing screening queue.
    if SCREENING_FILE.exists():
        previous = pd.read_csv(SCREENING_FILE).fillna("")

        required_columns = {
            "record_id",
            "screening_decision",
            "exclusion_reason",
        }

        if required_columns.issubset(previous.columns):
            previous = previous[
                [
                    "record_id",
                    "screening_decision",
                    "exclusion_reason",
                ]
            ].copy()

            previous["record_id"] = previous["record_id"].astype(str)

            # Keep the latest saved decision for each record.
            previous = previous.drop_duplicates(
                subset="record_id",
                keep="last",
            )

            # Merge saved decisions into the retained dataset.
            queue = queue.merge(
                previous,
                on="record_id",
                how="left",
                suffixes=("", "_previous"),
                validate="one_to_one",
            )

            for column in ["screening_decision", "exclusion_reason"]:
                previous_column = f"{column}_previous"

                if previous_column in queue.columns:
                    saved_values = queue[previous_column].fillna("").astype(str)
                    use_saved = saved_values.str.strip() != ""

                    queue.loc[use_saved, column] = saved_values[use_saved]
                    queue.drop(columns=[previous_column], inplace=True)

    # Ensure blank decisions are treated as Pending.
    queue["screening_decision"] = (
        queue["screening_decision"]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", "Pending")
    )

    queue["exclusion_reason"] = (
        queue["exclusion_reason"].fillna("").astype(str)
    )

    SCREENING_FILE.parent.mkdir(parents=True, exist_ok=True)
    queue.to_csv(SCREENING_FILE, index=False)

    print(f"Retained records loaded: {len(records)}")
    print(f"Records prepared for screening: {len(queue)}")
    print(f"Existing decisions preserved where record IDs match.")
    print(f"Screening queue saved to: {SCREENING_FILE}")

    return queue


def review_screening_queue():
    """Review pending records and save each completed decision immediately."""

    queue = create_screening_queue()

    for index in queue.index:
        decision = str(queue.at[index, "screening_decision"]).strip()

        # Skip records already reviewed.
        if decision in REVIEWED_DECISIONS:
            continue

        print("\n" + "=" * 60)
        print(f"Record {index + 1} of {len(queue)}")
        print(f"Title: {queue.at[index, 'title']}")
        print(f"Authors: {queue.at[index, 'author']}")
        print(f"Year: {queue.at[index, 'year']}")
        print(f"Journal: {queue.at[index, 'journal']}")
        print(f"DOI: {queue.at[index, 'doi']}")

        print("\n1. Include for full-text assessment")
        print("2. Exclude")
        print("3. Leave pending and continue")
        print("4. Save and exit")

        choice = input("Choose 1, 2, 3, or 4: ").strip()

        if choice == "4":
            break

        if choice == "1":
            queue.at[index, "screening_decision"] = "Include"
            queue.at[index, "exclusion_reason"] = ""

        elif choice == "2":
            reason = input("Enter the reason for exclusion: ").strip()

            if not reason:
                print("An exclusion reason is required. Record left pending.")
                continue

            queue.at[index, "screening_decision"] = "Exclude"
            queue.at[index, "exclusion_reason"] = reason

        elif choice == "3":
            continue

        else:
            print("Invalid choice. Record left pending.")
            continue

        # Save immediately after every completed decision.
        queue.to_csv(SCREENING_FILE, index=False)
        print("Decision saved.")

    queue.to_csv(SCREENING_FILE, index=False)

    decisions = queue["screening_decision"].astype(str).str.strip()

    included = (decisions == "Include").sum()
    excluded = (decisions == "Exclude").sum()
    pending = (~decisions.isin(REVIEWED_DECISIONS)).sum()

    print("\nScreening summary")
    print("-" * 30)
    print(f"Total records: {len(queue)}")
    print(f"Included: {included}")
    print(f"Excluded: {excluded}")
    print(f"Pending: {pending}")
    print(f"Saved to: {SCREENING_FILE}")


if __name__ == "__main__":
    review_screening_queue()
