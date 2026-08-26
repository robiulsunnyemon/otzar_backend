from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.schemas.auth import (
    EmailSubmitRequest,
    EmailSubmitResponse,
    PinVerifyRequest,
    RefreshTokenRequest,
    BiometricVerifyRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services.auth_service import (
    submit_email,
    verify_user_pin,
    refresh_user_tokens,
    resend_operator_pin,
    reset_operator_pin,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/request-pin",
    response_model=EmailSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Email (Registers & Sends PIN if new, or passes existing user without sending new PIN)",
)
@router.post(
    "/submit-email",
    response_model=EmailSubmitResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def submit_email_endpoint(
    data: EmailSubmitRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    If operator is new: registers account (is_verified=false), generates PIN, and dispatches via email.
    If operator is already registered: does NOT send a new PIN, returns existing is_verified status.
    """
    user, is_new_user, pin = await submit_email(session, data.email)

    if is_new_user:
        message = (
            f"Welcome! A 4-digit Security PIN has been dispatched to {user.email}. "
            "Please check your inbox to complete verification."
        )
    else:
        message = (
            f"Operator recognized ({user.email}). Please enter your security PIN."
        )

    return EmailSubmitResponse(
        email=user.email,
        is_new_user=is_new_user,
        is_verified=user.is_verified,
        message=message,
        expires_in_minutes=10 if is_new_user else None,
    )


@router.post(
    "/resend-pin",
    response_model=EmailSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend 4-Digit Security PIN for Unverified Operator",
)
async def resend_pin_endpoint(
    data: EmailSubmitRequest,
    session: AsyncSession = Depends(get_session),
):
    """Resend a new 4-digit OTP PIN to an unverified operator email."""
    user, _ = await resend_operator_pin(session, data.email)
    return EmailSubmitResponse(
        email=user.email,
        is_new_user=False,
        is_verified=user.is_verified,
        message=f"A fresh 4-digit security PIN has been dispatched to {user.email}.",
        expires_in_minutes=10,
    )


@router.post(
    "/reset-pin",
    response_model=EmailSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset PIN for Verified Operator",
)
async def reset_pin_endpoint(
    data: EmailSubmitRequest,
    session: AsyncSession = Depends(get_session),
):
    """Dispatches a temporary reset PIN code to an already verified operator."""
    user, _ = await reset_operator_pin(session, data.email)
    return EmailSubmitResponse(
        email=user.email,
        is_new_user=False,
        is_verified=user.is_verified,
        message=f"A temporary PIN reset code has been sent to {user.email}.",
        expires_in_minutes=10,
    )


@router.post(
    "/verify-pin",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify PIN & Login (Returns Access & Refresh Tokens)",
)
async def verify_pin_endpoint(
    data: PinVerifyRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Verifies the 4-digit PIN for the given email, authenticates the operator,
    and returns both a JWT access token and a refresh token along with user profile.
    """
    user, access_token, refresh_token = await verify_user_pin(session, data.email, data.pin)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.post(
    "/refresh-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token using Refresh Token",
)
async def refresh_token_endpoint(
    data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
):
    """Validates the refresh token and issues a fresh pair of access and refresh tokens."""
    user, access_token, refresh_token = await refresh_user_tokens(session, data.refresh_token)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.post(
    "/biometric-verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate Operator using On-Device Verified Biometric/Face Token",
)
async def biometric_verify_endpoint(
    data: BiometricVerifyRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Validates the secure biometric cryptographic token after on-device Face ID verification
    and issues fresh access and refresh tokens without requiring manual email/PIN.
    """
    user, access_token, refresh_token = await refresh_user_tokens(session, data.refresh_token)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout Operator & Invalidate Session",
)
async def logout_endpoint():
    """
    Terminates operator session cleanly and returns success confirmation.
    """
    return {
        "status": "success",
        "message": "Operator successfully logged out from Otzar Field Station.",
    }
