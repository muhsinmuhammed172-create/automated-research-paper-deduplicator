# Automated Research-Paper Deduplication and Verification System

An MCA project that automates the identification and removal of duplicate
research papers in PRISMA-based Systematic Literature Reviews (SLRs).

---

## Project Overview

When conducting an SLR, researchers collect hundreds or thousands of records
from databases such as IEEE Xplore, Google Scholar, Scopus, Springer,
ScienceDirect, and Crossref. The same paper often appears multiple times with
minor metadata differences. This system automates duplicate detection and
provides a human-in-the-loop verification step so that no record is removed
without a reviewer decision.

---

## Datasets

| Dataset | Purpose |
|---|---|
| **P1–P7 PDFs** (`data/pdfs/`) | Test PDF ingestion, SHA-256 hashing, Crossref enrichment, and file-level deduplication |
| **Crossref 500** (`data/sample/crossref_papers.csv`) | Test paper-level deduplication algorithms at scale |

---

## Installation

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. Install all dependencies
pip install -r requirements.txt
```

**Dependencies** (see `requirements.txt`):
`pandas`, `numpy`, `rapidfuzz`, `pymupdf`, `requests`, `matplotlib`,
`python-dateutil`, `six`, `tzdata`

---

## Web Application (Frontend + Backend)

You can launch the complete web application with a modern React dashboard:

### Option 1: Run Full Web App (Single Command)

```bash
# Start the FastAPI server (serves both API and the built React frontend)
python server.py
```
Open **http://127.0.0.1:8000** in your browser to view the **RESEARCH DEDUPLICATOR** dashboard.

### Option 2: Run in Development Mode (Vite HMR + FastAPI)

```bash
# Terminal 1 - Backend API:
python server.py

# Terminal 2 - Frontend Development Server:
cd frontend
npm run dev
```
Open **http://localhost:5173** in your browser.

---

## Quick Start — End-to-End Pipeline

A single script `run_pipeline.py` orchestrates all stages in the correct order.

### PDF Workflow (P1–P7)

```bash
# Place your PDF files in data/pdfs/ then run:
python run_pipeline.py --mode pdf
```

This runs:
1. PDF ingestion (text extraction, SHA-256, DOI extraction)
2. Crossref metadata enrichment (with title-based fallback for missing DOIs)
3. Metadata quality check
4. File-level duplicate report
5. Plant-test dataset preparation
6. Paper-level deduplication
7. Interactive human verification
8. Retained dataset construction
9. PRISMA statistics report

### Crossref 500 Experiment

```bash
python run_pipeline.py --mode crossref
```

### Skip Verification (decisions already saved)

```bash
python run_pipeline.py --mode crossref --skip-verify
```

### Regenerate PRISMA Report Only

```bash
python run_pipeline.py --mode report --dataset crossref
```

---

## Running Individual Steps

If you need to run steps independently:

```bash
# 1. Ingest PDFs
python src/pdf_ingestion.py

# 2. Enrich metadata via Crossref
python src/enrich_pdf_metadata.py

# 3. Check metadata quality
python src/metadata_quality_check.py

# 4. File-level duplicate report
python src/file_deduplication.py

# 5. Prepare plant-test dataset
python prepare_test_dataset.py

# 6. Paper-level deduplication (choose dataset)
python main.py --input crossref
python main.py --input plant_test
python main.py --input synthetic

# 7. Interactive review
python review.py crossref
python review.py plant_test
python review.py synthetic

# 8. Build retained dataset
python src/build_retained_dataset.py crossref

# 9. PRISMA report
python src/prisma_reporting.py crossref

# 10. PRISMA flowchart
python src/prisma_flowchart.py

