"""
HuntIQ — Resume Storage & Versioning Service.

Manages file persistence, SHA-256 hash deduplication, multi-version creation,
skills database synchronization, and active/primary version switching.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import PROJECT_ROOT, get_settings
from app.core.exceptions import DuplicateRecordError, RecordNotFoundError
from app.core.logging import get_logger
from app.models.resume import ResumeSkill, ResumeVersion
from app.repositories.resume import (
    ResumeSkillRepository,
    ResumeVersionRepository,
)
from app.repositories.user import UserPreferenceRepository
from app.resume.schemas import ParsedResumeData

logger = get_logger(__name__)

# Directory where uploaded resume files are stored
RESUME_STORAGE_DIR: Path = PROJECT_ROOT / "storage" / "resumes"


class ResumeStorageService:
    """Service handling resume file persistence and DB version lifecycle."""

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize storage service with destination directory."""
        self.storage_dir = base_dir or RESUME_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, user_id: str, filename: str, content: bytes) -> tuple[Path, str]:
        """
        Save resume file to disk and compute SHA-256 content hash.

        Args:
            user_id: User identifier.
            filename: Original filename.
            content: Raw PDF bytes.

        Returns:
            Tuple of (destination_file_path, sha256_hash_hex).
        """
        sha256 = hashlib.sha256(content).hexdigest()
        user_dir = self.storage_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(filename).suffix or ".pdf"
        target_path = user_dir / f"{sha256}{ext}"

        with open(target_path, "wb") as f:
            f.write(content)

        logger.info(
            "resume_file_saved",
            user_id=user_id,
            target_path=str(target_path),
            file_hash=sha256,
            size_bytes=len(content),
        )
        return target_path, sha256

    async def create_version(
        self,
        session: AsyncSession,
        user_id: str,
        name: str,
        file_path: str,
        file_hash: str,
        parsed_data: ParsedResumeData,
        is_primary: bool = True,
    ) -> ResumeVersion:
        """
        Persist a new ResumeVersion record and associated ResumeSkills in DB.

        Args:
            session: Async DB session.
            user_id: User ID owner.
            name: Version title (e.g. 'Backend Engineer Resume').
            file_path: Disk path to PDF.
            file_hash: SHA-256 hash.
            parsed_data: Structured ParsedResumeData from parser.
            is_primary: Whether to set as user's primary/active resume.

        Returns:
            Created ResumeVersion model instance.
        """
        version_repo = ResumeVersionRepository(session)
        skill_repo = ResumeSkillRepository(session)
        pref_repo = UserPreferenceRepository(session)

        # Check for duplicate hash
        existing = await version_repo.get_by_file_hash(user_id, file_hash)
        if existing:
            logger.info("resume_hash_duplicate", user_id=user_id, existing_id=existing.id)
            return existing

        # If primary, reset other primary flags
        if is_primary:
            await version_repo.bulk_update(
                filters={"user_id": user_id},
                values={"is_primary": False},
            )

        # 1. Create ResumeVersion
        version = await version_repo.create(
            user_id=user_id,
            name=name,
            file_path=str(file_path),
            file_hash=file_hash,
            structured_data=parsed_data.model_dump(),
            summary=parsed_data.summary,
            total_experience_years=parsed_data.total_experience_years,
            full_name=parsed_data.contact.full_name,
            email=parsed_data.contact.email,
            phone=parsed_data.contact.phone,
            is_active=True,
            is_primary=is_primary,
        )

        # 2. Create ResumeSkill records
        skill_records = []
        for skill_name in parsed_data.skills:
            skill_records.append({
                "resume_version_id": version.id,
                "skill_name": skill_name,
                "proficiency_level": "intermediate",
            })

        if skill_records:
            await skill_repo.bulk_create(skill_records)

        # 3. Sync UserPreference active_resume_id
        if is_primary:
            pref = await pref_repo.get_by_user_id(user_id)
            if pref:
                pref.active_resume_id = version.id
                await session.flush()

        logger.info(
            "resume_version_created",
            version_id=version.id,
            user_id=user_id,
            name=name,
            skills_count=len(skill_records),
        )
        return version

    async def list_versions(self, session: AsyncSession, user_id: str) -> list[ResumeVersion]:
        """List all resume versions for a user."""
        repo = ResumeVersionRepository(session)
        return list(await repo.get_by_user_id(user_id))

    async def set_active(self, session: AsyncSession, user_id: str, version_id: str) -> ResumeVersion:
        """Set a specific resume version as the primary active version."""
        version_repo = ResumeVersionRepository(session)
        pref_repo = UserPreferenceRepository(session)

        version = await version_repo.get_by_id_or_raise(version_id)
        if version.user_id != user_id:
            raise RecordNotFoundError(entity="ResumeVersion", identifier=version_id)

        await version_repo.set_primary(user_id, version_id)

        pref = await pref_repo.get_by_user_id(user_id)
        if pref:
            pref.active_resume_id = version_id
            await session.flush()

        logger.info("resume_version_activated", user_id=user_id, version_id=version_id)
        return version

    async def delete_version(self, session: AsyncSession, user_id: str, version_id: str) -> bool:
        """Delete a resume version and remove physical file from disk."""
        repo = ResumeVersionRepository(session)
        version = await repo.get_by_id(version_id)
        if not version or version.user_id != user_id:
            return False

        # Remove file from disk
        try:
            p = Path(version.file_path)
            if p.exists():
                p.unlink()
        except Exception as exc:
            logger.warning("resume_file_delete_failed", path=version.file_path, error=str(exc))

        # Delete DB record
        await repo.delete(version_id)
        logger.info("resume_version_deleted", user_id=user_id, version_id=version_id)
        return True
