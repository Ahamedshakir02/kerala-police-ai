"""
Kerala Police AI — Bulk FIR Upload Script
==========================================
Use this to upload your REAL FIR text files into the database.

USAGE:
  1. Put your FIR .txt files in the  backend/fir_data/  folder
     (one FIR per file, named like:  KER_TVM_247_2024.txt)

  2. Make sure the backend is running:
       uvicorn main:app --reload --port 8000

  3. Run this script from the backend/ directory:
       .\\venv\\Scripts\\python.exe scripts\\upload_firs.py

  4. The script will login as the demo officer, upload each FIR,
     and trigger the NLP + ChromaDB indexing pipeline.

FILE NAMING CONVENTION:
  Each .txt file should follow this naming pattern:
    DISTRICT_STATION_CASENUMBER.txt
  Example:
    Thiruvananthapuram_EastPS_247_2024.txt

  OR: put metadata on the FIRST 3 lines of the file:
    Line 1:  CASE_NUMBER: KER/TVM/247/2024
    Line 2:  DISTRICT: Thiruvananthapuram
    Line 3:  STATION: Thiruvananthapuram East Police Station
    (remaining lines = FIR body text)
"""

import os
import sys
import re
import requests
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
BADGE_NUMBER = "KP001"
PASSWORD = "test1234"
FIR_DIR = Path(__file__).parent.parent / "fir_data"

# ── Auth ──────────────────────────────────────────────────────────────────────

def login() -> str:
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "badge_number": BADGE_NUMBER,
        "password": PASSWORD,
    })
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.text}")
        sys.exit(1)
    token = resp.json()["access_token"]
    print(f"✅ Logged in as {BADGE_NUMBER}")
    return token


def parse_fir_file(filepath: Path) -> dict:
    """
    Parse a FIR file for metadata.
    - For TXT files: reads and parses header metadata + body text
    - For PDF files: only extracts metadata from filename (server extracts text via pdfplumber)
    """
    is_pdf = filepath.suffix.lower() == ".pdf"

    if is_pdf:
        # For PDFs, text extraction is done server-side.
        # Try to get metadata from filename only.
        stem = filepath.stem.replace("_", " ").replace("-", " ")
        return {
            "case_number": f"AUTO/{filepath.stem.upper().replace(' ', '_')}",
            "district": "Kerala",
            "station": stem[:50],
            "raw_text": "",  # ignored for PDFs
        }

    text = filepath.read_text(encoding="utf-8", errors="replace")
    lines = text.strip().splitlines()

    case_number = None
    district = None
    station = None
    body_start = 0

    # Try to parse metadata headers
    for i, line in enumerate(lines[:6]):
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().upper()
            val = val.strip()
            if key in ("CASE_NUMBER", "FIR NO", "FIR NUMBER"):
                case_number = val
                body_start = max(body_start, i + 1)
            elif key == "DISTRICT":
                district = val
                body_start = max(body_start, i + 1)
            elif key in ("STATION", "POLICE STATION"):
                station = val
                body_start = max(body_start, i + 1)

    # Fallback: try to extract from file text using regex
    if not case_number:
        m = re.search(r"FIR\s*No[:\s.]+([A-Z0-9/\-]+)", text, re.IGNORECASE)
        if m:
            case_number = m.group(1).strip()

    if not district:
        m = re.search(r"District[:\s]+([A-Za-z\s]+?)(?:\n|,|\.)", text, re.IGNORECASE)
        if m:
            district = m.group(1).strip()

    if not station:
        m = re.search(r"Police\s+Station[:\s]+([A-Za-z\s]+?)(?:\n|,|\.)", text, re.IGNORECASE)
        if m:
            station = m.group(1).strip()

    # Final fallback: use filename
    stem = filepath.stem.replace("_", " ").replace("-", " ")
    if not case_number:
        case_number = f"AUTO/{filepath.stem.upper()}"
    if not district:
        district = "Kerala"
    if not station:
        station = stem[:50]

    raw_text = "\n".join(lines[body_start:]).strip() or text.strip()

    return {
        "case_number": case_number,
        "district": district,
        "station": station,
        "raw_text": raw_text,
    }


