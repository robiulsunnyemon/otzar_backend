from datetime import datetime
from typing import Optional
from sqlmodel import Field
from app.models.base import UUIDModel, TimestampModel


class User(UUIDModel, TimestampModel, table=True):
    __tablename__ = "users"

    # Core Authentication
    email: str = Field(
        unique=True,
        index=True,
        nullable=False,
        description="Operator email address",
    )
    pin_hash: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Hashed permanent security PIN",
    )
    otp_code_hash: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Hashed 4-digit temporary OTP/PIN",
    )
    otp_expires_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Expiration datetime of active OTP/PIN",
    )
    is_active: bool = Field(
        default=True,
        nullable=False,
    )
    is_verified: bool = Field(
        default=False,
        nullable=False,
    )

    # Identity & Organization (From Profile Screen)
    full_name: str = Field(
        default="Operator",
        nullable=False,
        description="Full operator title and name (e.g. Dr. K. Osei)",
    )
    designation: str = Field(
        default="Exploration Geologist",
        nullable=False,
        description="Job role (e.g. Lead Exploration Geologist)",
    )
    company_name: str = Field(
        default="Geo Exploration Corp",
        nullable=False,
        description="Mining company or organization",
    )
    avatar_url: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Cloudinary secure avatar URL",
    )
    team_name: str = Field(
        default="Survey Unit Alpha",
        nullable=False,
        description="Assigned team unit",
    )

    # Field Metrics & Stats
    scans_count: int = Field(
        default=0,
        nullable=False,
        description="Total scans performed",
    )
    minerals_count: int = Field(
        default=0,
        nullable=False,
        description="Unique minerals cataloged",
    )
    team_count: int = Field(
        default=1,
        nullable=False,
        description="Connected team members count",
    )
    storage_used_mb: float = Field(
        default=0.0,
        nullable=False,
        description="Used storage in MB",
    )
    storage_total_mb: float = Field(
        default=5120.0,
        nullable=False,
        description="Storage quota in MB (5.0 GB default)",
    )

    # Field & Device Settings (From Profile Screen Toggles)
    sunlight_mode: bool = Field(
        default=False,
        nullable=False,
        description="Sunlight High-Contrast Mode toggle",
    )
    voice_logging: bool = Field(
        default=True,
        nullable=False,
        description="Voice Field Logging toggle",
    )
    auto_sync: bool = Field(
        default=False,
        nullable=False,
        description="Auto Background Sync on WiFi toggle",
    )
    offline_region: str = Field(
        default="Global Geological Base",
        nullable=False,
        description="Active offline map download region",
    )
    neural_version: str = Field(
        default="v4.2.1",
        nullable=False,
        description="Local neural model version",
    )
    export_allowed: bool = Field(
        default=True,
        nullable=False,
        description="Team lead export permissions status",
    )
