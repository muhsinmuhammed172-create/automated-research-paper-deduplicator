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
        # Fallback search if phrased slightly differently
        for m in summary["metric"]:
            if metric.lower() in str(m).lower():
                return int(summary.loc[summary["metric"] == m, "count"].iloc[0])
        return 0
    return int(rows.iloc[0])


def add_box(ax, x, y, width, height, title, details, facecolor="white", edgecolor="#1e293b", text_color="#0f172a"):
    """Draw one clean PRISMA flowchart box with rounded corners."""
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        linewidth=1.5,
        edgecolor=edgecolor,
        facecolor=facecolor,
    )
    ax.add_patch(patch)

    ax.text(
        x + width / 2,
        y + height * 0.68,
        title,
        ha="center",
        va="center",
        fontsize=10.5,
        fontweight="bold",
        color=text_color,
        wrap=True,
    )

    ax.text(
        x + width / 2,
        y + height * 0.35,
        details,
        ha="center",
        va="center",
        fontsize=8.5,
        color="#334155",
        wrap=True,
    )


def add_arrow(ax, start, end, color="#1e293b"):
    """Draw an arrow between two points."""
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle="->", linewidth=1.5, color=color),
    )


def create_prisma_flowchart(
    summary_file: Path = None,
    retained_file: Path = None,
    png_file: Path = None,
    pdf_file: Path = None,
    title_text: str = "PRISMA 2020 Flow Diagram – Deduplication & Identification"
):
    """Create a flowchart for the completed deduplication stages."""
    summary_file = Path(summary_file) if summary_file else SUMMARY_FILE
    retained_file = Path(retained_file) if retained_file else RETAINED_FILE
    png_file = Path(png_file) if png_file else PNG_FILE
    pdf_file = Path(pdf_file) if pdf_file else PDF_FILE

    if not summary_file.exists():
        raise FileNotFoundError(
            f"PRISMA summary not found: {summary_file}"
        )

    summary = pd.read_csv(summary_file).fillna("")

    identified = get_count(summary, "Records identified in input")
    if identified == 0:
        identified = get_count(summary, "Records identified")

    exact_candidates = get_count(summary, "Duplicate candidates detected by algorithm")
    potential_candidates = get_count(summary, "Potential duplicates detected by algorithm")
    file_duplicates = get_count(summary, "Exact file duplicates identified")
    
    reviewed = get_count(summary, "Candidates reviewed")
    confirmed = get_count(summary, "Candidates confirmed as duplicates by reviewer")
    if confirmed == 0:
        confirmed = get_count(summary, "Records removed as confirmed duplicates")
    
    not_duplicates = get_count(summary, "Candidates marked Not Duplicate")
    pending = get_count(summary, "Candidates awaiting review")
    remaining = get_count(summary, "Records remaining after deduplication")
    if remaining == 0 and retained_file.exists():
        retained_df = pd.read_csv(retained_file).fillna("")
        remaining = len(retained_df)

    fig, ax = plt.subplots(figsize=(11, 10), facecolor="#ffffff")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 12)
    ax.axis("off")

    # Header Title
    ax.text(
        6,
        11.5,
        title_text,
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="#0f172a"
    )

    # Stage Indicators
    ax.text(0.5, 9.8, "IDENTIFICATION", fontsize=10, fontweight="bold", color="#2563eb", rotation=90)
    ax.text(0.5, 6.5, "DEDUPLICATION", fontsize=10, fontweight="bold", color="#059669", rotation=90)
    ax.text(0.5, 2.8, "RETAINED", fontsize=10, fontweight="bold", color="#4338ca", rotation=90)

    # Box dimensions
    box_x = 2.4
    box_width = 5.2
    box_height = 1.05

    # 1. Records Identified
    add_box(
        ax,
        box_x,
        9.5,
        box_width,
        box_height,
        "Records identified from sources",
        f"Research paper records collected: {identified}",
        facecolor="#f0f9ff",
        edgecolor="#0284c7"
    )

    add_arrow(ax, (5.0, 9.5), (5.0, 8.8))

    # 2. Automated Duplicate Detection
    detection_text = f"Candidates flagged: {exact_candidates + potential_candidates}"
    if file_duplicates > 0:
        detection_text += f" (incl. {file_duplicates} SHA-256 file duplicate)"
    else:
        detection_text += f"\nExact duplicates: {exact_candidates} | Fuzzy potential: {potential_candidates}"

    add_box(
        ax,
        box_x,
        7.75,
        box_width,
        box_height,
        "Automated duplicate detection",
        detection_text,
        facecolor="#f8fafc",
        edgecolor="#475569"
    )

    add_arrow(ax, (5.0, 7.75), (5.0, 7.05))

    # 3. Manual Verification
    add_box(
        ax,
        box_x,
        6.0,
        box_width,
        box_height,
        "Human verification of flagged candidates",
        f"Reviewed: {reviewed} | Confirmed duplicates: {confirmed}\n"
        f"Distinct (retained): {not_duplicates} | Pending: {pending}",
        facecolor="#f0fdf4",
        edgecolor="#16a34a"
    )

    # Arrow to removed side box (Right side)
    add_arrow(ax, (7.6, 6.5), (8.4, 6.5), color="#dc2626")

    # Side Box: Confirmed Duplicates Removed
    add_box(
        ax,
        8.4,
        5.85,
        3.2,
        1.3,
        "Duplicate records removed",
        f"Confirmed duplicates: {confirmed}\n"
        f"(No double-counting between\nfile & paper levels)",
        facecolor="#fef2f2",
        edgecolor="#dc2626",
        text_color="#991b1b"
    )

    add_arrow(ax, (5.0, 6.0), (5.0, 4.8))

    # 4. Final Retained Corpus
    add_box(
        ax,
        box_x,
        3.75,
        box_width,
        box_height,
        "Deduplicated dataset (Retained for SLR)",
        f"Unique research papers retained: {remaining}",
        facecolor="#eef2ff",
        edgecolor="#4f46e5",
        text_color="#312e81"
    )

    # Verification Note
    note_text = (
        f"Validation: Initial ({identified}) − Confirmed duplicates ({confirmed}) = "
        f"Retained ({remaining}).\n"
        "Pending candidates are not removed. Title/abstract screening and full-text eligibility are separate SLR stages."
    )
    ax.text(
        6,
        2.2,
        note_text,
        ha="center",
        va="center",
        fontsize=8.5,
        style="italic",
        color="#475569",
        wrap=True,
    )

    png_file.parent.mkdir(parents=True, exist_ok=True)
    pdf_file.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(png_file, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_file, bbox_inches="tight")
    plt.close(fig)

    print(f"\nDeduplication flowchart generated: {png_file}")
    return png_file, pdf_file


if __name__ == "__main__":
    create_prisma_flowchart()
