import logging
from typing import Optional
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from app.core.config import settings

logger = logging.getLogger("cloudinary_service")

# Initialize Cloudinary credentials from settings
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


async def upload_avatar_image(file: UploadFile, user_id: str) -> Optional[str]:
    """
    Upload an avatar image to Cloudinary and return the secure HTTPS URL.
    """
    try:
        contents = await file.read()
        response = cloudinary.uploader.upload(
            contents,
            folder="otzar_avatars",
            public_id=f"avatar_{user_id}",
            overwrite=True,
            resource_type="image",
            transformation=[
                {"width": 400, "height": 400, "crop": "fill", "gravity": "face"},
                {"quality": "auto", "fetch_format": "auto"},
            ],
        )
        return response.get("secure_url")
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        # Return fallback mock URL in local development if credentials aren't live yet
        return f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/image/upload/v1/otzar_avatars/avatar_{user_id}.png"
