"""
HuntIQ — API Dependencies.

FastAPI dependency injectors for DB sessions and user contexts.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, RecordNotFoundError
from app.core.security import decode_token
from app.database import get_session_factory
from app.models.user import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency injecting an async SQLAlchemy session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Dependency injecting current authenticated user from JWT Bearer token."""
    if not token:
        # Fallback to demo user if no token provided during early dev
        return await get_current_user_stub(session)

    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
        )

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def get_current_user_stub(
    session: AsyncSession = Depends(get_db),
) -> User:
    """Fallback dependency returning a demo/primary user for development."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email("demo@huntiq.io")
    if not user:
        user = await user_repo.create(
            email="demo@huntiq.io",
            hashed_password="demo_password_hash",
            full_name="HuntIQ Candidate",
        )
        await session.commit()
    return user
