from pathlib import Path
import pandas as pd

INPUT_FILE = Path("output/pdf_enriched_metadata.csv")
OUTPUT_FILE = Path("output/pdf_metadata_review.csv")


def check_metadata(input_file: Path = INPUT_FILE, output_file: Path = OUTPUT_FILE):
    input_file = Path(input_file)
    output_file = Path(output_file)

    if not input_file.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {input_file}"
        )

    df = pd.read_csv(input_file).fillna("")
    review_reasons = []

    for _, row in df.iterrows():
        reasons = []

        title = str(row.get("title", "")).strip()
        doi = str(row.get("doi", "")).strip()
        author = str(row.get("author", "")).strip()
        year = str(row.get("year", "")).strip()

        title_lower = title.lower()

        # Missing metadata
        if not title:
            reasons.append("Missing title")

        if not author:
            reasons.append("Missing author")

        # Titles that resemble PDF properties or journal headings
        suspicious_phrases = [
            "microsoft word",
            "doi:",
            "international journal of",
            "genetics and molecular research",
        ]

        if any(phrase in title_lower for phrase in suspicious_phrases):
            reasons.append("Title may be metadata or journal name")

        # Incomplete-looking titles
        if title.endswith((" by", " of", " for", " and", ":")):
            reasons.append("Title may be incomplete")

        # A publication year outside a reasonable range
        if year and (
            not year.isdigit()
            or int(year) < 1900
            or int(year) > 2026
        ):
            reasons.append("Check publication year")

        # Basic DOI format check
        if doi and not doi.lower().startswith("10."):
            reasons.append("Check DOI format")

        review_reasons.append("; ".join(reasons))

    df["metadata_review_required"] = [
        "Yes" if reason else "No"
        for reason in review_reasons
    ]
    df["metadata_review_reason"] = review_reasons

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)

    flagged = (df["metadata_review_required"] == "Yes").sum()

    print(f"Total PDF records: {len(df)}")
    print(f"Records flagged for review: {flagged}")
    print(f"Review file saved to: {output_file}")

    if flagged:
        print("\nRecords requiring review:")
        print(
            df.loc[
                df["metadata_review_required"] == "Yes",
                ["filename", "title", "year", "metadata_review_reason"],
            ].to_string(index=False)
        )
    return df


if __name__ == "__main__":
    check_metadata()
