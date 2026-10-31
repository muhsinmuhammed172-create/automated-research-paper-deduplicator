"""FastAPI Backend Server for RESEARCH DEDUPLICATOR
Automated Research-Paper Deduplication and Verification System

Supports:
- Separate runs with isolated directories under `runs/` (Processing History)
- Pure PDF upload workflow: no hardcoded P1-P7, any number of PDFs
- Multi-step automatic pipeline execution
- Human verification with persistent decisions per run
- Dynamic PRISMA 2020 flowchart generation (PNG and PDF) per run
- Separate Benchmark Experiment for Crossref 500
"""

import json
import os
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import existing backend modules
from src.build_retained_dataset import build_retained_dataset
from src.enrich_pdf_metadata import enrich_metadata
from src.file_deduplication import find_file_duplicates
from src.metadata_quality_check import check_metadata
from src.paper_deduplication import detect_paper_duplicates
from src.pdf_ingestion import extract_pdf_metadata, ingest_pdfs
from src.preprocessing import normalize_papers
from src.prisma_flowchart import create_prisma_flowchart
from src.prisma_reporting import generate_prisma_report
from src.verification import create_verification_queue

app = FastAPI(
    title="Research Deduplicator API",
    description="Multi-run research paper deduplication system for PRISMA systematic literature reviews",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
RUNS_DIR = BASE_DIR / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)
BENCHMARK_DIR = BASE_DIR / "output"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

# Active job tracking
active_jobs = {}


def get_next_run_id() -> str:
    """Generate sequential run ID like run_001, run_002."""
    existing = [
        d.name for d in RUNS_DIR.iterdir()
        if d.is_dir() and d.name.startswith("run_")
    ]
    numbers = []
    for name in existing:
        try:
            num = int(name.split("_")[1])
            numbers.append(num)
        except (IndexError, ValueError):
            pass
    next_num = max(numbers, default=0) + 1
    return f"run_{next_num:03d}"


def get_run_dir(run_id: str) -> Path:
    r_dir = RUNS_DIR / run_id
    if not r_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return r_dir


def log_run_job(run_id: str, message: str):
    timestamp = time.strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    if run_id in active_jobs:
        active_jobs[run_id]["logs"].append(entry)
        active_jobs[run_id]["message"] = message
    print(f"[{run_id}] {entry}")


