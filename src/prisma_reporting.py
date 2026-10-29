
import sys
from pathlib import Path

import pandas as pd


# Usage:
# python src/prisma_reporting.py crossref
# python src/prisma_reporting.py synthetic

DATASET = sys.argv[1].lower() if len(sys.argv) > 1 else "synthetic"

if DATASET == "crossref":
    RESULTS_FILE = Path("output/crossref_deduplication_results.csv")
    QUEUE_FILE = Path("output/crossref_verification_queue.csv")
    RETAINED_FILE = Path("output/crossref_deduplicated_records.csv")
    REPORT_FILE = Path("output/crossref_prisma_summary.csv")

elif DATASET == "synthetic":
    RESULTS_FILE = Path("output/synthetic_deduplication_results.csv")
    QUEUE_FILE = Path("output/synthetic_verification_queue.csv")
    RETAINED_FILE = Path("output/synthetic_deduplicated_records.csv")
    REPORT_FILE = Path("output/synthetic_prisma_summary.csv")

else:
    raise ValueError("Dataset must be 'crossref' or 'synthetic'.")


def read_csv(path):
    """Read a required CSV file and handle missing files clearly."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    return pd.read_csv(path).fillna("")


def generate_prisma_report():
    """Generate a report for the completed deduplication workflow."""

    results = read_csv(RESULTS_FILE)
    verification = read_csv(QUEUE_FILE)

    if "duplicate_status" not in results.columns:
        raise ValueError(
            "Deduplication results must contain duplicate_status."
        )

    if "record_id" not in results.columns:
        raise ValueError(
            "Deduplication results must contain record_id."
        )

    if not {"record_id", "verification_status"}.issubset(
        verification.columns
    ):
        raise ValueError(
            "Verification queue must contain record_id "
            "and verification_status."
        )

    # Input records and algorithmically flagged candidates.
    records_identified = len(results)

    duplicate_candidates = int(
        (
            results["duplicate_status"].astype(str).str.strip()
            == "Duplicate"
        ).sum()
    )

    potential_duplicates = int(
        (
            results["duplicate_status"].astype(str).str.strip()
            == "Potential Duplicate"
        ).sum()
    )

    # Count each reviewed candidate only once by record ID.
    verification["record_id"] = verification["record_id"].astype(str)
    verification["verification_status"] = (
        verification["verification_status"].astype(str).str.strip()
    )

    verification = verification.drop_duplicates(
        subset="record_id",
        keep="last",
    )

    confirmed_ids = set(
        verification.loc[
            verification["verification_status"] == "Confirmed Duplicate",
            "record_id",
        ]
    )

    not_duplicate_ids = set(
        verification.loc[
            verification["verification_status"] == "Not Duplicate",
            "record_id",
        ]
    )

    pending_statuses = {"", "Pending", "nan", "None"}

    pending_reviews = int(
        verification["verification_status"]
        .isin(pending_statuses)
        .sum()
    )

    confirmed_duplicates = len(confirmed_ids)
    not_duplicates = len(not_duplicate_ids)

    # Read the actual retained dataset.
    retained = read_csv(RETAINED_FILE)

    if "record_id" not in retained.columns:
        raise ValueError(
            "Retained dataset must contain record_id."
        )

    records_remaining = len(retained)

    # Consistency checks: do not silently report incorrect counts.
    if records_remaining != records_identified - confirmed_duplicates:
        raise ValueError(
            "The retained dataset count does not match the verification "
            "decisions. Run 'python src/build_retained_dataset.py' "
            "and check the saved verification queue."
        )

    if confirmed_ids.intersection(set(retained["record_id"].astype(str))):
        raise ValueError(
            "A confirmed duplicate is still present in the retained dataset."
        )

    report = [
        ("Records identified in input", records_identified),
        ("Duplicate candidates detected by algorithm", duplicate_candidates),
        ("Potential duplicates detected by algorithm", potential_duplicates),
        ("Candidates requiring manual verification",
         duplicate_candidates + potential_duplicates),
        ("Candidates reviewed", confirmed_duplicates + not_duplicates),
        ("Candidates confirmed as duplicates by reviewer",
         confirmed_duplicates),
        ("Candidates marked Not Duplicate", not_duplicates),
        ("Candidates awaiting review", pending_reviews),
        ("Records removed as confirmed duplicates", confirmed_duplicates),
        ("Records remaining after deduplication", records_remaining),
    ]

    report_df = pd.DataFrame(report, columns=["metric", "count"])

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(REPORT_FILE, index=False)

    print(f"\nDeduplication report: {DATASET}")
    print("=" * 72)
    print(report_df.to_string(index=False))
    print(f"\nReport saved to: {REPORT_FILE}")

    if pending_reviews:
        print(
            f"\nWarning: {pending_reviews} duplicate candidates "
            "still require review."
        )
    else:
        print("\nAll flagged duplicate candidates have been reviewed.")

    print(
        "\nThis report covers record identification and deduplication only. "
        "Title/abstract screening and full-text eligibility are not included."
    )

    return report_df


if __name__ == "__main__":
    generate_prisma_report()
