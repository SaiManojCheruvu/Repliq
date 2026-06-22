from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from auth import get_current_user
from database import get_db
from models import User
from services.parser import parse_file
from services.vector_store import delete_chunks, list_chunks, store_chunks
from logger import get_logger

logger = get_logger("repliq.kb_router")

router = APIRouter(prefix="/kb", tags=["knowledge-base"])


# ── Response schemas ──────────────────────────────────────────────────────────


class UploadResponse(BaseModel):
    message: str
    source_name: str
    source_type: str
    chunks_stored: int


class KBEntry(BaseModel):
    source_name: str
    source_type: str
    chunk_count: int


class KBListResponse(BaseModel):
    business_id: str
    total_sources: int
    entries: list[KBEntry]


class DeleteResponse(BaseModel):
    message: str
    business_id: str




@router.post("/{business_id}/file", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_kb_file(
    business_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF, CSV, or XLSX file and ingest it into the business's KB.

    Steps
    -----
    1. Authorise: the calling admin must belong to this business.
    2. Parse: delegate to services/parser.parse_file() → raw text.
    3. Store: delegate to services/vector_store.store_chunks() → ChromaDB.
    4. Return: chunk count so the UI can confirm ingestion.
    """
    _assert_owns_business(current_user, business_id)

    try:
        extracted_text = await parse_file(file)
    except ValueError as exc:
        logger.warning("Parse failed for %s: %s", file.filename, exc)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # Derive source_type from content_type for the metadata label
    source_type = _content_type_to_label(file.content_type or "")

    chunks_stored = store_chunks(
        business_id=business_id,
        text=extracted_text,
        source_name=file.filename or "uploaded_file",
        source_type=source_type,
    )

    logger.info(
        "KB upload complete: business=%s file=%s chunks=%d",
        business_id,
        file.filename,
        chunks_stored,
    )

    return UploadResponse(
        message="File ingested successfully",
        source_name=file.filename or "uploaded_file",
        source_type=source_type,
        chunks_stored=chunks_stored,
    )



@router.post("/{business_id}/text", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_kb_text(
    business_id: str,
    text: str = Form(..., description="Raw knowledge base text pasted by the admin"),
    label: str = Form(default="manual_text", description="Human-readable label for this entry"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accept raw pasted text as KB input (no file parsing needed).

    This satisfies KB-03 from the business requirements:
    'Admin can paste raw text as knowledge base'.
    """
    _assert_owns_business(current_user, business_id)

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text cannot be empty.",
        )

    chunks_stored = store_chunks(
        business_id=business_id,
        text=text,
        source_name=label,
        source_type="text",
    )

    return UploadResponse(
        message="Text ingested successfully",
        source_name=label,
        source_type="text",
        chunks_stored=chunks_stored,
    )



@router.get("/{business_id}", response_model=KBListResponse)
def get_kb_entries(
    business_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all uploaded KB sources for this business (admin panel).
    """
    _assert_owns_business(current_user, business_id)

    entries = list_chunks(business_id)
    return KBListResponse(
        business_id=business_id,
        total_sources=len(entries),
        entries=[KBEntry(**e) for e in entries],
    )



@router.delete("/{business_id}", response_model=DeleteResponse)
def delete_kb(
    business_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hard-delete all KB chunks for this business (full reset).
    The collection can be re-populated by uploading files again.
    """
    _assert_owns_business(current_user, business_id)

    deleted = delete_chunks(business_id)
    msg = "KB deleted successfully" if deleted else "KB collection did not exist"
    return DeleteResponse(message=msg, business_id=business_id)



def _assert_owns_business(user: User, business_id: str) -> None:
    """
    Ensure the authenticated admin owns the requested business.
    This prevents one admin from modifying another business's KB.
    """
    if user.business_id != business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this business.",
        )


def _content_type_to_label(content_type: str) -> str:
    mapping = {
        "application/pdf": "pdf",
        "text/csv": "csv",
        "application/vnd.ms-excel": "csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    }
    return mapping.get(content_type, "unknown")