def run_pipeline_for_run(run_id: str, file_names: List[str]):
    """Execute the full deduplication pipeline for an isolated run."""
    run_dir = RUNS_DIR / run_id
    pdf_dir = run_dir / "pdfs"
    extracted_csv = run_dir / "pdf_extracted_metadata.csv"
    enriched_csv = run_dir / "pdf_enriched_metadata.csv"
    issues_csv = run_dir / "pdf_metadata_enrichment_issues.csv"
    review_csv = run_dir / "pdf_metadata_review.csv"
    file_dups_csv = run_dir / "file_duplicates.csv"
    results_csv = run_dir / "deduplication_results.csv"
    queue_csv = run_dir / "verification_queue.csv"
    retained_csv = run_dir / "deduplicated_records.csv"
    prisma_summary_csv = run_dir / "prisma_summary.csv"
    flowchart_png = run_dir / "prisma_flowchart.png"
    flowchart_pdf = run_dir / "prisma_flowchart.pdf"
    info_json = run_dir / "info.json"

    job = active_jobs.get(run_id)

    try:
        job["status"] = "running"
        job["started_at"] = time.time()
        job["progress"] = 10
        job["step"] = "PDF Ingestion"
        log_run_job(run_id, f"Saved {len(file_names)} uploaded PDF file(s). Starting PyMuPDF text & SHA-256 extraction...")

        # Step 1: PDF Ingestion
        ingest_pdfs(pdf_dir=pdf_dir, output_file=extracted_csv)
        job["progress"] = 30
        log_run_job(run_id, "PDF text, author, DOI, and SHA-256 hashes successfully extracted.")
        time.sleep(0.4)

        # Step 2: Metadata Enrichment
        job["step"] = "Crossref Metadata Enrichment"
        job["progress"] = 50
        log_run_job(run_id, "Querying Crossref REST API for bibliographic enrichment & title validation...")
        enrich_metadata(input_file=extracted_csv, output_file=enriched_csv, issues_file=issues_csv)
        check_metadata(input_file=enriched_csv, output_file=review_csv)
        job["progress"] = 65
        log_run_job(run_id, "Crossref enrichment and metadata quality inspection completed.")
        time.sleep(0.4)

        # Step 3: File-level Deduplication
        job["step"] = "File-Level Deduplication (SHA-256)"
        job["progress"] = 75
        log_run_job(run_id, "Evaluating exact binary file copies using SHA-256 digests...")
        file_dups = find_file_duplicates(metadata_csv=extracted_csv)
        file_dups.to_csv(file_dups_csv, index=False)
        log_run_job(run_id, f"Found {len(file_dups)} exact file-level duplicate(s).")
        time.sleep(0.4)

        # Step 4: Paper-level Deduplication
        job["step"] = "Paper-Level Deduplication"
        job["progress"] = 85
        log_run_job(run_id, "Executing DOI matching, normalized title matching, and fuzzy similarity comparison...")
        enriched_df = pd.read_csv(enriched_csv).fillna("")
        df_norm = normalize_papers(enriched_df)
        results = detect_paper_duplicates(df_norm)
        results.to_csv(results_csv, index=False)
        job["progress"] = 92
        log_run_job(run_id, "Paper-level deduplication completed.")
        time.sleep(0.4)

        # Step 5: Preparing Verification Queue
        job["step"] = "Preparing Human Verification Queue"
        queue = create_verification_queue(results, dataset="custom")
        queue.to_csv(queue_csv, index=False)
        log_run_job(run_id, f"Verification queue created with {len(queue)} candidate(s).")

        # Step 6: Initial report attempt or standby
        # If there are candidates requiring human review, we generate a provisional report & flowchart
        # so the user can immediately see the diagram with pending review!
        job["progress"] = 98
        job["step"] = "Generating PRISMA Flowchart"
        log_run_job(run_id, "Generating initial PRISMA deduplication flowchart...")

        # Count reviewed
        confirmed_ids = set()
        if not queue.empty:
            confirmed_ids = set(queue.loc[queue["verification_status"] == "Confirmed Duplicate", "record_id"])
        
        retained_init = results[~results["record_id"].isin(confirmed_ids)].copy()
        retained_init.to_csv(retained_csv, index=False)

        # Generate PRISMA report
        generate_prisma_report(
            dataset="run",
            results_file=results_csv,
            queue_file=queue_csv,
            retained_file=retained_csv,
            report_file=prisma_summary_csv,
            file_duplicates_count=len(file_dups)
        )

        create_prisma_flowchart(
            summary_file=prisma_summary_csv,
            retained_file=retained_csv,
            png_file=flowchart_png,
            pdf_file=flowchart_pdf,
            title_text=f"PRISMA 2020 Flow Diagram – {job.get('name', run_id)}"
        )

        job["progress"] = 100
        job["status"] = "completed"
        job["completed_at"] = time.time()
        job["step"] = "Completed"
        log_run_job(run_id, f"Processing finished. {len(queue)} candidates queued for human verification.")

        # Update info.json
        run_info = {
            "run_id": run_id,
            "name": job.get("name", run_id),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pdf_count": len(file_names),
            "status": "completed",
            "has_candidates": len(queue) > 0,
            "candidates_count": len(queue),
        }
        with open(info_json, "w", encoding="utf-8") as f:
            json.dump(run_info, f, indent=2)

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        log_run_job(run_id, f"Processing error: {e}")
        run_info = {
            "run_id": run_id,
            "name": job.get("name", run_id),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pdf_count": len(file_names),
            "status": "error",
            "error": str(e),
        }
        with open(info_json, "w", encoding="utf-8") as f:
            json.dump(run_info, f, indent=2)


# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "RESEARCH DEDUPLICATOR", "version": "2.0.0"}


@app.get("/api/runs")
def list_runs():
    """List all available processing runs, sorted newest first."""
    runs = []
    if RUNS_DIR.exists():
        for d in sorted(RUNS_DIR.iterdir(), reverse=True):
            if d.is_dir() and d.name.startswith("run_"):
                info_file = d / "info.json"
                if info_file.exists():
                    try:
                        with open(info_file, "r", encoding="utf-8") as f:
                            runs.append(json.load(f))
                        continue
                    except Exception:
                        pass
                # Fallback if info.json missing
                runs.append({
                    "run_id": d.name,
                    "name": d.name.replace("_", " ").title(),
                    "created_at": datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "pdf_count": len(list((d / "pdfs").glob("*.pdf"))) if (d / "pdfs").exists() else 0,
                    "status": "completed" if (d / "prisma_summary.csv").exists() else "pending",
                })
    return {"runs": runs}


@app.post("/api/upload")
async def create_run_and_upload_pdfs(files: List[UploadFile] = File(...)):
    """Upload PDFs to a new isolated run directory and trigger background pipeline."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    run_id = get_next_run_id()
    run_dir = RUNS_DIR / run_id
    pdf_dir = run_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    saved_filenames = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        dest = pdf_dir / file.filename
        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_filenames.append(file.filename)

    if not saved_filenames:
        raise HTTPException(status_code=400, detail="No valid PDF files were uploaded.")

    # Format run name e.g. "Run 001 – 8 Research Papers"
    run_num = run_id.split("_")[1]
    run_name = f"Run {run_num} – {len(saved_filenames)} Research Papers"

    active_jobs[run_id] = {
        "run_id": run_id,
        "name": run_name,
        "status": "queued",
        "step": "Initializing",
        "progress": 5,
        "message": f"Queued {len(saved_filenames)} PDF file(s).",
        "logs": [],
        "started_at": time.time(),
        "completed_at": None,
        "error": None,
    }

    thread = threading.Thread(target=run_pipeline_for_run, args=(run_id, saved_filenames))
    thread.daemon = True
    thread.start()

    return {
        "status": "started",
        "run_id": run_id,
        "name": run_name,
        "file_count": len(saved_filenames),
        "files": saved_filenames,
    }


@app.get("/api/runs/{run_id}/status")
def get_run_status(run_id: str):
    """Get live job progress or completion status for a run."""
    if run_id in active_jobs:
        return active_jobs[run_id]

    run_dir = get_run_dir(run_id)
    summary_csv = run_dir / "prisma_summary.csv"
    return {
        "run_id": run_id,
        "status": "completed" if summary_csv.exists() else "idle",
        "step": "Completed" if summary_csv.exists() else "Idle",
        "progress": 100 if summary_csv.exists() else 0,
        "message": "Ready.",
        "logs": [],
    }


@app.get("/api/runs/{run_id}/results")
def get_run_results(run_id: str):
    """Get the processing results summary for a specific run."""
    run_dir = get_run_dir(run_id)
    pdf_dir = run_dir / "pdfs"
    extracted_csv = run_dir / "pdf_extracted_metadata.csv"
    results_csv = run_dir / "deduplication_results.csv"
    queue_csv = run_dir / "verification_queue.csv"
    retained_csv = run_dir / "deduplicated_records.csv"
    file_dups_csv = run_dir / "file_duplicates.csv"
    prisma_summary_csv = run_dir / "prisma_summary.csv"

    pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    total_uploaded = len(pdf_files)

    # File duplicates count
    file_dups_count = 0
    file_dups_list = []
    if file_dups_csv.exists():
        fdf = pd.read_csv(file_dups_csv).fillna("")
        file_dups_count = len(fdf)
        for _, r in fdf.iterrows():
            file_dups_list.append({
                "duplicate": str(r.get("filename", "")),
                "original": str(r.get("duplicate_of_file", "")),
                "hash": str(r.get("file_hash", "")),
            })

    # Paper duplicates
    paper_candidates_count = 0
    if results_csv.exists():
        rdf = pd.read_csv(results_csv).fillna("")
        if "duplicate_status" in rdf.columns:
            paper_candidates_count = int(rdf["duplicate_status"].isin(["Duplicate", "Potential Duplicate"]).sum())

    # Verification counts
    confirmed_count = 0
    not_duplicate_count = 0
    pending_count = 0
    if queue_csv.exists():
        qdf = pd.read_csv(queue_csv).fillna("")
        if "verification_status" in qdf.columns:
            confirmed_count = int((qdf["verification_status"] == "Confirmed Duplicate").sum())
            not_duplicate_count = int((qdf["verification_status"] == "Not Duplicate").sum())
            pending_count = int((~qdf["verification_status"].isin(["Confirmed Duplicate", "Not Duplicate"])).sum())

    # Retained count: Initial uploaded records - Unique confirmed duplicates
    unique_retained_count = total_uploaded - confirmed_count if total_uploaded > 0 else 0
    if retained_csv.exists():
        retdf = pd.read_csv(retained_csv).fillna("")
        unique_retained_count = len(retdf)

    # Stages summary
    stages = [
        {"name": "PDF Ingestion & SHA-256 Hashing", "status": "Completed" if extracted_csv.exists() else "Pending"},
        {"name": "Crossref Metadata Enrichment", "status": "Completed" if (run_dir / "pdf_enriched_metadata.csv").exists() else "Pending"},
        {"name": "File-Level Duplicate Detection", "status": "Completed" if file_dups_csv.exists() else "Pending"},
        {"name": "Paper-Level Duplicate Detection", "status": "Completed" if results_csv.exists() else "Pending"},
        {"name": "Human Verification Queue", "status": "Reviewed" if pending_count == 0 else f"{pending_count} Pending"},
        {"name": "PRISMA Flowchart & Reporting", "status": "Generated" if (run_dir / "prisma_flowchart.png").exists() else "Pending"},
    ]

    return {
        "run_id": run_id,
        "total_uploaded": total_uploaded,
        "exact_file_duplicates": file_dups_count,
        "file_duplicates_list": file_dups_list,
        "paper_duplicate_candidates": paper_candidates_count,
        "confirmed_duplicates_removed": confirmed_count,
        "not_duplicate_retained": not_duplicate_count,
        "pending_verification": pending_count,
        "unique_retained_records": unique_retained_count,
        "stages": stages,
        "ready_for_finalization": pending_count == 0,
    }


@app.get("/api/runs/{run_id}/metadata")
def get_run_metadata(
    run_id: str,
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """Return extracted & enriched metadata for a run."""
    run_dir = get_run_dir(run_id)
    enriched_csv = run_dir / "pdf_enriched_metadata.csv"
    extracted_csv = run_dir / "pdf_extracted_metadata.csv"

    if not enriched_csv.exists() and not extracted_csv.exists():
        return {"records": [], "total": 0}

    csv_path = enriched_csv if enriched_csv.exists() else extracted_csv
    df = pd.read_csv(csv_path).fillna("")

    issues_csv = run_dir / "pdf_metadata_enrichment_issues.csv"
    issues_map = {}
    if issues_csv.exists():
        idf = pd.read_csv(issues_csv).fillna("")
        for _, r in idf.iterrows():
            issues_map[str(r.get("filename", ""))] = str(r.get("issue", ""))

    records = []
    for _, row in df.iterrows():
        fname = str(row.get("filename", ""))
        records.append({
            "filename": fname,
            "title": str(row.get("title", "")),
            "author": str(row.get("author", "")),
            "doi": str(row.get("doi", "")),
            "year": str(row.get("year", "")),
            "journal": str(row.get("crossref_journal", "")),
            "publisher": str(row.get("crossref_publisher", "")),
            "volume": str(row.get("crossref_volume", "")),
            "issue": str(row.get("crossref_issue", "")),
            "page": str(row.get("crossref_page", "")),
            "publication_date": str(row.get("crossref_publication_date", "")),
            "metadata_source": str(row.get("metadata_source", "PDF extraction")),
            "validation_status": str(row.get("metadata_validation", "Needs Review")),
            "enrichment_status": str(row.get("enrichment_status", "")),
            "title_match_score": row.get("title_match_score", ""),
            "file_hash": str(row.get("file_hash", "")),
            "issue": issues_map.get(fname, ""),
            # Side-by-side fields
            "pdf_title": str(row.get("pdf_title", row.get("title", ""))),
            "pdf_author": str(row.get("pdf_author", row.get("author", ""))),
            "pdf_year": str(row.get("pdf_year", row.get("year", ""))),
            "pdf_doi": str(row.get("doi", "")),
            "crossref_title": str(row.get("crossref_title", "")),
            "crossref_author": str(row.get("crossref_author", "")),
            "crossref_doi": str(row.get("crossref_doi", "")),
            "crossref_year": str(row.get("crossref_year", "")),
        })

    if q:
        ql = q.lower()
        records = [
            r for r in records
            if ql in r["title"].lower() or ql in r["author"].lower() or ql in r["doi"].lower() or ql in r["filename"].lower()
        ]

    if status and status != "all":
        records = [r for r in records if r["validation_status"].lower() == status.lower()]

    return {"records": records, "total": len(records)}


@app.get("/api/runs/{run_id}/verification/queue")
def get_run_verification_queue(run_id: str):
    """Return duplicate candidates requiring review with side-by-side paper comparisons."""
    run_dir = get_run_dir(run_id)
    queue_csv = run_dir / "verification_queue.csv"
    results_csv = run_dir / "deduplication_results.csv"

    if not queue_csv.exists():
        return {"candidates": [], "total": 0, "pending_count": 0}

    queue_df = pd.read_csv(queue_csv).fillna("")
    results_df = pd.read_csv(results_csv).fillna("") if results_csv.exists() else pd.DataFrame()

    paper_lookup = {}
    if not results_df.empty and "record_id" in results_df.columns:
        results_df["record_id"] = results_df["record_id"].astype(str)
        paper_lookup = results_df.set_index("record_id").to_dict("index")

    candidates = []
    for _, row in queue_df.iterrows():
        matched_id = str(row.get("matched_record", ""))
        matched_info = paper_lookup.get(matched_id, {})

        candidates.append({
            "record_id": str(row.get("record_id", "")),
            "filename": str(row.get("filename", "")),
            "title": str(row.get("title", "")),
            "author": str(row.get("author", "")),
            "doi": str(row.get("doi", "")),
            "year": str(row.get("year", "")),
            "duplicate_status": str(row.get("duplicate_status", "")),
            "match_reason": str(row.get("match_reason", "")),
            "title_similarity": row.get("title_similarity", 0),
            "verification_status": str(row.get("verification_status", "Pending")),
            "reviewer_decision": str(row.get("reviewer_decision", "")),
            "matched_record": {
                "record_id": matched_id,
                "filename": str(matched_info.get("filename", "")),
                "title": str(matched_info.get("title", "")),
                "author": str(matched_info.get("author", "")),
                "doi": str(matched_info.get("doi", "")),
                "year": str(matched_info.get("year", "")),
            } if matched_info else None,
        })

    pending_count = sum(1 for c in candidates if c["verification_status"] not in ["Confirmed Duplicate", "Not Duplicate"])

    return {"candidates": candidates, "total": len(candidates), "pending_count": pending_count}


class RunDecisionRequest(BaseModel):
    record_id: str
    decision: str  # "Confirmed Duplicate", "Not Duplicate", "Pending"


@app.post("/api/runs/{run_id}/verification/decide")
def submit_run_verification_decision(run_id: str, req: RunDecisionRequest):
    """Save reviewer decision persistently for a run."""
    run_dir = get_run_dir(run_id)
    queue_csv = run_dir / "verification_queue.csv"

    if not queue_csv.exists():
        raise HTTPException(status_code=404, detail="Verification queue not found.")

    df = pd.read_csv(queue_csv).fillna("")
    df["record_id"] = df["record_id"].astype(str)

    mask = df["record_id"] == req.record_id
    if not mask.any():
        raise HTTPException(status_code=404, detail=f"Record ID {req.record_id} not found.")

    df.loc[mask, "verification_status"] = req.decision
    df.loc[mask, "reviewer_decision"] = req.decision
    df.to_csv(queue_csv, index=False)

    return {"status": "success", "record_id": req.record_id, "decision": req.decision}


@app.post("/api/runs/{run_id}/verification/finalize")
def finalize_run_verification(run_id: str):
    """Rebuild retained dataset, update PRISMA summary and generate flowchart."""
    run_dir = get_run_dir(run_id)
    results_csv = run_dir / "deduplication_results.csv"
    queue_csv = run_dir / "verification_queue.csv"
    retained_csv = run_dir / "deduplicated_records.csv"
    prisma_summary_csv = run_dir / "prisma_summary.csv"
    file_dups_csv = run_dir / "file_duplicates.csv"
    flowchart_png = run_dir / "prisma_flowchart.png"
    flowchart_pdf = run_dir / "prisma_flowchart.pdf"

    try:
        build_retained_dataset(
            results_file=results_csv,
            queue_file=queue_csv,
            output_file=retained_csv,
        )

        file_dups_count = len(pd.read_csv(file_dups_csv)) if file_dups_csv.exists() else 0

        generate_prisma_report(
            dataset="run",
            results_file=results_csv,
            queue_file=queue_csv,
            retained_file=retained_csv,
            report_file=prisma_summary_csv,
            file_duplicates_count=file_dups_count,
        )

        create_prisma_flowchart(
            summary_file=prisma_summary_csv,
            retained_file=retained_csv,
            png_file=flowchart_png,
            pdf_file=flowchart_pdf,
            title_text=f"PRISMA 2020 Flow Diagram – {run_id.replace('_', ' ').title()}",
        )

        return {"status": "success", "message": f"Deduplication finalized and PRISMA flowchart generated for {run_id}."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/runs/{run_id}/prisma")
def get_run_prisma(run_id: str):
    """Return PRISMA summary metrics and flowchart availability for a run."""
    run_dir = get_run_dir(run_id)
    summary_csv = run_dir / "prisma_summary.csv"
    retained_csv = run_dir / "deduplicated_records.csv"
    flowchart_png = run_dir / "prisma_flowchart.png"

    metrics = []
    if summary_csv.exists():
        df = pd.read_csv(summary_csv)
        for _, r in df.iterrows():
            metrics.append({"metric": str(r["metric"]), "count": int(r["count"])})

    retained_records = []
    if retained_csv.exists():
        rdf = pd.read_csv(retained_csv).fillna("")
        for _, r in rdf.iterrows():
            retained_records.append({
                "filename": str(r.get("filename", "")),
                "title": str(r.get("title", "")),
                "author": str(r.get("author", "")),
                "doi": str(r.get("doi", "")),
                "year": str(r.get("year", "")),
            })

    return {
        "run_id": run_id,
        "metrics": metrics,
        "total_retained": len(retained_records),
        "retained_records": retained_records,
        "flowchart_available": flowchart_png.exists(),
    }


@app.get("/api/runs/{run_id}/flowchart.png")
def get_run_flowchart_png(run_id: str):
    run_dir = get_run_dir(run_id)
    png_path = run_dir / "prisma_flowchart.png"
    if not png_path.exists():
        raise HTTPException(status_code=404, detail="PRISMA flowchart image not found.")
    return FileResponse(png_path, media_type="image/png")


@app.get("/api/runs/{run_id}/download/{file_type}")
def download_run_file(run_id: str, file_type: str):
    run_dir = get_run_dir(run_id)
    allowed = {
        "flowchart-png": run_dir / "prisma_flowchart.png",
        "flowchart-pdf": run_dir / "prisma_flowchart.pdf",
        "retained-csv": run_dir / "deduplicated_records.csv",
        "summary-csv": run_dir / "prisma_summary.csv",
        "extracted-csv": run_dir / "pdf_extracted_metadata.csv",
        "enriched-csv": run_dir / "pdf_enriched_metadata.csv",
    }
    path = allowed.get(file_type)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Requested file not found.")

    ext = path.suffix.replace(".", "")
    filename = f"{run_id}_{file_type}.{ext}"
    return FileResponse(path, filename=filename)


# ==============================================================================
# Benchmark Experiment: Crossref 500 (Preserved completely separately)
# ==============================================================================

@app.get("/api/benchmark/crossref")
def get_benchmark_crossref():
    """Return the static Crossref 500 benchmark results."""
    summary_csv = BENCHMARK_DIR / "crossref_prisma_summary.csv"
    retained_csv = BENCHMARK_DIR / "crossref_deduplicated_records.csv"
    queue_csv = BENCHMARK_DIR / "crossref_verification_queue.csv"

    metrics = []
    if summary_csv.exists():
        df = pd.read_csv(summary_csv)
        for _, r in df.iterrows():
            metrics.append({"metric": str(r["metric"]), "count": int(r["count"])})

    retained_count = 496
    if retained_csv.exists():
        retained_count = len(pd.read_csv(retained_csv))

    candidates = []
    if queue_csv.exists():
        qdf = pd.read_csv(queue_csv).fillna("")
        for _, r in qdf.iterrows():
            candidates.append({
                "record_id": str(r.get("record_id", "")),
                "title": str(r.get("title", "")),
                "author": str(r.get("author", "")),
                "doi": str(r.get("doi", "")),
                "duplicate_status": str(r.get("duplicate_status", "")),
                "match_reason": str(r.get("match_reason", "")),
                "title_similarity": float(r.get("title_similarity", 0)),
                "verification_status": str(r.get("verification_status", "")),
            })

    return {
        "dataset": "Crossref 500 Benchmark",
        "initial_records": 500,
        "duplicate_candidates": 5,
        "confirmed_duplicates": 4,
        "not_duplicates": 1,
        "pending_verification": 0,
        "records_removed": 4,
        "final_retained": retained_count,
        "metrics": metrics,
        "candidates": candidates,
        "flowchart_available": (BENCHMARK_DIR / "crossref_prisma_flowchart.png").exists(),
    }


@app.get("/api/benchmark/crossref/flowchart.png")
def get_benchmark_flowchart_png():
    png_path = BENCHMARK_DIR / "crossref_prisma_flowchart.png"
    if not png_path.exists():
        raise HTTPException(status_code=404, detail="Benchmark flowchart image not found.")
    return FileResponse(png_path, media_type="image/png")


@app.get("/api/benchmark/crossref/download/{file_type}")
def download_benchmark_file(file_type: str):
    allowed = {
        "flowchart-pdf": BENCHMARK_DIR / "crossref_prisma_flowchart.pdf",
        "flowchart-png": BENCHMARK_DIR / "crossref_prisma_flowchart.png",
        "retained-csv": BENCHMARK_DIR / "crossref_deduplicated_records.csv",
        "summary-csv": BENCHMARK_DIR / "crossref_prisma_summary.csv",
    }
    path = allowed.get(file_type)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path, filename=f"crossref_500_{file_type}.{path.suffix.replace('.', '')}")


# ==============================================================================
# SPA Static File Serving (Production React build fallback)
# ==============================================================================

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
