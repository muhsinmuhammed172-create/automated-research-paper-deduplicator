import io
import time
import pandas as pd
from fastapi.testclient import TestClient
import fitz  # PyMuPDF
from server import app

client = TestClient(app)

print("=" * 60)
print("TEST 1: Benchmark Crossref 500 endpoint")
print("=" * 60)
res_bm = client.get("/api/benchmark/crossref")
assert res_bm.status_code == 200, res_bm.text
bm_data = res_bm.json()
print("Benchmark Name:", bm_data["dataset"])
print("Initial records:", bm_data["initial_records"])
print("Duplicate candidates:", bm_data["duplicate_candidates"])
print("Confirmed duplicates:", bm_data["confirmed_duplicates"])
print("Not duplicates:", bm_data["not_duplicates"])
print("Retained records:", bm_data["final_retained"])
assert bm_data["initial_records"] == 500
assert bm_data["final_retained"] == 496
assert bm_data["confirmed_duplicates"] == 4
assert bm_data["not_duplicates"] == 1
print("PASS: Benchmark Crossref 500 is completely isolated and correct!")

print("\n" + "=" * 60)
print("TEST 2: Create 3 test PDFs in memory (including 1 exact duplicate)")
print("=" * 60)

def make_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text, fontsize=12)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

pdf1_bytes = make_pdf(
    "Title: Deep Learning for Plant Disease Detection\n"
    "Author: Marcel Salathe, David Hughes\n"
    "DOI: 10.3389/fpls.2016.01419\n"
    "Published: 2016\n"
    "Abstract: Plant disease detection using deep neural networks."
)

# P1_copy has identical content to P1
pdf1_copy_bytes = pdf1_bytes

# P2 is a distinct paper
pdf2_bytes = make_pdf(
    "Title: Plant Disease Detection and Classification by Deep Learning\n"
    "Author: Muhammad Hammad Saleem, Johan Potgieter\n"
    "DOI: 10.3390/plants8110468\n"
    "Published: 2019\n"
    "Abstract: A comprehensive review of deep learning techniques."
)

files = [
    ("files", ("P1.pdf", pdf1_bytes, "application/pdf")),
    ("files", ("P1_copy.pdf", pdf1_copy_bytes, "application/pdf")),
    ("files", ("P2.pdf", pdf2_bytes, "application/pdf")),
]

print("Uploading 3 PDFs to /api/upload...")
res_up = client.post("/api/upload", files=files)
assert res_up.status_code == 200, res_up.text
up_data = res_up.json()
run_id = up_data["run_id"]
print(f"Created run: {run_id} ({up_data['name']})")

print("\nPolling run status until completion...")
for _ in range(30):
    time.sleep(1)
    res_st = client.get(f"/api/runs/{run_id}/status")
    st_data = res_st.json()
    print(f"Progress: {st_data.get('progress')}% | Step: {st_data.get('step')} | Status: {st_data.get('status')}")
    if st_data.get("status") in ["completed", "error"]:
        break

assert st_data.get("status") == "completed", f"Job failed: {st_data.get('error')}"
print("PASS: Run pipeline completed!")

print("\n" + "=" * 60)
print("TEST 3: Verify Run Results & File-Level SHA-256 Duplicate")
print("=" * 60)
res_res = client.get(f"/api/runs/{run_id}/results")
assert res_res.status_code == 200, res_res.text
res_data = res_res.json()
print("Total uploaded:", res_data["total_uploaded"])
print("Exact file duplicates (SHA-256):", res_data["exact_file_duplicates"])
print("File duplicates details:", res_data["file_duplicates_list"])
print("Paper duplicate candidates:", res_data["paper_duplicate_candidates"])
assert res_data["total_uploaded"] == 3
assert res_data["exact_file_duplicates"] == 1
assert res_data["file_duplicates_list"][0]["duplicate"] == "P1_copy.pdf"
assert res_data["file_duplicates_list"][0]["original"] == "P1.pdf"
print("PASS: P1_copy.pdf detected as exact file duplicate of P1.pdf via SHA-256!")

print("\n" + "=" * 60)
print("TEST 4: Candidate Verification Queue & Reviewer Decision")
print("=" * 60)
res_q = client.get(f"/api/runs/{run_id}/verification/queue")
assert res_q.status_code == 200
q_data = res_q.json()
print("Candidates count:", q_data["total"])
assert q_data["total"] >= 1
cand = q_data["candidates"][0]
print(f"Candidate: {cand['filename']} ({cand['title']}) matched with {cand['matched_record']['title']} via {cand['match_reason']}")

print("Submitting decision: 'Confirmed Duplicate' for candidate...")
res_dec = client.post(f"/api/runs/{run_id}/verification/decide", json={
    "record_id": cand["record_id"],
    "decision": "Confirmed Duplicate"
})
assert res_dec.status_code == 200, res_dec.text
print("PASS: Reviewer decision saved successfully!")

print("\n" + "=" * 60)
print("TEST 5: Finalize Deduplication & Generate PRISMA Flowchart")
print("=" * 60)
res_fin = client.post(f"/api/runs/{run_id}/verification/finalize")
assert res_fin.status_code == 200, res_fin.text
print("Finalize response:", res_fin.json())

# Check PRISMA data
res_pr = client.get(f"/api/runs/{run_id}/prisma")
assert res_pr.status_code == 200
pr_data = res_pr.json()
print("PRISMA Total Retained:", pr_data["total_retained"])
print("PRISMA Metrics:", pr_data["metrics"])
print("Flowchart available:", pr_data["flowchart_available"])
assert pr_data["total_retained"] == 2  # 3 initial - 1 confirmed duplicate = 2 retained
assert pr_data["flowchart_available"] is True
print("PASS: 3 initial PDFs - 1 confirmed duplicate = 2 unique retained papers!")

print("\n" + "=" * 60)
print("TEST 6: Download PRISMA flowchart & CSV files")
print("=" * 60)
res_png = client.get(f"/api/runs/{run_id}/flowchart.png")
assert res_png.status_code == 200
assert res_png.headers["content-type"] == "image/png"
print("Flowchart PNG download: OK (bytes:", len(res_png.content), ")")

res_csv = client.get(f"/api/runs/{run_id}/download/retained-csv")
assert res_csv.status_code == 200
print("Retained CSV download: OK")

print("\nALL WORKFLOW TESTS COMPLETED SUCCESSFULLY!")
