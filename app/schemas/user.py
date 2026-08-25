import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    full_name: str
    designation: str
    company_name: str
    avatar_url: Optional[str] = None
    team_name: str
    scans_count: int
    minerals_count: int
    team_count: int
    storage_used_mb: float
    storage_total_mb: float
    sunlight_mode: bool
    voice_logging: bool
    auto_sync: bool
    offline_region: str
    neural_version: str
    export_allowed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    designation: Optional[str] = None
    company_name: Optional[str] = None
    team_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserSettingsUpdate(BaseModel):
    sunlight_mode: Optional[bool] = None
    voice_logging: Optional[bool] = None
    auto_sync: Optional[bool] = None
    offline_region: Optional[str] = None
