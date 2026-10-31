
"""Build the final retained dataset after human verification.

Removes only the candidate records that the reviewer confirmed as
duplicates.  Blocks finalisation if any flagged candidate is still
pending, so the PRISMA counts are always complete and accurate.

Usage
-----
python src/build_retained_dataset.py crossref
python src/build_retained_dataset.py synthetic
python src/build_retained_dataset.py plant_test
"""

import sys
from pathlib import Path

import pandas as pd


def _resolve_paths(dataset: str) -> tuple[Path, Path, Path]:
    dataset = dataset.lower()

    if dataset == "crossref":
        return (
            Path("output/crossref_deduplication_results.csv"),
            Path("output/crossref_verification_queue.csv"),
            Path("output/crossref_deduplicated_records.csv"),
        )
    elif dataset == "synthetic":
        return (
            Path("output/synthetic_deduplication_results.csv"),
            Path("output/synthetic_verification_queue.csv"),
            Path("output/synthetic_deduplicated_records.csv"),
        )
    elif dataset == "plant_test":
        return (
            Path("output/plant_test_deduplication_results.csv"),
            Path("output/plant_test_verification_queue.csv"),
            Path("output/plant_test_deduplicated_records.csv"),
        )
    else:
        raise ValueError(
            f"Unknown dataset '{dataset}'. "
            "Use 'crossref', 'synthetic', or 'plant_test'."
        )


def build_retained_dataset(
    dataset: str = "synthetic",
    results_file: Path = None,
    queue_file: Path = None,
    output_file: Path = None
) -> pd.DataFrame:
    if not (results_file and queue_file and output_file):
        r_f, q_f, out_f = _resolve_paths(dataset)
        results_file = results_file or r_f
        queue_file = queue_file or q_f
        output_file = output_file or out_f

    results_file = Path(results_file)
    queue_file = Path(queue_file)
    output_file = Path(output_file)

    if not results_file.exists():
        raise FileNotFoundError(f"Dataset not found: {results_file}")
    if not queue_file.exists():
        raise FileNotFoundError(f"Verification queue not found: {queue_file}")

    papers = pd.read_csv(results_file).fillna("")
    queue = pd.read_csv(queue_file).fillna("")

    if "record_id" not in papers.columns:
        raise ValueError("record_id is missing from the results dataset.")
    if "record_id" not in queue.columns:
        raise ValueError("record_id is missing from the verification queue.")
    if "verification_status" not in queue.columns:
        raise ValueError("verification_status is missing from the queue.")

    papers["record_id"] = papers["record_id"].astype(str)
    queue["record_id"] = queue["record_id"].astype(str)

    # Block finalisation while any flagged candidate remains unreviewed.
    pending = queue[
        ~queue["verification_status"].isin(
            ["Confirmed Duplicate", "Not Duplicate"]
        )
    ]

    if not pending.empty:
        raise ValueError(
            f"{len(pending)} candidate(s) are still pending review. "
            "Complete verification before building the final dataset.\n"
            f"  Pending record IDs: {pending['record_id'].tolist()}"
        )

    # Record IDs manually confirmed as duplicates.
    duplicate_ids = set(
        queue.loc[
            queue["verification_status"] == "Confirmed Duplicate",
            "record_id",
        ]
    )

    # Remove only the candidate records confirmed as duplicates.
    retained = papers[~papers["record_id"].isin(duplicate_ids)].copy()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    retained.to_csv(output_file, index=False)

    print("\n" + "=" * 55)
    print("DEDUPLICATION SUMMARY")
    print("=" * 55)
    print("Dataset:", dataset)
    print("Original records:", len(papers))
    print("Confirmed duplicate records removed:", len(duplicate_ids))
    print("Records retained:", len(retained))
    print("Output file:", output_file)
    return retained


if __name__ == "__main__":
    _dataset = sys.argv[1].lower() if len(sys.argv) > 1 else "synthetic"
    build_retained_dataset(_dataset)
