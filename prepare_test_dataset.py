
"""Filter enriched PDF metadata to produce the P1–P7 test dataset.

Usage
-----
python prepare_test_dataset.py
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path("output/pdf_enriched_metadata.csv")
OUTPUT_FILE = Path("output/plant_disease_test_metadata.csv")

TEST_FILES = {
    "P1.pdf",
    "P1_copy.pdf",
    "P2.pdf",
    "P3.pdf",
    "P4.pdf",
    "P5.pdf",
    "P6.pdf",
    "P7.pdf",
}


def prepare_dataset() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Enriched metadata not found: {INPUT_FILE}\n"
            "Run 'python src/enrich_pdf_metadata.py' first."
        )

    df = pd.read_csv(INPUT_FILE).fillna("")

    test_df = df[df["filename"].isin(TEST_FILES)].copy()

    # Keep only the most recent record for each filename.
    test_df = test_df.drop_duplicates(subset=["filename"], keep="last")

    missing = TEST_FILES - set(test_df["filename"])
    if missing:
        print("Missing files:", sorted(missing))
        raise SystemExit("Dataset was not created. Check the filenames.")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    test_df.to_csv(OUTPUT_FILE, index=False)

    print("Plant disease test dataset created successfully.")
    print(f"Total records: {len(test_df)}")
    print(f"Saved to: {OUTPUT_FILE}")
    print("\nFiles included:")
    print(test_df["filename"].to_string(index=False))


if __name__ == "__main__":
    prepare_dataset()
