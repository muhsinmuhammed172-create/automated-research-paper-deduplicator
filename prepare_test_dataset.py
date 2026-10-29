
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

df = pd.read_csv(INPUT_FILE).fillna("")

test_df = df[df["filename"].isin(TEST_FILES)].copy()

# Keep only the current test files.
test_df = test_df.drop_duplicates(subset=["filename"], keep="last")

missing = TEST_FILES - set(test_df["filename"])

if missing:
    print("Missing files:", sorted(missing))
    raise SystemExit("Dataset was not created. Check the filenames.")

test_df.to_csv(OUTPUT_FILE, index=False)

print("Plant disease test dataset created successfully.")
print(f"Total records: {len(test_df)}")
print(f"Saved to: {OUTPUT_FILE}")
print("\nFiles included:")
print(test_df["filename"].to_string(index=False))
