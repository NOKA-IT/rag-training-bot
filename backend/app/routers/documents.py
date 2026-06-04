"""Document upload, listing, and deletion endpoints."""
import os
import uuid
from typing import List, Optional

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
)
from sqlalchemy.orm import Session

from ..database import get_db, SessionLocal
from ..models import Document, Category, Department, User, Role
from ..schemas import DocumentOut
from ..config import settings
from ..deps import require_uploader, get_current_user
from ..services import document_processor, vector_store

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXT = {"pdf", "docx", "doc", "txt", "md", "text"}


def _process_document(document_id: int):
    """Background task: extract text, chunk, embed, store in Chroma."""
    db = SessionLocal()
    try:
        doc = db.query(Document).get(document_id)
        if not doc:
            return
        try:
            text = document_processor.extract_text(doc.stored_path, doc.file_type)
            chunks = document_processor.chunk_text(text)
            cat_ids = ",".join(str(c.id) for c in doc.categories)
            metadata = {
                "filename": doc.filename,
                "title": doc.title or doc.filename,
                "visibility": doc.visibility,
                "department_id": doc.department_id if doc.department_id is not None else -1,
                "category_ids": cat_ids,
            }
            count = vector_store.add_document_chunks(doc.id, chunks, metadata)
            doc.chunk_count = count
            doc.status = "ready" if count > 0 else "failed"
            if count == 0:
                doc.error = "No extractable text found in document."
        except Exception as e:  # noqa: BLE001
            doc.status = "failed"
            doc.error = str(e)[:480]
        db.commit()
    finally:
        db.close()


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(""),
    visibility: str = Form("department"),
    department_id: Optional[int] = Form(None),
    category_ids: str = Form(""),
    db: Session = Depends(get_db),
    current: User = Depends(require_uploader),
):
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400,
                            detail=f"Unsupported file type '.{ext}'")

    # Resolve department / visibility based on role
    if visibility not in ("general", "department"):
        visibility = "department"

    if current.role == Role.UPLOADER:
        # Uploaders are scoped to their own department
        department_id = current.department_id
        if department_id is None and visibility == "department":
            raise HTTPException(status_code=400,
                                detail="Uploader has no assigned department")
    else:  # admin
        if visibility == "department" and department_id is None:
            raise HTTPException(status_code=400,
                                detail="department_id required for department docs")

    if department_id is not None and not db.query(Department).get(department_id):
        raise HTTPException(status_code=400, detail="Department not found")

    # Save file to disk
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    content = await file.read()
    with open(stored_path, "wb") as f:
        f.write(content)

    doc = Document(
        filename=file.filename,
        stored_path=stored_path,
        file_type=ext,
        title=title or file.filename,
        visibility=visibility,
        department_id=department_id if visibility == "department" else None,
        uploaded_by=current.id,
        status="processing",
    )

    # Attach categories
    if category_ids.strip():
        ids = [int(x) for x in category_ids.split(",") if x.strip().isdigit()]
        cats = db.query(Category).filter(Category.id.in_(ids)).all()
        doc.categories = cats

    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(_process_document, doc.id)
    return doc


@router.get("", response_model=List[DocumentOut])
def list_documents(department_id: Optional[int] = None,
                   db: Session = Depends(get_db),
                   current: User = Depends(get_current_user)):
    q = db.query(Document)
    if current.role != Role.ADMIN:
        # general docs OR own-department docs
        if current.department_id is not None:
            q = q.filter(
                (Document.visibility == "general")
                | (Document.department_id == current.department_id)
            )
        else:
            q = q.filter(Document.visibility == "general")
    if department_id is not None:
        q = q.filter(Document.department_id == department_id)
    return q.order_by(Document.created_at.desc()).all()


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int,
                    db: Session = Depends(get_db),
                    current: User = Depends(require_uploader)):
    doc = db.query(Document).get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    # Uploaders can only delete docs in their department
    if current.role == Role.UPLOADER and doc.department_id != current.department_id:
        raise HTTPException(status_code=403,
                            detail="Cannot delete documents outside your department")

    vector_store.delete_document(doc.id)
    if doc.stored_path and os.path.exists(doc.stored_path):
        try:
            os.remove(doc.stored_path)
        except OSError:
            pass
    db.delete(doc)
    db.commit()
