
"""End-to-end deduplication pipeline.

Runs every stage in the correct order for the chosen dataset so that
users do not need to remember or manually execute six separate commands.

Usage
-----
# Full PDF workflow (ingest → enrich → quality-check → dedup → report)
python run_pipeline.py --mode pdf

# Crossref 500-record metadata workflow (dedup → report → flowchart)
python run_pipeline.py --mode crossref

# Plant-test paper-level dedup (uses already-enriched PDF metadata)
python run_pipeline.py --mode plant_test

# Generate PRISMA report and flowchart from existing verified results
python run_pipeline.py --mode report --dataset crossref

Notes
-----
* Stages that require network access (PDF enrichment, Crossref download)
  will make real HTTP requests.
* The verification step is always interactive — the pipeline pauses and
  prompts you to review flagged duplicate candidates in the terminal.
  Run with --skip-verify to bypass this pause (useful for dry-runs when
  decisions are already saved from a previous session).
"""

import argparse
import sys
from pathlib import Path


def run_pdf_pipeline(skip_verify: bool = False) -> None:
    """Ingest PDFs → enrich → quality-check → deduplicate → report."""
    print("\n" + "=" * 60)
    print("STEP 1 — PDF Ingestion")
    print("=" * 60)
    from src.pdf_ingestion import ingest_pdfs
    ingest_pdfs()

    print("\n" + "=" * 60)
    print("STEP 2 — Crossref Metadata Enrichment")
    print("=" * 60)
    from src.enrich_pdf_metadata import enrich_metadata
    enrich_metadata()

    print("\n" + "=" * 60)
    print("STEP 3 — Metadata Quality Check")
    print("=" * 60)
    from src.metadata_quality_check import check_metadata
    check_metadata()

    print("\n" + "=" * 60)
    print("STEP 4 — File-Level Duplicate Report")
    print("=" * 60)
    from src.file_deduplication import report_file_duplicates
    report_file_duplicates()

    print("\n" + "=" * 60)
    print("STEP 5 — Prepare Plant-Test Dataset")
    print("=" * 60)
    from prepare_test_dataset import prepare_dataset
    prepare_dataset()

    run_paper_dedup_pipeline("plant_test", skip_verify=skip_verify)


def run_crossref_pipeline(skip_verify: bool = False) -> None:
    """Deduplicate Crossref 500-record dataset → report → flowchart."""
    run_paper_dedup_pipeline("crossref", skip_verify=skip_verify)


def run_paper_dedup_pipeline(dataset: str, skip_verify: bool = False) -> None:
    """Shared paper-level dedup pipeline for any metadata dataset."""
    import pandas as pd
    from src.preprocessing import normalize_papers
    from src.paper_deduplication import detect_paper_duplicates
    from src.verification import create_verification_queue, review_queue
    from src.build_retained_dataset import build_retained_dataset
    from src.prisma_reporting import generate_prisma_report

    input_paths = {
        "crossref": Path("data/sample/crossref_papers.csv"),
        "plant_test": Path("output/plant_disease_test_metadata.csv"),
        "synthetic": Path("data/sample/papers.csv"),
    }

    if dataset not in input_paths:
        raise ValueError(f"Unknown dataset: {dataset}")

    input_file = input_paths[dataset]

    print(f"\n{'=' * 60}")
    print(f"DEDUPLICATION — {dataset.upper()}")
    print("=" * 60)

    if not input_file.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_file}")

    papers = pd.read_csv(input_file).fillna("")
    papers = normalize_papers(papers)

    results = detect_paper_duplicates(papers)

    output_file = Path(f"output/{dataset}_deduplication_results.csv")
    queue_file = Path(f"output/{dataset}_verification_queue.csv")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_file, index=False)
    print(f"Deduplication results saved: {output_file}")

    queue = create_verification_queue(results, dataset=dataset)
    queue.to_csv(queue_file, index=False)
    print(f"Verification queue saved: {queue_file}")

    pending = (queue["verification_status"] == "Pending").sum()
    print(f"Candidates requiring review: {len(queue)}  (pending: {pending})")

    if pending and not skip_verify:
        print(f"\n{'=' * 60}")
        print("HUMAN VERIFICATION — Review flagged candidates now")
        print("=" * 60)
        review_queue(dataset)

    try:
        build_retained_dataset(dataset)
    except ValueError as exc:
        print(f"\nCannot finalise dataset yet: {exc}")
        return

    try:
        generate_prisma_report(dataset)
    except (FileNotFoundError, ValueError) as exc:
        print(f"\nCannot generate PRISMA report: {exc}")
        return

    if dataset == "crossref":
        try:
            from src.prisma_flowchart import create_prisma_flowchart
            create_prisma_flowchart()
        except (FileNotFoundError, ValueError) as exc:
            print(f"\nCannot generate flowchart: {exc}")


def run_report_pipeline(dataset: str) -> None:
    """Regenerate PRISMA report and flowchart from existing outputs."""
    from src.prisma_reporting import generate_prisma_report
    generate_prisma_report(dataset)

    if dataset == "crossref":
        from src.prisma_flowchart import create_prisma_flowchart
        create_prisma_flowchart()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="End-to-end research-paper deduplication pipeline"
    )
    parser.add_argument(
        "--mode",
        choices=["pdf", "crossref", "plant_test", "report"],
        required=True,
        help=(
            "pdf: full PDF ingestion + enrichment + dedup; "
            "crossref: metadata dedup on Crossref 500 dataset; "
            "plant_test: paper-level dedup on P1-P7 enriched data; "
            "report: regenerate PRISMA report from existing outputs"
        ),
    )
    parser.add_argument(
        "--dataset",
        choices=["crossref", "synthetic", "plant_test"],
        default="crossref",
        help="Dataset to use when --mode is 'report'",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip the interactive review step (useful when decisions are already saved)",
    )
    args = parser.parse_args()

    if args.mode == "pdf":
        run_pdf_pipeline(skip_verify=args.skip_verify)
    elif args.mode == "crossref":
        run_crossref_pipeline(skip_verify=args.skip_verify)
    elif args.mode == "plant_test":
        run_paper_dedup_pipeline("plant_test", skip_verify=args.skip_verify)
    elif args.mode == "report":
        run_report_pipeline(args.dataset)


if __name__ == "__main__":
    main()