# 11. Download fresh Crossref data
python fetch_crossref.py
```

---

## Project Structure

```
automated-research-paper-deduplicator/
├── run_pipeline.py              ← End-to-end pipeline script
├── main.py                      ← Paper-level dedup entry point
├── fetch_crossref.py            ← Download Crossref 500 dataset
├── prepare_test_dataset.py      ← Filter P1–P7 from enriched metadata
├── review.py                    ← Interactive verification CLI
├── test_dedup.py                ← Ad-hoc dedup test
├── test_deduplication.py        ← Regression tests (12 labelled cases)
├── test_record_ids.py           ← Unit test: record ID uniqueness
├── requirements.txt             ← Python dependencies
│
├── src/
│   ├── utils.py                 ← Shared: SHA-256, DOI normalisation, year extraction
│   ├── pdf_ingestion.py         ← SHA-256 hash + text extraction + metadata
│   ├── enrich_pdf_metadata.py   ← Crossref DOI lookup + title-based fallback
│   ├── metadata_quality_check.py← Flag suspicious/incomplete metadata
│   ├── file_deduplication.py    ← File-level hash-based duplicate detection
│   ├── preprocessing.py         ← Normalize fields, assign UUID record IDs
│   ├── similarity.py            ← token_sort_ratio title similarity
│   ├── paper_deduplication.py   ← Core 3-rule matching (DOI, title+author, fuzzy)
│   ├── verification.py          ← Queue creation + interactive CLI review
│   ├── build_retained_dataset.py← Remove confirmed duplicates
│   ├── prisma_reporting.py      ← Stats + consistency checks
│   ├── prisma_flowchart.py      ← Matplotlib PRISMA diagram
│   ├── screening.py             ← Title/abstract screening queue (CLI)
│   └── eligibility.py           ← Full-text eligibility queue (CLI)
│
├── data/
│   ├── pdfs/                    ← P1.pdf, P1_copy.pdf, P2–P7.pdf
│   ├── sample/                  ← crossref_papers.csv, test CSVs
│   └── processed/               ← Persistent record-ID files
│
└── output/                      ← Generated CSVs and PRISMA figures
```

---

## Deduplication Rules

Paper-level matching applies three rules in priority order:

| Rule | Condition | Classification |
|---|---|---|
| 1 | Matching non-empty normalised DOI | Duplicate |
| 2a | Exact normalised title + matching authors (both non-empty) | Duplicate |
| 2b | Exact normalised title when both records have no author | Duplicate |
| 3 | Token-sort fuzzy title similarity ≥ 85 | Potential Duplicate |

All flagged candidates go to the human verification queue. Only
**Confirmed Duplicate** records are removed.

---

## Key Design Decisions

- **SHA-256 hashing** identifies identical PDF files (e.g. P1.pdf = P1_copy.pdf).
- **Persistent reviewer decisions** are preserved by record ID across re-runs.
- **No automatic removal** — every duplicate candidate requires a human decision.
- **Crossref title-based fallback** searches for papers that have no extractable DOI.
- **Unicode NFKC normalisation** converts PDF ligature characters (ﬁ, ﬂ, …) in DOIs before Crossref lookup.
- **PRISMA scope** is correctly limited to the Identification + Deduplication stage; screening and eligibility stages are separate.

---

## Expected Results

### Dataset A — P1–P7 PDFs

- 8 files ingested → 7 unique files (P1_copy.pdf is an exact copy of P1.pdf)
- P1_copy detected as `Duplicate` via DOI match
- P3's incomplete extracted title corrected via Crossref enrichment

### Dataset B — Crossref 500

| Metric | Count |
|---|---|
| Records identified | 500 |
| Duplicate candidates | 2 |
| Potential duplicate candidates | 3 |
| Total candidates reviewed | 5 |
| Confirmed duplicates | 4 |
| Not duplicate (correction notice retained) | 1 |
| Records removed | 4 |
| **Final retained records** | **496** |

---

## Output Files

| File | Description |
|---|---|
| `output/pdf_extracted_metadata.csv` | Raw extracted PDF metadata + SHA-256 hashes |
| `output/pdf_enriched_metadata.csv` | Crossref-enriched metadata |
| `output/pdf_metadata_enrichment_issues.csv` | DOI lookup failures and title mismatches |
| `output/pdf_metadata_review.csv` | Flagged records needing manual review |
| `output/crossref_deduplication_results.csv` | Dedup results for Crossref 500 |
| `output/crossref_verification_queue.csv` | Verification queue with reviewer decisions |
| `output/crossref_deduplicated_records.csv` | 496 retained records |
| `output/crossref_prisma_summary.csv` | PRISMA statistics |
| `output/crossref_prisma_flowchart.png` | PRISMA-style deduplication flowchart |
| `output/crossref_prisma_flowchart.pdf` | Same flowchart in PDF format |

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.11+ | Main language |
| Pandas | Data processing |
| PyMuPDF (fitz) | PDF text extraction |
| hashlib | SHA-256 file hashing |
| RapidFuzz | Token-sort title similarity |
| Requests | Crossref API communication |
| Matplotlib | PRISMA flowchart generation |
| Crossref REST API | Bibliographic metadata enrichment |

---

## Academic Context

This system implements the **Identification and Deduplication** stage
of the PRISMA 2020 systematic review framework. It does **not** replace
the Title/Abstract Screening or Full-Text Eligibility stages, which
require domain-expert judgment and are supported by the CLI tools in
`src/screening.py` and `src/eligibility.py`.
