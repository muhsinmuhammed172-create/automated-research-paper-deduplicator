"""PRISMA-style deduplication statistics.

Usage
-----
python src/prisma_reporting.py crossref
python src/prisma_reporting.py synthetic
"""

import sys
from pathlib import Path

import pandas as pd


def _resolve_paths(dataset: str) -> tuple[Path, Path, Path, Path]:
    dataset = dataset.lower()

    if dataset == "crossref":
        return (
            Path("output/crossref_deduplication_results.csv"),
            Path("output/crossref_verification_queue.csv"),
            Path("output/crossref_deduplicated_records.csv"),
            Path("output/crossref_prisma_summary.csv"),
        )
    elif dataset == "synthetic":
        return (
            Path("output/synthetic_deduplication_results.csv"),
            Path("output/synthetic_verification_queue.csv"),
            Path("output/synthetic_deduplicated_records.csv"),
            Path("output/synthetic_prisma_summary.csv"),
        )
    elif dataset == "plant_test":
        return (
            Path("output/plant_test_deduplication_results.csv"),
            Path("output/plant_test_verification_queue.csv"),
            Path("output/plant_test_deduplicated_records.csv"),
            Path("output/plant_test_prisma_summary.csv"),
        )
    else:
        raise ValueError(f"Unknown dataset '{dataset}'. Use 'crossref', 'synthetic', or 'plant_test'.")


def _read_csv(path: Path) -> pd.DataFrame:
    """Read a required CSV file and surface missing-file errors clearly."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path).fillna("")


def generate_prisma_report(
    dataset: str = "synthetic",
    results_file: Path = None,
    queue_file: Path = None,
    retained_file: Path = None,
    report_file: Path = None,
    file_duplicates_count: int = 0
) -> pd.DataFrame:
    """Generate a report for the completed deduplication workflow."""
    if not (results_file and queue_file and retained_file and report_file):
        r_f, q_f, ret_f, rep_f = _resolve_paths(dataset)
        results_file = results_file or r_f
        queue_file = queue_file or q_f
        retained_file = retained_file or ret_f
        report_file = report_file or rep_f

    results = _read_csv(Path(results_file))
    verification = _read_csv(Path(queue_file))

    if "duplicate_status" not in results.columns:
        raise ValueError("Deduplication results must contain duplicate_status.")
    if "record_id" not in results.columns:
        raise ValueError("Deduplication results must contain record_id.")
    if not {"record_id", "verification_status"}.issubset(verification.columns):
        raise ValueError(
            "Verification queue must contain record_id and verification_status."
        )

    # Input records and algorithmically flagged candidates.
    records_identified = len(results)

    duplicate_candidates = int(
        (results["duplicate_status"].astype(str).str.strip() == "Duplicate").sum()
    )
    potential_duplicates = int(
        (results["duplicate_status"].astype(str).str.strip() == "Potential Duplicate").sum()
    )

    # Count each reviewed candidate only once by record ID.
    verification["record_id"] = verification["record_id"].astype(str)
    verification["verification_status"] = (
        verification["verification_status"].astype(str).str.strip()
    )
    verification = verification.drop_duplicates(subset="record_id", keep="last")

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
        verification["verification_status"].isin(pending_statuses).sum()
    )

    confirmed_duplicates = len(confirmed_ids)
    not_duplicates = len(not_duplicate_ids)

    # Read the actual retained dataset.
    retained = _read_csv(Path(retained_file))
    if "record_id" not in retained.columns:
        raise ValueError("Retained dataset must contain record_id.")

    records_remaining = len(retained)

    # Consistency checks.
    if records_remaining != records_identified - confirmed_duplicates:
        raise ValueError(
            f"The retained dataset count ({records_remaining}) does not match the verification "
            f"decisions ({records_identified} - {confirmed_duplicates} = {records_identified - confirmed_duplicates})."
        )

    if confirmed_ids.intersection(set(retained["record_id"].astype(str))):
        raise ValueError(
            "A confirmed duplicate is still present in the retained dataset."
        )

    report = [
        ("Records identified in input", records_identified),
        ("Exact file duplicates identified", file_duplicates_count),
        ("Duplicate candidates detected by algorithm", duplicate_candidates),
        ("Potential duplicates detected by algorithm", potential_duplicates),
        ("Candidates requiring manual verification",
         duplicate_candidates + potential_duplicates),
        ("Candidates reviewed", confirmed_duplicates + not_duplicates),
        ("Candidates confirmed as duplicates by reviewer", confirmed_duplicates),
        ("Candidates marked Not Duplicate", not_duplicates),
        ("Candidates awaiting review", pending_reviews),
        ("Records removed as confirmed duplicates", confirmed_duplicates),
        ("Records remaining after deduplication", records_remaining),
    ]

    report_df = pd.DataFrame(report, columns=["metric", "count"])

    Path(report_file).parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(Path(report_file), index=False)

    print(f"\nDeduplication report: {dataset}")
    print("=" * 72)
    print(report_df.to_string(index=False))
    print(f"\nReport saved to: {report_file}")

    if pending_reviews:
        print(
            f"\nWarning: {pending_reviews} duplicate candidates "
            "still require review."
        )
    else:
        print("\nAll flagged duplicate candidates have been reviewed.")

    return report_df


if __name__ == "__main__":
    _dataset = sys.argv[1].lower() if len(sys.argv) > 1 else "synthetic"
    generate_prisma_report(_dataset)
