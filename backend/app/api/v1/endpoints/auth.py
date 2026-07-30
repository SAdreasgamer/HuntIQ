"""
HuntIQ — Authentication API Endpoint.

Endpoints for user registration, login, JWT token refresh, and profile fetching.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Body, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    email: str = Body(..., embed=True),
    password: str = Body(..., embed=True),
    full_name: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Register a new HuntIQ candidate account."""
    user_repo = UserRepository(session)
    existing = await user_repo.get_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    hashed = hash_password(password)
    user = await user_repo.create(
        email=email,
        hashed_password=hashed,
        full_name=full_name,
    )
    await session.commit()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Authenticate user with email & password, returning JWT access & refresh tokens."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
    }


@router.post("/refresh")
async def refresh_token_endpoint(
    refresh_token: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Exchange a valid refresh token for a new access token."""
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")

        user_id = payload.get("sub", "")
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        new_access_token = create_access_token(user.id)
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {exc}")


@router.get("/me")
async def get_current_user_profile(
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get candidate profile of current authenticated user."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
