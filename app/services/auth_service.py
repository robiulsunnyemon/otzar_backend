import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from app.models.user import User
from app.core.security import (
    generate_4digit_pin,
    hash_pin,
    verify_pin_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.services.email_service import send_pin_email


async def submit_email(session: AsyncSession, email: str) -> Tuple[User, bool, Optional[str]]:
    """
    Handles operator email submission.
    - If user does not exist: creates new user (is_verified=False), generates 4-digit PIN, emails it.
    - If user already exists: does NOT send a new PIN, returns existing user and is_verified status.
    """
    normalized_email = email.strip().lower()
    statement = select(User).where(User.email == normalized_email)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        # New operator registration
        default_name = normalized_email.split("@")[0].replace(".", " ").title()
        pin = generate_4digit_pin()

        user = User(
            email=normalized_email,
            full_name=f"Dr. {default_name}",
            designation="Exploration Geologist",
            company_name="Barrick Mining Corp",
            team_name="West Africa Survey Unit",
            scans_count=0,
            minerals_count=0,
            team_count=1,
            is_active=True,
            is_verified=False,
            otp_code_hash=hash_pin(pin),
            otp_expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Dispatch email for new user
        await send_pin_email(to_email=user.email, pin=pin, full_name=user.full_name)
        return user, True, pin

    # Existing operator: Do not send new PIN
    return user, False, None


async def resend_operator_pin(session: AsyncSession, email: str) -> Tuple[User, str]:
    """Resend a new 4-digit OTP PIN to an unverified operator."""
    normalized_email = email.strip().lower()
    statement = select(User).where(User.email == normalized_email)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator account not found.",
        )

    pin = generate_4digit_pin()
    user.otp_code_hash = hash_pin(pin)
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    await send_pin_email(to_email=user.email, pin=pin, full_name=user.full_name)
    return user, pin


async def reset_operator_pin(session: AsyncSession, email: str) -> Tuple[User, str]:
    """Reset PIN for a verified operator who forgot their security PIN."""
    normalized_email = email.strip().lower()
    statement = select(User).where(User.email == normalized_email)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator account not found.",
        )

    pin = generate_4digit_pin()
    user.otp_code_hash = hash_pin(pin)
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    await send_pin_email(to_email=user.email, pin=pin, full_name=user.full_name)
    return user, pin


async def verify_user_pin(session: AsyncSession, email: str, pin: str) -> Tuple[User, str, str]:
    """Verify 4-digit PIN against stored hash and generate JWT access + refresh tokens."""
    normalized_email = email.strip().lower()
    statement = select(User).where(User.email == normalized_email)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator account not found. Please submit your email first.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator account is disabled.",
        )

    is_valid = False
    now = datetime.utcnow()

    # 1. Check temporary OTP
    if user.otp_code_hash and user.otp_expires_at:
        if user.otp_expires_at >= now:
            if verify_pin_hash(pin, user.otp_code_hash):
                is_valid = True

    # 2. Check permanent PIN if set
    if not is_valid and user.pin_hash:
        if verify_pin_hash(pin, user.pin_hash):
            is_valid = True

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired 4-digit security PIN.",
        )

    # Mark as verified and set permanent PIN if not yet set
    user.is_verified = True
    if not user.pin_hash:
        user.pin_hash = hash_pin(pin)
    user.otp_code_hash = None
    user.otp_expires_at = None
    user.updated_at = now

    session.add(user)
    await session.commit()
    await session.refresh(user)

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    return user, access_token, refresh_token


async def refresh_user_tokens(session: AsyncSession, refresh_token: str) -> Tuple[User, str, str]:
    """Validate refresh token and issue a fresh pair of access and refresh tokens."""
    user_id_str = decode_token(refresh_token, expected_type="refresh")

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user ID in refresh token.",
        )

    statement = select(User).where(User.id == user_uuid)
    result = await session.exec(statement)
    user = result.first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operator account not found or disabled.",
        )

    new_access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return user, new_access_token, new_refresh_token