def upload_fir(token: str, fir: dict, filepath: Path) -> bool:
    headers = {"Authorization": f"Bearer {token}"}
    is_pdf = filepath.suffix.lower() == ".pdf"

    # Check if it exists first
    resp = requests.get(f"{BASE_URL}/api/firs", headers=headers)
    if resp.ok:
        existing = [f["case_number"] for f in resp.json()]
        if fir["case_number"] in existing:
            print(f"  ⚡ {fir['case_number']} already in DB — skipping")
            return True

    if is_pdf:
        # Send PDF as file upload — server extracts text via pdfplumber
        with open(filepath, "rb") as pdf_file:
            resp = requests.post(
                f"{BASE_URL}/api/firs/upload",
                data={
                    "case_number": fir["case_number"],
                    "district": fir["district"],
                    "police_station": fir["station"],
                    "original_language": "en",
                },
                files={"file": (filepath.name, pdf_file, "application/pdf")},
                headers=headers,
            )
    else:
        # Send as raw text
        resp = requests.post(
            f"{BASE_URL}/api/firs/upload",
            data={
                "case_number": fir["case_number"],
                "district": fir["district"],
                "police_station": fir["station"],
                "original_language": "en",
                "text": fir["raw_text"],
            },
            headers=headers,
        )

    if resp.status_code == 201:
        fir_id = resp.json()["id"]
        print(f"  ✅ Uploaded: {fir['case_number']} (ID: {fir_id})")
        # Trigger indexing
        idx_resp = requests.post(f"{BASE_URL}/api/firs/{fir_id}/train", headers=headers)
        if idx_resp.ok:
            print(f"     🔍 Indexing started for {fir['case_number']}")
        return True
    elif resp.status_code == 409:
        print(f"  ⚡ {fir['case_number']} already exists")
        return True
    else:
        print(f"  ❌ Failed to upload {fir['case_number']}: {resp.text[:200]}")
        return False


def main():
    print("\n🚔 Kerala Police AI — Bulk FIR Uploader")
    print("=" * 50)

    if not FIR_DIR.exists():
        FIR_DIR.mkdir(parents=True)
        print(f"\n📁 Created directory: {FIR_DIR}")
        print("   ➜ Place your FIR .txt files in this folder and re-run the script.")
        print("   ➜ File format: plain text, UTF-8 encoded")
        print("   ➜ Optional: first lines can have CASE_NUMBER:, DISTRICT:, STATION: headers\n")
        return

    pdf_files = list(FIR_DIR.glob("*.pdf"))
    txt_files = list(FIR_DIR.glob("*.txt"))
    all_files = sorted(pdf_files + txt_files)

    if not all_files:
        print(f"\n⚠️  No PDF or TXT files found in {FIR_DIR}")
        print("   ➜ Copy your FIR PDF/TXT files there and re-run.")
        return

    print(f"\n📋 Found {len(all_files)} FIR file(s): {len(pdf_files)} PDF, {len(txt_files)} TXT\n")

    token = login()
    print()

    success = 0
    fail = 0
    for fp in all_files:
        print(f"📄 Processing: {fp.name}")
        try:
            fir = parse_fir_file(fp)
            print(f"   Case: {fir['case_number']}, District: {fir['district']}, Station: {fir['station']}")
            if upload_fir(token, fir, fp):
                success += 1
            else:
                fail += 1
        except Exception as e:
            print(f"  ❌ Error processing {fp.name}: {e}")
            fail += 1
        print()

    print("=" * 50)
    print(f"✅ Uploaded: {success}  |  ❌ Failed: {fail}")
    print("\nNow open the app — FIRs will appear in Case Intelligence and MO Patterns after indexing.\n")


if __name__ == "__main__":
    main()
