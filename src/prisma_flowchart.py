
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


SUMMARY_FILE = Path("output/crossref_prisma_summary.csv")
RETAINED_FILE = Path("output/crossref_deduplicated_records.csv")

PNG_FILE = Path("output/crossref_prisma_flowchart.png")
PDF_FILE = Path("output/crossref_prisma_flowchart.pdf")


def get_count(summary, metric):
    """Return a count for a metric in the saved summary."""
    rows = summary.loc[summary["metric"] == metric, "count"]

    if rows.empty:
        raise ValueError(f"Metric not found in PRISMA summary: {metric}")

    return int(rows.iloc[0])


def add_box(ax, x, y, width, height, title, details):
    """Draw one flowchart box."""
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        linewidth=1.5,
        edgecolor="black",
        facecolor="white",
    )
    ax.add_patch(patch)

    ax.text(
        x + width / 2,
        y + height * 0.68,
        title,
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        wrap=True,
    )

    ax.text(
        x + width / 2,
        y + height * 0.35,
        details,
        ha="center",
        va="center",
        fontsize=9,
        wrap=True,
    )


def add_arrow(ax, start, end):
    """Draw an arrow between two points."""
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle="->", linewidth=1.5),
    )


def create_prisma_flowchart():
    """Create a flowchart for the completed deduplication stages."""

    if not SUMMARY_FILE.exists():
        raise FileNotFoundError(
            f"PRISMA summary not found: {SUMMARY_FILE}\n"
            "Run 'python src/prisma_reporting.py crossref' first."
        )

    if not RETAINED_FILE.exists():
        raise FileNotFoundError(
            f"Retained dataset not found: {RETAINED_FILE}"
        )

    summary = pd.read_csv(SUMMARY_FILE).fillna("")
    retained = pd.read_csv(RETAINED_FILE).fillna("")

    identified = get_count(summary, "Records identified in input")
    exact_candidates = get_count(
        summary, "Duplicate candidates detected by algorithm"
    )
    potential_candidates = get_count(
        summary, "Potential duplicates detected by algorithm"
    )
    reviewed = get_count(summary, "Candidates reviewed")
    confirmed = get_count(
        summary, "Candidates confirmed as duplicates by reviewer"
    )
    not_duplicates = get_count(
        summary, "Candidates marked Not Duplicate"
    )
    pending = get_count(summary, "Candidates awaiting review")
    remaining = get_count(
        summary, "Records remaining after deduplication"
    )

    if len(retained) != remaining:
        raise ValueError(
            f"Retained dataset has {len(retained)} rows, but the "
            f"summary reports {remaining}. Regenerate the retained "
            "dataset and summary before creating the flowchart."
        )

    if confirmed + not_duplicates + pending != reviewed + pending:
        # This should not normally occur; the detailed metrics are
        # printed below so any inconsistent verification counts are visible.
        print("Warning: verification counts may need checking.")

    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 12)
    ax.axis("off")

    ax.text(
        6,
        11.5,
        "PRISMA-Style Research Paper Deduplication Flow",
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
    )

    # Main vertical flow.
    box_x = 3.0
    box_width = 6.0
    box_height = 1.05

    add_box(
        ax,
        box_x,
        9.7,
        box_width,
        box_height,
        "Records identified",
        f"Research records collected: {identified}",
    )

    add_arrow(ax, (6, 9.7), (6, 9.1))

    add_box(
        ax,
        box_x,
        7.95,
        box_width,
        box_height,
        "Automatic duplicate detection",
        f"Duplicate candidates: {exact_candidates}\n"
        f"Potential duplicate candidates: {potential_candidates}",
    )

    add_arrow(ax, (6, 7.95), (6, 7.35))

    add_box(
        ax,
        box_x,
        6.2,
        box_width,
        box_height,
        "Manual verification of flagged candidates",
        f"Reviewed: {reviewed} | Confirmed duplicates: {confirmed}\n"
        f"Not duplicates: {not_duplicates} | Pending: {pending}",
    )

    add_arrow(ax, (6, 6.2), (6, 5.6))

    add_box(
        ax,
        box_x,
        4.45,
        box_width,
        box_height,
        "Confirmed duplicate records removed",
        f"Records removed: {confirmed}",
    )

    add_arrow(ax, (6, 4.45), (6, 3.85))

    add_box(
        ax,
        box_x,
        2.7,
        box_width,
        box_height,
        "Deduplicated dataset",
        f"Records retained for subsequent research: {remaining}",
    )

    # Side note describing the reviewed-candidate counts.
    add_box(
        ax,
        0.2,
        6.15,
        2.3,
        1.3,
        "Review outcome",
        f"{confirmed} confirmed duplicate(s)\n"
        f"{not_duplicates} distinct candidate(s)",
    )

    add_arrow(ax, (2.5, 6.8), (3.0, 6.8))

    ax.text(
        6,
        1.65,
        "Scope: record identification, duplicate detection, "
        "manual verification, and deduplication only.",
        ha="center",
        va="center",
        fontsize=9,
        style="italic",
        wrap=True,
    )

    ax.text(
        6,
        1.15,
        "Title/abstract screening and full-text eligibility "
        "are outside this flowchart.",
        ha="center",
        va="center",
        fontsize=9,
    )

    PNG_FILE.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(PNG_FILE, dpi=300, bbox_inches="tight")
    fig.savefig(PDF_FILE, bbox_inches="tight")
    plt.close(fig)

    print("\nDeduplication flowchart generated successfully!")
    print(f"PNG saved to: {PNG_FILE}")
    print(f"PDF saved to: {PDF_FILE}")
    print(f"Records identified: {identified}")
    print(f"Confirmed duplicates removed: {confirmed}")
    print(f"Records retained: {remaining}")
    print(f"Candidates awaiting review: {pending}")


if __name__ == "__main__":
    create_prisma_flowchart()
