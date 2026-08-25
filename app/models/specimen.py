import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field
from app.models.base import UUIDModel, TimestampModel


class Specimen(UUIDModel, TimestampModel, table=True):
    __tablename__ = "specimens"

    tag: str = Field(
        index=True,
        nullable=False,
        description="Specimen field identification code (e.g., #SC-082)",
    )
    name: str = Field(
        index=True,
        nullable=False,
        description="Identified mineral name (e.g., Malachite, Tanzanite)",
    )
    formula: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Chemical formula of the specimen",
    )
    confidence: float = Field(
        default=0.0,
        nullable=False,
        description="Confidence percentage score (e.g., 95.0)",
    )
    grade: Optional[str] = Field(
        default="Specimen",
        nullable=True,
        description="Geological grade (e.g., Specimen, Gemstone, High-Grade Ore)",
    )
    location_name: Optional[str] = Field(
        default="Field Vein",
        nullable=True,
        description="Geological deposit or claim sector name",
    )

    # GPS Telemetry
    latitude: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Latitude coordinates with hemisphere",
    )
    longitude: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Longitude coordinates with hemisphere",
    )
    altitude: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Elevation / Altitude above sea level",
    )

    # Field Observations & Multi-Modal Media
    field_notes: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Geologist field notes and strike observations",
    )
    tags: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Comma-separated or JSON list of deposit tags",
    )
    photos: Optional[str] = Field(
        default=None,
        nullable=True,
        description="JSON serialized list of specimen photo file paths/URLs",
    )
    has_voice_note: bool = Field(
        default=False,
        nullable=False,
        description="Whether a voice audio note was recorded in the field",
    )
    voice_duration: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Duration of recorded voice note (e.g., 00:15)",
    )

    # Operator Reference & Sync Metadata
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
        description="Operator ID who discovered the specimen",
    )
    synced_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="Datetime when cloud synchronization completed",
    )
