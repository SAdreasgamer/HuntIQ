"""
HuntIQ — Resumes API Endpoint.

Endpoints for uploading PDF resumes, managing resume versions, and setting active primary resume.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_stub, get_db
from app.models.user import User
from app.repositories.resume import ResumeVersionRepository
from app.resume.parser import ResumeParser
from app.resume.storage import ResumeStorageService

router = APIRouter()


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Upload and parse a new candidate PDF resume version."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    storage_service = ResumeStorageService()
    parser = ResumeParser()
    resume_repo = ResumeVersionRepository(session)

    # 1. Store on disk & compute SHA-256
    file_path, content_hash = await storage_service.save_resume_file(
        file_bytes=content,
        user_id=user.id,
        original_filename=file.filename,
    )

    # 2. Parse text & structure
    parsed_data = await parser.parse_pdf_bytes(content, filename=file.filename)

    # 3. Save ResumeVersion record
    version = await resume_repo.create_version(
        user_id=user.id,
        filename=file.filename,
        storage_path=str(file_path),
        file_hash=content_hash,
        parsed_data=parsed_data.model_dump(),
        is_primary=True,
    )
    await session.commit()

    return {
        "id": version.id,
        "filename": version.filename,
        "file_hash": version.file_hash,
        "is_primary": version.is_primary,
        "skills_found": parsed_data.skills.technical_skills[:10],
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


@router.get("/")
async def list_resumes(
    user: User = Depends(get_current_user_stub),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List all uploaded resume versions for the current user."""
    resume_repo = ResumeVersionRepository(session)
    versions = await resume_repo.get_user_versions(user.id)

    items = [
        {
            "id": v.id,
            "filename": v.filename,
            "file_hash": v.file_hash,
            "is_primary": v.is_primary,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]
    return {"items": items, "count": len(items)}
