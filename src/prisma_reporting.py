
from pathlib import Path

import pandas as pd

RESULTS_FILE = Path("output/deduplication_results.csv")
QUEUE_FILE = Path("output/verification_queue.csv")
REPORT_FILE = Path("output/prisma_summary.csv")


def generate_prisma_report():
    # Check that both input files exist.
    if not RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"Detection results not found: {RESULTS_FILE}. "
            "Run python main.py first."
        )

    if not QUEUE_FILE.exists():
        raise FileNotFoundError(
            f"Verification queue not found: {QUEUE_FILE}. "
            "Run python main.py first."
        )

    results = pd.read_csv(RESULTS_FILE)
    queue = pd.read_csv(QUEUE_FILE).fillna("")

    # Total bibliographic records provided to this prototype.
    records_identified = len(results)

    # Count only decisions confirmed by a human reviewer.
    if "verification_status" in queue.columns:
        confirmed_duplicates = int(
            (
                queue["verification_status"]
                == "Confirmed Duplicate"
            ).sum()
        )

        rejected_candidates = int(
            (
                queue["verification_status"]
                == "Not Duplicate"
            ).sum()
        )

        pending_reviews = int(
            (
                queue["verification_status"]
                == "Pending"
            ).sum()
        )
    else:
        confirmed_duplicates = 0
        rejected_candidates = 0
        pending_reviews = len(queue)

    # Do not remove records based only on algorithm predictions.
    records_after_deduplication = max(
        0, records_identified - confirmed_duplicates
    )

    report = [
        {
            "metric": "Records identified in input",
            "count": records_identified,
        },
        {
            "metric": "Duplicate records confirmed by reviewer",
            "count": confirmed_duplicates,
        },
        {
            "metric": "Candidates rejected as duplicates",
            "count": rejected_candidates,
        },
        {
            "metric": "Candidates awaiting review",
            "count": pending_reviews,
        },
        {
            "metric": "Records remaining after confirmed removals",
            "count": records_after_deduplication,
        },
    ]

    report_df = pd.DataFrame(report)

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(REPORT_FILE, index=False)

    print("\nPRISMA-related deduplication summary")
    print("=" * 45)
    print(report_df.to_string(index=False))
    print(f"\nReport saved to: {REPORT_FILE}")

    return report_df


if __name__ == "__main__":
    generate_prisma_report()
