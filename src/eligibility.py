
from pathlib import Path

import pandas as pd


SCREENING_FILE = Path("output/crossref_screening_queue.csv")
ELIGIBILITY_FILE = Path("output/crossref_eligibility_queue.csv")

ELIGIBILITY_DECISIONS = {"Include", "Exclude"}


def create_eligibility_queue():
    """Prepare full-text eligibility records from included papers."""

    if not SCREENING_FILE.exists():
        raise FileNotFoundError(
            f"Screening queue not found: {SCREENING_FILE}"
        )

    screening = pd.read_csv(SCREENING_FILE).fillna("")

    required = {"record_id", "screening_decision"}
    if not required.issubset(screening.columns):
        raise ValueError(
            "Screening file must contain record_id and "
            "screening_decision."
        )

    # Only papers included at title-and-abstract screening proceed.
    included = screening[
        screening["screening_decision"].astype(str).str.strip()
        == "Include"
    ].copy()

    columns = [
        "record_id", "title", "author", "doi", "year", "journal"
    ]
    columns = [column for column in columns if column in included.columns]

    queue = included[columns].copy()

    queue["eligibility_decision"] = "Pending"
    queue["exclusion_reason"] = ""

    # Preserve decisions from previous runs.
    if ELIGIBILITY_FILE.exists():
        previous = pd.read_csv(ELIGIBILITY_FILE).fillna("")

        required_previous = {
            "record_id",
            "eligibility_decision",
            "exclusion_reason",
        }

        if required_previous.issubset(previous.columns):
            previous = previous[
                [
                    "record_id",
                    "eligibility_decision",
                    "exclusion_reason",
                ]
            ].copy()

            previous["record_id"] = previous["record_id"].astype(str)
            previous = previous.drop_duplicates(
                "record_id", keep="last"
            ).set_index("record_id")

            queue["record_id"] = queue["record_id"].astype(str)
            queue = queue.set_index("record_id")

            for column in [
                "eligibility_decision",
                "exclusion_reason",
            ]:
                saved = pd.Series(
                    queue.index.map(previous[column]),
                    index=queue.index,
                    dtype="object",
                )

                queue[column] = saved.where(
                    saved.notna(), queue[column]
                )

            queue["eligibility_decision"] = (
                queue["eligibility_decision"].replace("", "Pending")
            )

            queue = queue.reset_index()

    ELIGIBILITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    queue.to_csv(ELIGIBILITY_FILE, index=False)

    print(f"Records eligible for full-text assessment: {len(queue)}")
    print(f"Eligibility queue saved to: {ELIGIBILITY_FILE}")

    return queue


def review_eligibility_queue():
    """Review full texts and save eligibility decisions."""

    queue = create_eligibility_queue()

    for index in queue.index:
        decision = str(
            queue.at[index, "eligibility_decision"]
        ).strip()

        if decision in ELIGIBILITY_DECISIONS:
            continue

        print("\n" + "=" * 60)
        print(f"Paper {index + 1} of {len(queue)}")
        print(f"Title: {queue.at[index, 'title']}")
        print(f"Authors: {queue.at[index, 'author']}")
        print(f"Year: {queue.at[index, 'year']}")
        print(f"Journal: {queue.at[index, 'journal']}")
        print(f"DOI: {queue.at[index, 'doi']}")

        print("\nReview the full text before deciding.")
        print("1. Include in the final review")
        print("2. Exclude after full-text assessment")
        print("3. Leave pending and continue")
        print("4. Save and exit")

        choice = input("Choose 1, 2, 3, or 4: ").strip()

        if choice == "4":
            break

        if choice == "1":
            queue.at[index, "eligibility_decision"] = "Include"
            queue.at[index, "exclusion_reason"] = ""

        elif choice == "2":
            reason = input(
                "Enter the full-text exclusion reason: "
            ).strip()

            if not reason:
                print(
                    "An exclusion reason is required. "
                    "Record left pending."
                )
                continue

            queue.at[index, "eligibility_decision"] = "Exclude"
            queue.at[index, "exclusion_reason"] = reason

        elif choice == "3":
            continue

        else:
            print("Invalid choice. Record left pending.")
            continue

        queue.to_csv(ELIGIBILITY_FILE, index=False)
        print("Decision saved.")

    queue.to_csv(ELIGIBILITY_FILE, index=False)

    decisions = queue["eligibility_decision"].astype(str).str.strip()

    print("\nFull-text eligibility summary")
    print("-" * 35)
    print(f"Total records: {len(queue)}")
    print(f"Included: {(decisions == 'Include').sum()}")
    print(f"Excluded: {(decisions == 'Exclude').sum()}")
    print(
        f"Pending: "
        f"{(~decisions.isin(ELIGIBILITY_DECISIONS)).sum()}"
    )
    print(f"Saved to: {ELIGIBILITY_FILE}")


if __name__ == "__main__":
    review_eligibility_queue()
