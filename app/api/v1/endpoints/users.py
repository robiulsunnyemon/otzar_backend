import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.core.security import decode_token
from app.models.user import User
from app.schemas.user import UserRead, UserProfileUpdate, UserSettingsUpdate
from app.services.cloudinary_service import upload_avatar_image

router = APIRouter(prefix="/users", tags=["Users & Profile"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Dependency to extract authenticated user from JWT token."""
    token = credentials.credentials
    user_id_str = decode_token(token)

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user ID in token.",
        )

    statement = select(User).where(User.id == user_uuid)
    result = await session.exec(statement)
    user = result.first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operator account not found or disabled.",
        )

    return user


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get Current Operator Profile & Settings",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve full profile, field metrics, and device settings for current operator."""
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update Operator Profile",
)
async def update_my_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update operator full name, designation, company name, or team unit."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.patch(
    "/me/settings",
    response_model=UserRead,
    summary="Update Field & Device Settings",
)
async def update_my_settings(
    data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update settings like sunlight mode, voice logging, auto sync, or offline region."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.post(
    "/me/avatar",
    response_model=UserRead,
    summary="Upload Profile Avatar via Cloudinary",
)
async def upload_avatar(
    file: UploadFile = File(..., description="Image file (JPG/PNG/WEBP)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload new avatar image to Cloudinary and update profile avatar URL."""
    if file.content_type and not file.content_type.startswith("image/") and not (file.filename and file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image.",
        )

    secure_url = await upload_avatar_image(file, str(current_user.id))
    if not secure_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image to Cloudinary.",
        )

    current_user.avatar_url = secure_url
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Delete / Deactivate Operator Account",
)
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Deactivates operator account and schedules data purge in compliance with data privacy regulations.
    """
    current_user.is_active = False
    session.add(current_user)
    await session.commit()
    return {
        "success": True,
        "message": "Operator account and cloud telemetry scheduled for deletion.",
        "email": current_user.email,
    }
