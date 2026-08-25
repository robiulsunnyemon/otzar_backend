import uuid
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class SpecimenCreate(BaseModel):
    tag: str = Field(..., description="Specimen code, e.g. #SC-082")
    name: str = Field(..., description="Mineral specimen name")
    formula: Optional[str] = Field(None, description="Chemical formula")
    conf: Optional[float] = Field(90.0, description="Match confidence percentage")
    grade: Optional[str] = Field("Specimen", description="Grade tier")
    date: Optional[str] = Field(None, description="Discovery date string")
    loc: Optional[str] = Field("Vein #4", description="Deposit or vein location")
    notes: Optional[str] = Field("", description="Field observations")
    photos: Optional[List[str]] = Field(default_factory=list, description="List of photo file paths/URIs")
    hasVoiceNote: Optional[bool] = Field(False, description="Whether audio note exists")
    voiceDuration: Optional[str] = Field("00:00", description="Duration of voice note")
    lat: Optional[str] = Field(None, description="Latitude")
    lon: Optional[str] = Field(None, description="Longitude")
    altitude: Optional[str] = Field(None, description="Altitude ASL")
    timestamp: Optional[str] = Field(None, description="Timestamp ISO string")


class SpecimenBatchSyncRequest(BaseModel):
    device_id: Optional[str] = Field(None, description="Client mobile device identifier")
    operator_email: Optional[str] = Field(None, description="Current field operator email")
    items: List[SpecimenCreate] = Field(default_factory=list, description="Array of offline discovery logs")


class SpecimenResponse(BaseModel):
    id: uuid.UUID
    tag: str
    name: str
    formula: Optional[str] = None
    confidence: float
    grade: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    altitude: Optional[str] = None
    field_notes: Optional[str] = None
    photos: Optional[List[str]] = None
    has_voice_note: bool = False
    voice_duration: Optional[str] = None
    synced_at: datetime

    class Config:
        from_attributes = True


class SpecimenBatchSyncResponse(BaseModel):
    status: str = "success"
    synced_count: int
    total_received: int
    synced_at: datetime
    message: str
    receipts: List[str] = Field(default_factory=list, description="List of synced specimen tags")
