import json
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.specimen import Specimen
from app.models.user import User
from app.schemas.specimen import SpecimenBatchSyncRequest, SpecimenBatchSyncResponse, SpecimenCreate


class SpecimenService:
    @staticmethod
    async def batch_sync(
        db: AsyncSession,
        request: SpecimenBatchSyncRequest,
        current_user: Optional[User] = None,
    ) -> SpecimenBatchSyncResponse:
        synced_receipts: List[str] = []
        user_id = current_user.id if current_user else None

        for item in request.items:
            # Check if specimen tag already exists to avoid duplicates
            statement = select(Specimen).where(Specimen.tag == item.tag)
            result = await db.execute(statement)
            existing_specimen = result.scalars().first()

            photos_json = json.dumps(item.photos) if item.photos else "[]"

            if existing_specimen:
                # Update existing record with latest field data
                existing_specimen.name = item.name
                existing_specimen.formula = item.formula
                existing_specimen.confidence = item.conf or existing_specimen.confidence
                existing_specimen.grade = item.grade or existing_specimen.grade
                existing_specimen.location_name = item.loc or existing_specimen.location_name
                existing_specimen.latitude = item.lat or existing_specimen.latitude
                existing_specimen.longitude = item.lon or existing_specimen.longitude
                existing_specimen.altitude = item.altitude or existing_specimen.altitude
                existing_specimen.field_notes = item.notes or existing_specimen.field_notes
                existing_specimen.photos = photos_json
                existing_specimen.has_voice_note = item.hasVoiceNote or False
                existing_specimen.voice_duration = item.voiceDuration
                existing_specimen.synced_at = datetime.utcnow()
                db.add(existing_specimen)
            else:
                # Create new database record
                new_specimen = Specimen(
                    tag=item.tag,
                    name=item.name,
                    formula=item.formula,
                    confidence=item.conf or 90.0,
                    grade=item.grade or "Specimen",
                    location_name=item.loc or "Field Vein",
                    latitude=item.lat,
                    longitude=item.lon,
                    altitude=item.altitude,
                    field_notes=item.notes,
                    photos=photos_json,
                    has_voice_note=item.hasVoiceNote or False,
                    voice_duration=item.voiceDuration,
                    user_id=user_id,
                    synced_at=datetime.utcnow(),
                )
                db.add(new_specimen)

            synced_receipts.append(item.tag)

        if current_user:
            # Update user cloud metrics
            user_scans_stmt = select(Specimen).where(Specimen.user_id == current_user.id)
            user_scans_res = await db.execute(user_scans_stmt)
            user_all_specimens = list(user_scans_res.scalars().all())
            current_user.scans_count = len(user_all_specimens)
            current_user.minerals_count = len(set(s.name.strip().lower() for s in user_all_specimens if s.name))
            db.add(current_user)

        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist batch synchronized specimens: {str(e)}",
            )

        return SpecimenBatchSyncResponse(
            status="success",
            synced_count=len(synced_receipts),
            total_received=len(request.items),
            synced_at=datetime.utcnow(),
            message=f"Successfully synchronized {len(synced_receipts)} specimen records to cloud vault.",
            receipts=synced_receipts,
        )

    @staticmethod
    async def list_specimens(
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[any] = None,
    ) -> List[Specimen]:
        statement = select(Specimen)
        if user_id:
            statement = statement.where(Specimen.user_id == user_id)
        statement = statement.order_by(Specimen.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())
