import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.services.cloudinary_service import upload_specimen_image
from app.core.config import settings

logger = logging.getLogger("ai_model_service")
router = APIRouter(prefix="/ai", tags=["Neural Model & AI Engine"])

# Live State for Active Neural Model Version
# In production, this can also be backed by DB / Redis / config
_CURRENT_MODEL_INFO = {
    "version": "v4.5.0",
    "min_app_version": "1.0.0",
    "release_date": "2026-08-26T12:00:00Z",
    "model_name": "Otzar MobileNet-V3 Geological Edge Classifier",
    "model_url": f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/raw/upload/v1/otzar_models/model_v4_5.tflite",
    "labels_url": f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/raw/upload/v1/otzar_models/labels_v4_5.txt",
    "minerals_db_url": f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/raw/upload/v1/otzar_models/minerals_db_v4_5.json",
    "total_classes": 36,
    "size_bytes": 14205000,
    "release_notes": "Enhanced detection for African Copperbelt Ores (Malachite, Bornite, Chrysocolla) and High-Grade Anthracite Coal.",
    "is_mandatory": False,
}


@router.get(
    "/neural-model-latest",
    summary="Get Latest Active Neural Model Version & Download URLs",
    description="Returns current active AI edge model metadata for Over-The-Air (OTA) background sync.",
)
async def get_latest_neural_model():
    return {
        "status": "success",
        "data": _CURRENT_MODEL_INFO,
    }


@router.post(
    "/update-model-version",
    summary="Update Active Model Version Metadata",
    description="Allows administrators to publish a newly trained model version Over-The-Air.",
)
async def update_model_version(
    version: str = Form("v4.5.0"),
    model_url: Optional[str] = Form(None),
    labels_url: Optional[str] = Form(None),
    minerals_db_url: Optional[str] = Form(None),
    release_notes: Optional[str] = Form(None),
):
    if version:
        _CURRENT_MODEL_INFO["version"] = version
    if model_url:
        _CURRENT_MODEL_INFO["model_url"] = model_url
    if labels_url:
        _CURRENT_MODEL_INFO["labels_url"] = labels_url
    if minerals_db_url:
        _CURRENT_MODEL_INFO["minerals_db_url"] = minerals_db_url
    if release_notes:
        _CURRENT_MODEL_INFO["release_notes"] = release_notes

    return {
        "status": "success",
        "message": f"Active AI Model successfully updated to version {version}",
        "data": _CURRENT_MODEL_INFO,
    }
