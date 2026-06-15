import io
import csv
import pdfplumber
import pandas as pd
from fastapi import UploadFile
from logger import get_logger

logger = get_logger("repliq.parser")

SUPPORTED_TYPES = {
    "application/pdf": "pdf",
    "text/csv": "csv",
    "application/vnd.ms-excel": "csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
}


async def parse_file(file: UploadFile) -> str:
    content_type = file.content_type
    file_type = SUPPORTED_TYPES.get(content_type)

    if not file_type:
        logger.error(f"Unsupported file type: {content_type}")
        raise ValueError(f"Unsupported file type: {content_type}")
    
     
    logger.info("Parsing file: %s | type: %s", file.filename, file_type)
 
    raw_bytes = await file.read()
 
    if file_type == "pdf":
        return _parse_pdf(raw_bytes, file.filename)
    elif file_type == "csv":
        return _parse_csv(raw_bytes, file.filename)
    elif file_type == "xlsx":
        return _parse_xlsx(raw_bytes, file.filename)
    

def _parse_pdf(raw_bytes: bytes, filename: str) -> str:
    """Extract all text from a PDF file page by page."""
    text_chunks = []
 
    with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
        total_pages = len(pdf.pages)
        logger.info("PDF has %d pages: %s", total_pages, filename)
 
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                text_chunks.append(f"[Page {i + 1}]\n{text.strip()}")
 
    if not text_chunks:
        raise ValueError(f"No text could be extracted from PDF: {filename}")
 
    full_text = "\n\n".join(text_chunks)
    logger.info("Extracted %d characters from PDF: %s", len(full_text), filename)
    return full_text

def _parse_csv(raw_bytes: bytes, filename: str) -> str:
    """Convert CSV rows into readable text chunks."""
    text_chunks = []
 
    decoded = raw_bytes.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)
 
    if not rows:
        raise ValueError(f"CSV file is empty: {filename}")
 
    logger.info("CSV has %d rows: %s", len(rows), filename)
 
    for i, row in enumerate(rows):
        # Convert each row to "key: value" format
        row_text = " | ".join(f"{k}: {v}" for k, v in row.items() if v and v.strip())
        if row_text:
            text_chunks.append(f"[Row {i + 1}] {row_text}")
 
    full_text = "\n".join(text_chunks)
    logger.info("Extracted %d characters from CSV: %s", len(full_text), filename)
    return full_text
 
 
def _parse_xlsx(raw_bytes: bytes, filename: str) -> str:
    """Convert Excel file rows into readable text chunks."""
    text_chunks = []
 
    df = pd.read_excel(io.BytesIO(raw_bytes))
    df = df.fillna("")  # replace NaN with empty string
 
    logger.info("XLSX has %d rows, %d columns: %s", len(df), len(df.columns), filename)
 
    for i, row in df.iterrows():
        row_text = " | ".join(f"{col}: {val}" for col, val in row.items() if str(val).strip())
        if row_text:
            text_chunks.append(f"[Row {i + 1}] {row_text}")
 
    full_text = "\n".join(text_chunks)
    logger.info("Extracted %d characters from XLSX: %s", len(full_text), filename)
    return full_text
 