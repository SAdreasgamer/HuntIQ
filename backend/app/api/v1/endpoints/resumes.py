"""
HuntIQ — Resumes API Endpoint.

Endpoints for uploading PDF resumes, managing resume versions, and setting active primary resume.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.resume import ResumeVersionRepository
from app.resume.embeddings import ResumeEmbeddingService
from app.resume.parser import ResumeParser
from app.resume.storage import ResumeStorageService

router = APIRouter()


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
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

    # 1. Store on disk & compute SHA-256
    file_path, content_hash = storage_service.save_file(
        user_id=user.id,
        filename=file.filename,
        content=content,
    )

    # 2. Parse text & structure
    parsed_data = parser.parse_pdf_bytes(content, filename=file.filename)

    # 3. Save ResumeVersion record via ResumeStorageService
    version = await storage_service.create_version(
        session=session,
        user_id=user.id,
        name=file.filename,
        file_path=str(file_path),
        file_hash=content_hash,
        parsed_data=parsed_data,
        is_primary=True,
    )

    # 4. Generate 384-dim dense vector embedding
    embed_service = ResumeEmbeddingService()
    await embed_service.create_or_update_embedding(session, version, parsed_data)

    await session.commit()

    # 5. Auto-match all existing jobs against the new resume
    matched_count = 0
    try:
        from app.matcher.composite_matcher import MatchingEngine
        matching_engine = MatchingEngine()
        matched_results = await matching_engine.batch_match_unscored_jobs(session, user.id, limit=200)
        matched_count = len(matched_results)
        await session.commit()
    except Exception:
        pass  # Matching is best-effort; upload should still succeed

    return {
        "id": version.id,
        "filename": version.name,
        "file_hash": version.file_hash,
        "is_primary": version.is_primary,
        "skills_found": parsed_data.skills[:10],
        "jobs_matched": matched_count,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


@router.get("/")
async def list_resumes(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List all uploaded resume versions for the current user."""
    resume_repo = ResumeVersionRepository(session)
    versions = await resume_repo.get_by_user_id(user.id)

    items = [
        {
            "id": v.id,
            "filename": v.name,
            "file_hash": v.file_hash,
            "is_primary": v.is_primary,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]
    return {"items": items, "count": len(items)}
