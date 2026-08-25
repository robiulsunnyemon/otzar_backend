import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.security import decode_token
from app.models.user import User
from app.schemas.specimen import (
    SpecimenBatchSyncRequest,
    SpecimenBatchSyncResponse,
    SpecimenResponse,
)
from app.services.specimen_service import SpecimenService

router = APIRouter(tags=["Specimens & Sync Engine"])
security = HTTPBearer(auto_error=False)


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """Extract authenticated user if token present, else return None for offline devices."""
    if not credentials:
        return None

    token = credentials.credentials
    user_id_str = decode_token(token)
    if not user_id_str:
        return None

    try:
        user_uuid = uuid.UUID(user_id_str)
        user = await session.get(User, user_uuid)
        return user
    except Exception:
        return None


@router.post(
    "/sync/batch",
    response_model=SpecimenBatchSyncResponse,
    summary="Batch Synchronize Field Specimen Discoveries",
    description="Accepts an array of locally queued mineral discoveries from the mobile app and persists them into the cloud database.",
)
async def sync_batch_specimens(
    request: SpecimenBatchSyncRequest,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    if not request.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No specimen items provided in sync payload.",
        )

    response = await SpecimenService.batch_sync(
        db=session,
        request=request,
        current_user=current_user,
    )
    return response


@router.get(
    "/specimens",
    response_model=List[SpecimenResponse],
    summary="List Synchronized Cloud Specimens",
    description="Retrieve list of all geological specimens synchronized across mining concessions.",
)
async def list_cloud_specimens(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    specimens = await SpecimenService.list_specimens(
        db=session,
        limit=limit,
        offset=offset,
    )

    response_items = []
    for s in specimens:
        photos_list = []
        if s.photos:
            try:
                photos_list = json.loads(s.photos)
            except Exception:
                photos_list = []

        response_items.append(
            SpecimenResponse(
                id=s.id,
                tag=s.tag,
                name=s.name,
                formula=s.formula,
                confidence=s.confidence,
                grade=s.grade,
                location_name=s.location_name,
                latitude=s.latitude,
                longitude=s.longitude,
                altitude=s.altitude,
                field_notes=s.field_notes,
                photos=photos_list,
                has_voice_note=s.has_voice_note,
                voice_duration=s.voice_duration,
                synced_at=s.synced_at,
            )
        )

    return response_items
