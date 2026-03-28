# FIR Data Folder — Kerala Police AI

Place your **real FIR files** here — **PDF or TXT format** are both supported.

## For PDF FIRs (most common)
Just drop any `.pdf` FIR files here. The server will automatically extract the text using `pdfplumber`.

**Naming tip:** Name the file after the case number for easy tracking:
```
KER_TVM_247_2024.pdf
KER_EKM_112_2024.pdf
```

## For TXT FIRs
Optionally add metadata headers at the top:

```
CASE_NUMBER: KER/TVM/247/2024
DISTRICT: Thiruvananthapuram
STATION: Thiruvananthapuram East Police Station

[Full FIR text below...]
```

## How to Upload

```powershell
cd backend
.\venv\Scripts\python.exe scripts\upload_firs.py
```

The script will:
1. Login as the demo officer
2. Upload each FIR via the API
3. Trigger NLP analysis + ChromaDB indexing for each FIR

## Notes
- One file per FIR
- If metadata headers (CASE_NUMBER, DISTRICT, STATION) are omitted, the script will try to parse them from the FIR body using regex
- Malayalam FIRs are supported — just set the language tag in the file if needed
- Files already uploaded will be skipped (no duplicates)
